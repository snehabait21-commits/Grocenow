from flask import Blueprint, request, jsonify, g
from . import db
from .models import Product, Category, Order, OrderItem, User
from .auth import token_required, vendor_required

# Create blueprint for vendor routes
vendor_bp = Blueprint('vendor', __name__)


def _vendor_product_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock_quantity': product.stock_quantity,
        'category_id': product.category_id,
        'category_name': product.category.name if product.category else None,
        'vendor_id': product.vendor_id,
    }

@vendor_bp.route('/login', methods=['POST'])
def vendor_login():
    """
    Vendor login API

    POST /api/vendor/login
    Body: {
        "email": "vendor@grocenow.com",
        "password": "vendorpassword123"
    }

    Returns: Vendor user data with JWT token
    Note: Only users with 'vendor' role can successfully login here
    """
    data = request.get_json()

    # Validate required fields
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({
            'error': 'Email and password are required'
        }), 400

    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Debug logging
    print(f"\n[Vendor Login] Attempt: email={data['email']}")
    if not user:
        print(f"[Vendor Login] User not found: {data['email']}")
        return jsonify({
            'error': 'Invalid email or password'
        }), 401
    
    print(f"[Vendor Login] User found: id={user.id}, role={user.role}, email={user.email}")
    
    # Check password (handle old hash format errors)
    try:
        password_valid = user.check_password(data['password'])
        print(f"[Vendor Login] Password check: {password_valid}")
    except Exception as e:
        print(f"[Vendor Login] Password check error (old hash format?): {e}")
        print(f"[Vendor Login] Regenerating password hash...")
        # If password check fails due to hash format, try to update it
        # But only if we can verify the password somehow
        # For now, treat as invalid
        password_valid = False
    
    if not password_valid:
        print(f"[Vendor Login] Invalid password for user: {user.email}")
        return jsonify({
            'error': 'Invalid email or password'
        }), 401

    # Only vendor or admin can use vendor panel
    if user.role not in ('vendor', 'admin'):
        print(f"[Vendor Login] Access denied: role={user.role} (needs vendor or admin)")
        return jsonify({
            'error': 'Access denied. Vendor or admin privileges required.'
        }), 403
    
    print(f"[Vendor Login] Success: user={user.email}, role={user.role}")

    # Generate JWT token
    token = user.generate_token()

    return jsonify({
        'message': 'Vendor login successful',
        'user': user.to_dict(),
        'token': token,
        'token_type': 'Bearer',
        'role': 'vendor'
    }), 200

@vendor_bp.route('/dashboard', methods=['GET'])
@token_required
@vendor_required
def vendor_dashboard():
    """
    Vendor dashboard overview

    GET /api/vendor/dashboard
    Headers: Authorization: Bearer <vendor_token>

    Returns: Summary statistics for vendor panel
    """
    vendor_id = g.current_user.id

    # Start with safe defaults so dashboard can still render.
    total_products = 0
    total_orders = 0
    total_revenue = 0.0
    low_stock_products = []
    recent_orders = []

    try:
        total_products = Product.query.filter_by(vendor_id=vendor_id).count()

        total_orders = db.session.query(db.func.count(db.distinct(Order.id))).join(
            OrderItem, Order.id == OrderItem.order_id
        ).join(
            Product, OrderItem.product_id == Product.id
        ).filter(
            Product.vendor_id == vendor_id
        ).scalar() or 0

        revenue_result = db.session.query(
            db.func.sum(OrderItem.quantity * Product.price)
        ).select_from(Order).join(
            OrderItem, Order.id == OrderItem.order_id
        ).join(
            Product, OrderItem.product_id == Product.id
        ).filter(
            Product.vendor_id == vendor_id
        ).scalar()
        total_revenue = float(revenue_result) if revenue_result else 0.0

        low_stock_products = Product.query.filter(
            Product.vendor_id == vendor_id,
            Product.stock_quantity < 10
        ).all()

        recent_orders = Order.query.join(
            OrderItem, Order.id == OrderItem.order_id
        ).join(
            Product, OrderItem.product_id == Product.id
        ).filter(
            Product.vendor_id == vendor_id
        ).order_by(Order.order_date.desc()).distinct().limit(10).all()

    except Exception as e:
        # Keep UI usable and log root cause in server console for debugging.
        print(f"[Vendor Dashboard] Error: {e}")

    return jsonify({
        'summary': {
            'total_products': int(total_products or 0),
            'total_orders': int(total_orders or 0),
            'total_revenue': round(float(total_revenue or 0), 2)
        },
        'low_stock_alerts': [{
            'id': product.id,
            'name': product.name,
            'stock_quantity': product.stock_quantity,
            'category_name': product.category.name if product.category else None
        } for product in low_stock_products],
        'recent_orders': [order.to_dict() for order in recent_orders]
    }), 200

@vendor_bp.route('/products', methods=['POST'])
@token_required
@vendor_required
def add_product():
    """
    Add new product (vendor only)

    POST /api/vendor/products
    Headers: Authorization: Bearer <vendor_token>
    Body: {
        "name": "Organic Bananas",
        "category_id": 1,
        "price": 2.99,
        "stock_quantity": 50,
        "description": "Fresh organic bananas"
    }

    Returns: Created product details
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['name', 'category_id', 'price']
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            'error': 'Name, category_id, and price are required'
        }), 400

    # Validate price
    if data['price'] <= 0:
        return jsonify({'error': 'Price must be greater than 0'}), 400

    # Validate stock quantity
    if data.get('stock_quantity', 0) < 0:
        return jsonify({'error': 'Stock quantity cannot be negative'}), 400

    try:
        # Check if category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Invalid category_id'}), 400

        # Create new product
        new_product = Product(
            name=data['name'],
            price=data['price'],
            stock_quantity=data.get('stock_quantity', 0),
            category_id=data['category_id'],
            vendor_id=g.current_user.id
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            'message': 'Product added successfully',
            'product': _vendor_product_dict(new_product)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product'}), 500

@vendor_bp.route('/products', methods=['GET'])
@token_required
@vendor_required
def view_my_products():
    """
    View vendor's own products

    GET /api/vendor/products
    Headers: Authorization: Bearer <vendor_token>

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - category_id: Filter by category
    - low_stock: Show only low stock items (true)

    Returns: Vendor's products with pagination
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category_id = request.args.get('category_id', type=int)
        low_stock = request.args.get('low_stock', type=bool)

        # Vendors see only their products; admin can see all products
        if g.current_user.role == 'admin':
            query = Product.query
        else:
            query = Product.query.filter_by(vendor_id=g.current_user.id)

        if category_id:
            query = query.filter_by(category_id=category_id)

        if low_stock:
            query = query.filter(Product.stock_quantity < 10)

        # Get paginated results
        products = query.order_by(Product.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Format product data
        product_list = [_vendor_product_dict(product) for product in products.items]

        return jsonify({
            'products': product_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': products.pages,
                'total_products': products.total,
                'has_next': products.has_next,
                'has_prev': products.has_prev
            },
            'filters': {
                'category_id': category_id,
                'low_stock': low_stock
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch products'}), 500

@vendor_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
@vendor_required
def update_product(product_id):
    """
    Update product price or quantity (vendor only)

    PUT /api/vendor/products/123
    Headers: Authorization: Bearer <vendor_token>
    Body: {
        "price": 3.49,
        "stock_quantity": 75
    }

    Returns: Updated product details
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided for update'}), 400

    try:
        # Vendors can edit only their own products; admin can edit any product
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        if g.current_user.role != 'admin' and product.vendor_id != g.current_user.id:
            return jsonify({'error': 'Product not found or access denied'}), 404

        # Update allowed fields
        updated_fields = []

        if 'price' in data:
            if data['price'] <= 0:
                return jsonify({'error': 'Price must be greater than 0'}), 400
            product.price = data['price']
            updated_fields.append('price')

        if 'stock_quantity' in data:
            if data['stock_quantity'] < 0:
                return jsonify({'error': 'Stock quantity cannot be negative'}), 400
            product.stock_quantity = data['stock_quantity']
            updated_fields.append('stock_quantity')

        if not updated_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        db.session.commit()

        return jsonify({
            'message': 'Product updated successfully',
            'updated_fields': updated_fields,
            'product': _vendor_product_dict(product)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update product'}), 500

@vendor_bp.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
@vendor_required
def delete_product(product_id):
    """
    Delete a product (vendor only, own products only)

    DELETE /api/vendor/products/123
    Headers: Authorization: Bearer <vendor_token>

    Returns: Success message
    """
    try:
        # Vendors can delete only their own products; admin can delete any product
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        if g.current_user.role != 'admin' and product.vendor_id != g.current_user.id:
            return jsonify({'error': 'Product not found or access denied'}), 404

        name = product.name
        db.session.delete(product)
        db.session.commit()

        return jsonify({
            'message': f'Product "{name}" deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product'}), 500


@vendor_bp.route('/orders', methods=['GET'])
@token_required
@vendor_required
def view_my_orders():
    """
    View orders for vendor's products

    GET /api/vendor/orders
    Headers: Authorization: Bearer <vendor_token>

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - status: Filter by order status
    - date_from: Filter from date (YYYY-MM-DD)
    - date_to: Filter to date (YYYY-MM-DD)

    Returns: Orders for vendor's products
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status_filter = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Build query for orders of vendor's products
        query = Order.query.join(OrderItem).join(Product).filter(Product.vendor_id == g.current_user.id).distinct()

        if status_filter:
            query = query.filter(Order.status == status_filter)

        if date_from:
            query = query.filter(Order.order_date >= date_from)

        if date_to:
            query = query.filter(Order.order_date <= date_to + ' 23:59:59')

        # Get paginated results
        orders = query.order_by(Order.order_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Enhanced order data
        order_list = []
        total_revenue = 0

        for order in orders.items:
            order_data = order.to_dict()
            order_total = sum((item.quantity or 0) * (item.product.price if item.product else 0) for item in order.items)
            order_data['order_total'] = order_total
            total_revenue += order_total
            order_list.append(order_data)

        # Get order statistics for vendor's products
        order_stats = db.session.query(
            Order.status,
            db.func.count(db.distinct(Order.id)).label('count'),
            db.func.sum(OrderItem.quantity * Product.price).label('revenue')
        ).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).filter(Product.vendor_id == g.current_user.id).group_by(Order.status).all()

        status_summary = {}
        for status, count, revenue in order_stats:
            status_summary[status] = {
                'count': count,
                'revenue': float(revenue) if revenue else 0
            }

        return jsonify({
            'orders': order_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': orders.pages,
                'total_orders': orders.total,
                'has_next': orders.has_next,
                'has_prev': orders.has_prev
            },
            'statistics': {
                'total_orders': Order.query.join(OrderItem).join(Product).filter(Product.vendor_id == g.current_user.id).distinct().count(),
                'status_summary': status_summary,
                'page_revenue': round(total_revenue, 2)
            },
            'filters': {
                'status': status_filter,
                'date_from': date_from,
                'date_to': date_to
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500


@vendor_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@token_required
@vendor_required
def update_order_status(order_id):
    """
    Update delivery/order status for an order that contains vendor's product.

    PUT /api/vendor/orders/<order_id>/status
    Body: { "status": "pending|confirmed|shipped|delivered|cancelled" }
    """
    data = request.get_json() or {}
    new_status = (data.get('status') or '').strip().lower()
    allowed = {'pending', 'confirmed', 'shipped', 'delivered', 'cancelled'}

    if new_status not in allowed:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        order = Order.query.get(order_id)
        if not order or not order.items:
            return jsonify({'error': 'Order not found'}), 404

        # Ensure vendor owns at least one product line in this order (admin allowed too via vendor_required)
        has_vendor_item = any(item.product and item.product.vendor_id == g.current_user.id for item in order.items)
        if g.token_payload.get('role') != 'admin' and not has_vendor_item:
            return jsonify({'error': 'Forbidden'}), 403

        order.status = new_status
        db.session.commit()

        return jsonify({'message': 'Status updated', 'order': order.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to update status'}), 500
