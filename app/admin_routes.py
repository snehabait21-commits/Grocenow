from flask import Blueprint, request, jsonify, g, render_template, redirect, url_for, session, flash
from . import db
from .models import User, Product, Category, Order, OrderItem, Cart, Admin
from .auth import token_required, admin_required

# API blueprint for existing JSON admin APIs (/api/admin/...)
admin_api_bp = Blueprint('admin_api', __name__)

# Session-based admin panel blueprint (/admin/...)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_api_bp.route('/login', methods=['POST'])
def admin_login_api():
    """
    Admin login API

    POST /api/admin/login
    Body: {
        "email": "admin@grocenow.com",
        "password": "adminpassword123"
    }

    Returns: Admin user data with JWT token
    Note: Only users with 'admin' role can successfully login here
    """
    data = request.get_json()

    # Validate required fields
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({
            'error': 'Email and password are required'
        }), 400

    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    try:
        password_ok = user.check_password(data['password'])
    except Exception:
        password_ok = False
    if not password_ok:
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check if user has admin role
    if user.role != 'admin':
        return jsonify({
            'error': 'Access denied. Admin privileges required.'
        }), 403

    # Generate JWT token
    token = user.generate_token()

    return jsonify({
        'message': 'Admin login successful',
        'user': user.to_dict(),
        'token': token,
        'token_type': 'Bearer',
        'role': 'admin'
    }), 200

@admin_api_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def admin_dashboard_api():
    """
    Admin dashboard overview

    GET /api/admin/dashboard
    Headers: Authorization: Bearer <admin_token>

    Returns: Summary statistics for admin panel
    """
    try:
        # Get summary statistics
        total_users = User.query.count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_categories = Category.query.count()

        # Get recent orders (last 10)
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()

        # Get orders by status
        order_stats = db.session.query(
            Order.status,
            db.func.count(Order.id).label('count')
        ).group_by(Order.status).all()

        order_status_summary = {status: count for status, count in order_stats}

        # Get low stock products (less than 10 items)
        low_stock_products = Product.query.filter(Product.stock_quantity < 10).all()

        return jsonify({
            'summary': {
                'total_users': total_users,
                'total_products': total_products,
                'total_orders': total_orders,
                'total_categories': total_categories
            },
            'order_status_summary': order_status_summary,
            'recent_orders': [order.to_dict() for order in recent_orders],
            'low_stock_alerts': [{
                'id': product.id,
                'name': product.name,
                'stock_quantity': product.stock_quantity,
                'category_name': product.category.name if product.category else None
            } for product in low_stock_products]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@admin_api_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def view_all_users():
    """
    View all users (admin only)

    GET /api/admin/users
    Headers: Authorization: Bearer <admin_token>

    Query Parameters:
    - role: Filter by user role (admin/vendor/user)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)

    Returns: Paginated list of all users
    """
    try:
        # Get query parameters
        role_filter = request.args.get('role')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Build query
        query = User.query

        if role_filter:
            query = query.filter_by(role=role_filter)

        # Get paginated results
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Get user statistics
        user_stats = db.session.query(
            User.role,
            db.func.count(User.id).label('count')
        ).group_by(User.role).all()

        role_summary = {role: count for role, count in user_stats}

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': users.pages,
                'total_users': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            },
            'role_summary': role_summary,
            'filters': {
                'role': role_filter
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch users'}), 500

@admin_api_bp.route('/products', methods=['GET'])
@token_required
@admin_required
def view_all_products():
    """
    View all products (admin only)

    GET /api/admin/products
    Headers: Authorization: Bearer <admin_token>

    Query Parameters:
    - category_id: Filter by category
    - vendor_id: Filter by vendor
    - low_stock: Show only low stock items (quantity < 10)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)

    Returns: Paginated list of all products with vendor info
    """
    try:
        # Get query parameters
        category_id = request.args.get('category_id', type=int)
        vendor_id = request.args.get('vendor_id', type=int)
        low_stock = request.args.get('low_stock', type=bool)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Build query
        query = Product.query

        if category_id:
            query = query.filter_by(category_id=category_id)

        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)

        if low_stock:
            query = query.filter(Product.stock_quantity < 10)

        # Get paginated results
        products = query.order_by(Product.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Enhanced product data with vendor info
        product_list = []
        for product in products.items:
            vendor = User.query.get(product.vendor_id) if product.vendor_id else None
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock_quantity': product.stock_quantity,
                'category_id': product.category_id,
                'category_name': product.category.name if product.category else None,
                'vendor_id': product.vendor_id,
                'vendor': {
                    'id': vendor.id,
                    'name': vendor.name,
                    'email': vendor.email
                } if vendor else None,
            }
            product_list.append(product_data)

        # Get product statistics
        total_products = Product.query.count()
        low_stock_count = Product.query.filter(Product.stock_quantity < 10).count()
        out_of_stock_count = Product.query.filter(Product.stock_quantity == 0).count()

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
            'statistics': {
                'total_products': total_products,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count
            },
            'filters': {
                'category_id': category_id,
                'vendor_id': vendor_id,
                'low_stock': low_stock
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch products'}), 500

@admin_api_bp.route('/orders', methods=['GET'])
@token_required
@admin_required
def view_all_orders():
    """
    View all orders (admin only)

    GET /api/admin/orders
    Headers: Authorization: Bearer <admin_token>

    Query Parameters:
    - status: Filter by order status
    - user_id: Filter by customer
    - date_from: Filter orders from date (YYYY-MM-DD)
    - date_to: Filter orders to date (YYYY-MM-DD)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)

    Returns: Paginated list of all orders with customer and product info
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        user_id = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Build query
        query = Order.query

        if status_filter:
            query = query.filter_by(status=status_filter)

        if user_id:
            query = query.filter_by(user_id=user_id)

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
            order_total = order_data.get('order_total', 0)
            total_revenue += order_total
            order_list.append(order_data)

        # Get order statistics
        order_stats = db.session.query(
            Order.status,
            db.func.count(db.distinct(Order.id)).label('count'),
            db.func.sum(OrderItem.quantity * Product.price).label('revenue')
        ).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).group_by(Order.status).all()

        status_summary = {}
        for status, count, revenue in order_stats:
            status_summary[status] = {
                'count': count,
                'revenue': float(revenue) if revenue else 0
            }

        # Calculate total revenue for current page
        page_revenue = sum(order['order_total'] for order in order_list)

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
                'total_orders': Order.query.count(),
                'status_summary': status_summary,
                'page_revenue': round(page_revenue, 2)
            },
            'filters': {
                'status': status_filter,
                'user_id': user_id,
                'date_from': date_from,
                'date_to': date_to
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch orders'}), 500

@admin_api_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user_details(user_id):
    """
    Get detailed information about a specific user (admin only)

    GET /api/admin/users/1
    Headers: Authorization: Bearer <admin_token>

    Returns: User details with their orders and cart
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get user's orders
        user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()

        # Get user's cart items
        user_cart = Cart.query.filter_by(user_id=user_id).all()

        # Calculate user statistics
        total_orders = len(user_orders)
        total_spent = sum(order.to_dict().get('order_total', 0) for order in user_orders)
        cart_items_count = len(user_cart)

        return jsonify({
            'user': user.to_dict(),
            'statistics': {
                'total_orders': total_orders,
                'total_spent': round(total_spent, 2),
                'cart_items_count': cart_items_count
            },
            'recent_orders': [order.to_dict() for order in user_orders[:5]],  # Last 5 orders
            'cart_items': [cart_item.to_dict() for cart_item in user_cart]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch user details'}), 500

@admin_api_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics():
    """
    Get analytics data for admin dashboard

    GET /api/admin/analytics
    Headers: Authorization: Bearer <admin_token>

    Returns: Various analytics and insights
    """
    try:
        # Revenue analytics
        revenue_stats = db.session.query(
            db.func.date(Order.order_date).label('date'),
            db.func.sum(OrderItem.quantity * Product.price).label('revenue'),
            db.func.count(db.distinct(Order.id)).label('orders_count')
        ).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).group_by(db.func.date(Order.order_date)).order_by(db.func.date(Order.order_date).desc()).limit(30).all()

        # Top selling products
        top_products = db.session.query(
            Product,
            db.func.sum(OrderItem.quantity).label('total_sold'),
            db.func.sum(OrderItem.quantity * Product.price).label('total_revenue')
        ).join(OrderItem, OrderItem.product_id == Product.id).group_by(Product.id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(10).all()

        # Top customers by spending
        top_customers = db.session.query(
            User,
            db.func.sum(OrderItem.quantity * Product.price).label('total_spent'),
            db.func.count(db.distinct(Order.id)).label('orders_count')
        ).join(Order, User.id == Order.user_id).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).group_by(User.id).order_by(db.func.sum(OrderItem.quantity * Product.price).desc()).limit(10).all()

        return jsonify({
            'revenue_trends': [{
                'date': str(date),
                'revenue': float(revenue),
                'orders_count': orders_count
            } for date, revenue, orders_count in revenue_stats],
            'top_products': [{
                'id': product.id,
                'name': product.name,
                'total_sold': total_sold,
                'total_revenue': float(total_revenue)
            } for product, total_sold, total_revenue in top_products],
            'top_customers': [{
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'total_spent': float(total_spent),
                'orders_count': orders_count
            } for user, total_spent, orders_count in top_customers]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch analytics'}), 500


# -----------------------
# Session-based Admin UI
# -----------------------

def admin_login_required(view_func):
    """Decorator to ensure admin is logged in via session."""
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin.admin_login'))
        return view_func(*args, **kwargs)

    return wrapped


@admin_bp.route('/')
def admin_index():
    if 'admin_id' in session:
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Render and handle admin login form (session-based)."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('admin/login.html')

        # Use general User model with admin role for login
        admin = User.query.filter_by(email=username, role='admin').first()
        if not admin or not admin.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('admin/login.html')

        session['admin_id'] = admin.id
        return redirect(url_for('admin.admin_dashboard'))

    # GET
    return render_template('admin/login.html')


@admin_bp.route('/dashboard')
@admin_login_required
def admin_dashboard():
    """Admin dashboard page with key counts."""
    total_products = Product.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()

    # Simple analytics for charts (last 7 days)
    try:
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        start = today - timedelta(days=6)

        # Orders count per day (last 7)
        rows = db.session.query(
            db.func.date(Order.order_date).label('d'),
            db.func.count(Order.id).label('c'),
            db.func.sum(OrderItem.quantity * Product.price).label('rev')
        ).join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).filter(Order.order_date >= start).group_by(db.func.date(Order.order_date)).all()

        by_day = {str(d): {'count': int(c or 0), 'revenue': float(rev or 0)} for d, c, rev in rows}
        labels = [(start + timedelta(days=i)).isoformat() for i in range(7)]
        orders_series = [by_day.get(day, {}).get('count', 0) for day in labels]
        revenue_series = [round(by_day.get(day, {}).get('revenue', 0), 2) for day in labels]

        # Order status breakdown
        st_rows = db.session.query(Order.status, db.func.count(Order.id)).group_by(Order.status).all()
        status_labels = [s or 'pending' for s, _ in st_rows]
        status_counts = [int(c or 0) for _, c in st_rows]
    except Exception:
        labels, orders_series, revenue_series, status_labels, status_counts = [], [], [], [], []

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        chart_labels=labels,
        chart_orders=orders_series,
        chart_revenue=revenue_series,
        status_labels=status_labels,
        status_counts=status_counts,
    )


@admin_bp.route('/products')
@admin_login_required
def admin_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin/products.html', products=products)


@admin_bp.route('/add-product', methods=['GET', 'POST'])
@admin_login_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock_quantity', '').strip() or '0'
        category_id = request.form.get('category_id', '').strip()

        if not name or not price or not category_id:
            flash('Name, price and category are required.', 'danger')
            return redirect(url_for('admin.admin_add_product'))

        try:
            product = Product(
                name=name,
                price=float(price),
                stock_quantity=int(stock),
                category_id=int(category_id),
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to add product.', 'danger')

        return redirect(url_for('admin.admin_products'))

    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin/add_product.html', categories=categories)


@admin_bp.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@admin_login_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip() or product.name
        product.price = float(request.form.get('price', product.price))
        product.stock_quantity = int(request.form.get('stock_quantity', product.stock_quantity))
        product.category_id = int(request.form.get('category_id', product.category_id))

        try:
            db.session.commit()
            flash('Product updated successfully.', 'success')
        except Exception:
            db.session.rollback()
            flash('Failed to update product.', 'danger')

        return redirect(url_for('admin.admin_products'))

    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin/edit_product.html', product=product, categories=categories)


@admin_bp.route('/delete-product/<int:product_id>', methods=['GET'])
@admin_login_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete product.', 'danger')

    return redirect(url_for('admin.admin_products'))


@admin_bp.route('/logout')
@admin_login_required
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin.admin_login'))