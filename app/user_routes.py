from flask import Blueprint, request, jsonify, g
from . import db
from .models import Product, Category, Cart, Order, OrderItem, User, Address
from .auth import token_required

# Create blueprint for user routes
user_bp = Blueprint('user', __name__)

def _normalize_frontend_category(category_value):
    """
    Convert frontend category slugs/names into DB category names.
    shop.html uses slugs like: vegetables|fruits|juice|dried.
    """
    if not category_value:
        return None
    val = str(category_value).strip()
    if not val:
        return None
    key = val.lower()
    mapping = {
        'vegetables': 'Vegetables',
        'fruits': 'Fruits',
        'juice': 'Juice',
        'dried': 'Dried',
        'online orders': 'Online Orders'
    }
    return mapping.get(key) or val

def _get_or_create_category(category_name):
    if not category_name:
        return None
    category_name = str(category_name).strip()
    if not category_name:
        return None

    # Case-insensitive lookup (helps when old categories exist)
    category = Category.query.filter(db.func.lower(Category.name) == category_name.lower()).first()
    if category:
        return category

    # Handle singular/plural mismatches (e.g. Vegetable vs Vegetables)
    alt_name = category_name[:-1] if category_name.endswith('s') else category_name + 's'
    category = Category.query.filter(db.func.lower(Category.name) == alt_name.lower()).first()
    if category:
        return category

    category = Category(name=category_name)
    db.session.add(category)
    db.session.flush()
    return category


def _address_payload(data):
    return {
        'full_name': (data.get('full_name') or data.get('name') or '').strip(),
        'phone': (data.get('phone') or '').strip(),
        'address_line': (data.get('address_line') or data.get('line') or '').strip(),
        'city': (data.get('city') or '').strip(),
        'state': (data.get('state') or '').strip(),
        'pincode': (data.get('pincode') or '').strip(),
    }

@user_bp.route('/products', methods=['GET'])
@token_required
def get_products():
    """
    Fetch all products or filter by category

    GET /api/user/products
    GET /api/user/products?category_id=1
    Headers: Authorization: Bearer <token>

    Returns: List of products with category info
    """
    category_id = request.args.get('category_id', type=int)

    try:
        if category_id:
            products = Product.query.filter_by(category_id=category_id).all()
        else:
            products = Product.query.all()

        product_list = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock_quantity': product.stock_quantity,
                'category_id': product.category_id,
                'category_name': product.category.name if product.category else None
            }
            product_list.append(product_data)

        return jsonify({
            'products': product_list,
            'count': len(product_list),
            'category_filter': category_id
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch products'}), 500

@user_bp.route('/cart', methods=['GET'])
@token_required
def get_cart():
    try:
        cart_items = Cart.query.filter_by(user_id=g.current_user.id).all()
        total_quantity = sum(item.quantity for item in cart_items)
        return jsonify({
            'cart_items': [item.to_dict() for item in cart_items],
            'total_items': total_quantity,
            'count': len(cart_items)
        }), 200
    except Exception:
        return jsonify({'error': 'Failed to fetch cart'}), 500


@user_bp.route('/cart', methods=['POST'])
@token_required
def add_to_cart():
    data = request.get_json()

    if not data or 'product_id' not in data:
        return jsonify({'error': 'Product ID is required'}), 400

    product_id = int(data['product_id'])
    quantity = int(data.get('quantity', 1))

    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if product.stock_quantity < quantity:
            return jsonify({'error': f'Insufficient stock. Available: {product.stock_quantity}'}), 400

        cart_item = Cart.query.filter_by(user_id=g.current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = Cart(user_id=g.current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()

        return jsonify({'message': 'Product added to cart', 'cart_item': cart_item.to_dict()}), 201

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product to cart'}), 500


@user_bp.route('/cart/frontend-add', methods=['POST'])
@token_required
def frontend_add_to_cart():
    """Alias for add_to_cart used by the storefront frontend."""
    return add_to_cart()

@user_bp.route('/cart/<int:cart_item_id>', methods=['DELETE'])
@token_required
def remove_from_cart(cart_item_id):
    try:
        cart_item = Cart.query.filter_by(id=cart_item_id, user_id=g.current_user.id).first()
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404

        db.session.delete(cart_item)
        db.session.commit()

        return jsonify({'message': 'Item removed from cart'}), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove item from cart'}), 500

@user_bp.route('/cart/clear', methods=['DELETE'])
@token_required
def clear_cart():
    try:
        cart_items = Cart.query.filter_by(user_id=g.current_user.id).all()
        if not cart_items:
            return jsonify({'message': 'Cart is already empty'}), 200

        removed_count = len(cart_items)
        for item in cart_items:
            db.session.delete(item)

        db.session.commit()

        return jsonify({'message': 'Cart cleared successfully', 'items_removed': removed_count}), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to clear cart'}), 500

@user_bp.route('/cart/bulk', methods=['POST'])
@token_required
def add_multiple_to_cart():
    data = request.get_json()
    if not data or 'items' not in data or not isinstance(data['items'], list):
        return jsonify({'error': 'Items array is required'}), 400

    items = data['items']
    if not items:
        return jsonify({'error': 'Items array cannot be empty'}), 400

    try:
        added_items = []
        updated_items = []
        failed_items = []

        for item in items:
            if not isinstance(item, dict) or 'product_id' not in item:
                failed_items.append({'item': item, 'error': 'product_id required'})
                continue

            product_id = item['product_id']
            quantity = item.get('quantity', 1)
            if quantity < 1:
                failed_items.append({'product_id': product_id, 'error': 'Quantity must be at least 1'})
                continue

            product = Product.query.get(product_id)
            if not product:
                failed_items.append({'product_id': product_id, 'error': 'Product not found'})
                continue

            if product.stock_quantity < quantity:
                failed_items.append({'product_id': product_id, 'error': f'Insufficient stock. Available: {product.stock_quantity}'})
                continue

            cart_item = Cart.query.filter_by(user_id=g.current_user.id, product_id=product_id).first()
            if cart_item:
                old_quantity = cart_item.quantity
                cart_item.quantity += quantity
                updated_items.append({'product_id': product_id, 'old_quantity': old_quantity, 'new_quantity': cart_item.quantity})
            else:
                cart_item = Cart(user_id=g.current_user.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)
                added_items.append({'product_id': product_id, 'quantity': quantity})

        db.session.commit()

        return jsonify({
            'message': 'Bulk cart update completed',
            'added_items': added_items,
            'updated_items': updated_items,
            'failed_items': failed_items,
            'summary': {'added': len(added_items), 'updated': len(updated_items), 'failed': len(failed_items)}
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to process bulk cart update'}), 500
    
@user_bp.route('/cart/summary', methods=['GET'])
@token_required
def get_cart_summary():
    try:
        cart_items = Cart.query.filter_by(user_id=g.current_user.id).all()
        total_items = sum(item.quantity for item in cart_items)
        total_unique_products = len(cart_items)
        total_amount = sum(item.quantity * item.product.price for item in cart_items)

        return jsonify({
            'total_unique_products': total_unique_products,
            'total_quantity': total_items,
            'total_amount': round(total_amount, 2),
            'has_items': total_items > 0
        }), 200

    except Exception:
        return jsonify({'error': 'Failed to get cart summary'}), 500

@user_bp.route('/orders', methods=['POST'])
@token_required
def place_order():
    """
    Place order from cart items

    POST /api/user/orders
    Headers: Authorization: Bearer <token>
    Body: {
        "cart_item_ids": [1, 2, 3]  // Optional: specific cart items to order
    }

    Returns: Order details
    """
    data = request.get_json() or {}
    cart_item_ids = data.get('cart_item_ids')  # Optional: order specific items

    try:
        # Get cart items for current user
        query = Cart.query.filter_by(user_id=g.current_user.id)

        if cart_item_ids:
            query = query.filter(Cart.id.in_(cart_item_ids))

        cart_items = query.all()

        if not cart_items:
            return jsonify({'error': 'No items in cart to order'}), 400

        orders_created = []

        # Check stock availability first for all items
        for cart_item in cart_items:
            if cart_item.product.stock_quantity < cart_item.quantity:
                return jsonify({
                    'error': f'Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock_quantity}'
                }), 400

        # Create one order with multiple order_items
        order = Order(
            user_id=g.current_user.id,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        for cart_item in cart_items:
            # Check stock availability
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
            )
            db.session.add(order_item)

            # Reduce product stock
            cart_item.product.stock_quantity -= cart_item.quantity

            # Remove from cart
            db.session.delete(cart_item)

        orders_created.append(order)

        db.session.commit()

        # Calculate total amount
        total_amount = sum(order.to_dict().get('order_total', 0) for order in orders_created)

        return jsonify({
            'message': 'Order placed successfully',
            'orders': [order.to_dict() for order in orders_created],
            'total_orders': len(orders_created),
            'total_amount': round(total_amount, 2)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to place order'}), 500

@user_bp.route('/orders', methods=['GET'])
@token_required
def get_user_orders():
    """
    Get user's order history

    GET /api/user/orders
    GET /api/user/orders?status=pending
    Headers: Authorization: Bearer <token>

    Returns: User's orders
    """
    status_filter = request.args.get('status')

    try:
        query = Order.query.filter_by(user_id=g.current_user.id)

        if status_filter:
            query = query.filter_by(status=status_filter)

        orders = query.order_by(Order.order_date.desc()).all()

        order_list = [order.to_dict() for order in orders]
        total_amount = sum(o.get('order_total', 0) for o in order_list)

        return jsonify({
            'orders': order_list,
            'total_orders': len(order_list),
            'total_amount': round(total_amount, 2),
            'status_filter': status_filter
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500


@user_bp.route('/addresses', methods=['GET'])
@token_required
def get_user_addresses():
    try:
        addresses = Address.query.filter_by(user_id=g.current_user.id).order_by(
            Address.is_default.desc(), Address.updated_at.desc()
        ).all()
        return jsonify({
            'addresses': [a.to_dict() for a in addresses],
            'count': len(addresses)
        }), 200
    except Exception:
        return jsonify({'error': 'Failed to fetch addresses'}), 500


@user_bp.route('/addresses', methods=['POST'])
@token_required
def create_user_address():
    data = request.get_json() or {}
    payload = _address_payload(data)
    if not all(payload.values()):
        return jsonify({'error': 'full_name, phone, address_line, city, state, and pincode are required'}), 400

    try:
        is_default = bool(data.get('is_default', False))
        if is_default:
            Address.query.filter_by(user_id=g.current_user.id, is_default=True).update({'is_default': False})

        # First address is default automatically
        if Address.query.filter_by(user_id=g.current_user.id).count() == 0:
            is_default = True

        address = Address(
            user_id=g.current_user.id,
            full_name=payload['full_name'],
            phone=payload['phone'],
            address_line=payload['address_line'],
            city=payload['city'],
            state=payload['state'],
            pincode=payload['pincode'],
            is_default=is_default
        )
        db.session.add(address)
        db.session.commit()
        return jsonify({'message': 'Address saved successfully', 'address': address.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to save address'}), 500


@user_bp.route('/addresses/<int:address_id>', methods=['PUT'])
@token_required
def update_user_address(address_id):
    data = request.get_json() or {}
    payload = _address_payload(data)
    if not all(payload.values()):
        return jsonify({'error': 'full_name, phone, address_line, city, state, and pincode are required'}), 400

    try:
        address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
        if not address:
            return jsonify({'error': 'Address not found'}), 404

        address.full_name = payload['full_name']
        address.phone = payload['phone']
        address.address_line = payload['address_line']
        address.city = payload['city']
        address.state = payload['state']
        address.pincode = payload['pincode']

        if 'is_default' in data and bool(data.get('is_default')):
            Address.query.filter_by(user_id=g.current_user.id, is_default=True).update({'is_default': False})
            address.is_default = True

        db.session.commit()
        return jsonify({'message': 'Address updated', 'address': address.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to update address'}), 500


@user_bp.route('/addresses/<int:address_id>', methods=['DELETE'])
@token_required
def delete_user_address(address_id):
    try:
        address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
        if not address:
            return jsonify({'error': 'Address not found'}), 404

        was_default = bool(address.is_default)
        db.session.delete(address)
        db.session.flush()

        if was_default:
            next_address = Address.query.filter_by(user_id=g.current_user.id).order_by(Address.updated_at.desc()).first()
            if next_address:
                next_address.is_default = True

        db.session.commit()
        return jsonify({'message': 'Address deleted'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete address'}), 500


@user_bp.route('/addresses/<int:address_id>/default', methods=['PUT'])
@token_required
def set_default_address(address_id):
    try:
        address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
        if not address:
            return jsonify({'error': 'Address not found'}), 404

        Address.query.filter_by(user_id=g.current_user.id, is_default=True).update({'is_default': False})
        address.is_default = True
        db.session.commit()
        return jsonify({'message': 'Default address updated', 'address': address.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to set default address'}), 500

@user_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order_details(order_id):
    """
    Get specific order details

    GET /api/user/orders/1
    Headers: Authorization: Bearer <token>

    Returns: Order details
    """
    try:
        order = Order.query.filter_by(
            id=order_id,
            user_id=g.current_user.id
        ).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        order_data = order.to_dict()

        return jsonify({
            'order': order_data
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch order details'}), 500

@user_bp.route('/orders/<int:order_id>/cancel', methods=['PUT'])
@token_required
def cancel_order(order_id):
    """
    Cancel a pending order

    PUT /api/user/orders/1/cancel
    Headers: Authorization: Bearer <token>

    Returns: Updated order details
    """
    try:
        # Find order and verify ownership
        order = Order.query.filter_by(
            id=order_id,
            user_id=g.current_user.id
        ).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Check if order can be cancelled
        if order.status != 'pending':
            return jsonify({
                'error': f'Cannot cancel order with status: {order.status}. Only pending orders can be cancelled.'
            }), 400

        # Restore product stock for all line items
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity

        # Update order status
        order.status = 'cancelled'

        db.session.commit()

        order_data = order.to_dict()

        return jsonify({
            'message': 'Order cancelled successfully',
            'order': order_data,
            'stock_restored': sum(item.quantity for item in order.items)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel order'}), 500

@user_bp.route('/orders/<int:order_id>/reorder', methods=['POST'])
@token_required
def reorder_from_order(order_id):
    """
    Reorder items from a previous order

    POST /api/user/orders/1/reorder
    Headers: Authorization: Bearer <token>

    Returns: Cart update details
    """
    try:
        # Find order and verify ownership
        order = Order.query.filter_by(
            id=order_id,
            user_id=g.current_user.id
        ).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        if not order.items:
            return jsonify({'error': 'Order has no items to reorder'}), 400

        action = 'updated'
        added_count = 0
        updated_count = 0
        reordered_products = []

        for item in order.items:
            if not item.product:
                continue
            if item.product.stock_quantity < item.quantity:
                return jsonify({
                    'error': f'Insufficient stock for {item.product.name}. Available: {item.product.stock_quantity}'
                }), 400

            cart_item = Cart.query.filter_by(
                user_id=g.current_user.id,
                product_id=item.product_id
            ).first()

            if cart_item:
                cart_item.quantity += item.quantity
                updated_count += 1
            else:
                cart_item = Cart(
                    user_id=g.current_user.id,
                    product_id=item.product_id,
                    quantity=item.quantity
                )
                db.session.add(cart_item)
                added_count += 1

            reordered_products.append({
                'id': item.product.id,
                'name': item.product.name,
                'price': item.product.price,
                'quantity_added': item.quantity
            })

        action = 'added' if updated_count == 0 else 'updated'
        message = 'Order items added to cart successfully'

        db.session.commit()

        return jsonify({
            'message': message,
            'action': action,
            'products': reordered_products,
            'summary': {
                'added': added_count,
                'updated': updated_count
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reorder items'}), 500


@user_bp.route('/frontend-orders', methods=['POST'])
@token_required
def create_frontend_orders():
    """
    Create orders from the front-end localStorage cart.

    POST /api/user/frontend-orders
    Headers: Authorization: Bearer <token>
    Body: {
        "items": [
            {"name": "...", "price": 100, "quantity": 2},
            ...
        ]
    }
    """
    data = request.get_json() or {}
    items = data.get('items') or []

    if not isinstance(items, list) or not items:
        return jsonify({'error': 'No items provided'}), 400

    try:
        # Default vendor (first vendor user) so vendor dashboard can see these orders
        default_vendor = User.query.filter_by(role='vendor').first()

        orders_created = []

        for item in items:
            name = (item.get('name') or '').strip()
            price = float(item.get('price') or 0)
            qty = int(item.get('quantity') or 1)
            product_id = item.get('product_id') or item.get('productId')
            if not name or price <= 0 or qty < 1:
                continue

            product = None
            if product_id:
                product = Product.query.get(int(product_id))
            if not product:
                product = Product.query.filter_by(name=name).first()

            if not product:
                category_input = (item.get('category') or item.get('category_slug') or item.get('categorySlug') or '').strip()
                category_name = _normalize_frontend_category(category_input) or 'Vegetables'
                category = _get_or_create_category(category_name)
                product = Product(
                    name=name,
                    price=price,
                    stock_quantity=qty,
                    category_id=category.id,
                    vendor_id=default_vendor.id if default_vendor else None
                )
                db.session.add(product)
                db.session.flush()
            else:
                if default_vendor and not product.vendor_id:
                    product.vendor_id = default_vendor.id
                db.session.flush()

            order = Order(
                user_id=g.current_user.id,
                status='pending'
            )
            db.session.add(order)
            db.session.flush()

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty
            )
            db.session.add(order_item)
            orders_created.append(order)

        if not orders_created:
            db.session.rollback()
            return jsonify({'error': 'No valid items to create orders'}), 400

        db.session.commit()

        total_amount = sum(o.to_dict().get('order_total', 0) for o in orders_created)

        return jsonify({
            'message': 'Frontend order stored successfully',
            'orders': [o.to_dict() for o in orders_created],
            'total_orders': len(orders_created),
            'total_amount': round(total_amount, 2)
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Frontend Orders] Error while storing order: {e}")
        return jsonify({'error': f'Failed to store frontend order: {str(e)}'}), 500
@user_bp.route('/add-demo-products', methods=['GET'])
def add_demo_products():
    try:
        products = [
            Product(id=1, name="Strawberry", price=120, stock_quantity=50),
            Product(id=2, name="Bell Pepper", price=80, stock_quantity=50),
            Product(id=3, name="Green Beans", price=80, stock_quantity=50),
            Product(id=4, name="Cabbage", price=40, stock_quantity=50),
            Product(id=5, name="Tomato", price=80, stock_quantity=50),
            Product(id=6, name="Broccoli", price=120, stock_quantity=50),
            Product(id=7, name="Carrot", price=100, stock_quantity=50),
            Product(id=8, name="Juice", price=150, stock_quantity=50),
            Product(id=9, name="Onion", price=80, stock_quantity=50),
            Product(id=10, name="Apple", price=100, stock_quantity=50),
            Product(id=11, name="Garlic", price=40, stock_quantity=50),
            Product(id=12, name="Chilli", price=20, stock_quantity=50),
        ]

        for p in products:
            existing = Product.query.get(p.id)
            if not existing:
                db.session.add(p)

        db.session.commit()
        return {"message": "Demo products added ✅"}

    except Exception as e:
        return {"error": str(e)}