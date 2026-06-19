from flask import Blueprint, request, jsonify
from datetime import datetime
from . import db
from .models import Product, Category

# Create blueprint for API routes
api = Blueprint('api', __name__)

DEFAULT_CATEGORY_NAMES = ['Vegetables', 'Fruits', 'Juice', 'Dried']


def _find_category_by_name(category_name):
    """Case-insensitive category lookup with singular/plural fallback."""
    if not category_name:
        return None
    category_name = str(category_name).strip()
    category = Category.query.filter(db.func.lower(Category.name) == category_name.lower()).first()
    if category:
        return category
    alt_name = category_name[:-1] if category_name.endswith('s') else category_name + 's'
    return Category.query.filter(db.func.lower(Category.name) == alt_name.lower()).first()


def _ensure_default_categories():
    """Ensure storefront categories exist even if the table is partially seeded."""
    created = False
    for name in DEFAULT_CATEGORY_NAMES:
        if not _find_category_by_name(name):
            db.session.add(Category(name=name))
            created = True
    if created:
        db.session.commit()


def _category_dict(category):
    return {
        'id': category.id,
        'name': category.name,
    }


def _product_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock_quantity': product.stock_quantity,
        'category_id': product.category_id,
        'category_name': product.category.name if product.category else None,
        'vendor_id': product.vendor_id,
    }


@api.route('/ping', methods=['GET'])
def ping():
    """Minimal check - no database. Returns 200 if Flask is up."""
    return jsonify({'ok': True}), 200


@api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - always returns 200 if Flask is running.
    """
    db_status = 'Unknown'
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'Connected'
    except Exception as e:
        db_status = f'Error: {str(e)}'

    return jsonify({
        'status': 'OK',
        'message': 'GroceNow API is running',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@api.route('/categories', methods=['GET'])
def get_categories():
    """
    Get all categories
    """
    try:
        _ensure_default_categories()
        categories = Category.query.filter(db.func.lower(Category.name) != 'online orders').all()
        return jsonify([_category_dict(cat) for cat in categories])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to load categories: {str(e)}'}), 500

@api.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category
    """
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400

    name = str(data['name']).strip()
    if not name:
        return jsonify({'error': 'Category name is required'}), 400

    existing_category = _find_category_by_name(name)
    if existing_category:
        return jsonify({'error': 'Category already exists'}), 400

    try:
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        return jsonify(_category_dict(new_category)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create category: {str(e)}'}), 500

@api.route('/products', methods=['GET'])
def get_products():
    """
    Get all products with optional category filter
    """
    category_id = request.args.get('category_id', type=int)

    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
    else:
        products = Product.query.all()

    return jsonify([_product_dict(prod) for prod in products])

@api.route('/products', methods=['POST'])
def create_product():
    """
    Create a new product using direct MySQL queries
    Uses current table structure: name, category_id, price, stock_quantity, vendor_id, description
    """
    from .mysql_connection import get_db_connection
    
    print("\n[API] POST /api/products - Add product request received")
    data = request.get_json()

    # Validate required fields
    required_fields = ['name', 'price', 'quantity']
    if not data or not all(field in data for field in required_fields):
        print("[API] Validation failed: Name, price, and quantity are required")
        return jsonify({'error': 'Name, price, and quantity are required'}), 400

    # Validate price
    try:
        price = float(data['price'])
        if price <= 0:
            print("[API] Validation failed: Price must be greater than 0")
            return jsonify({'error': 'Price must be greater than 0'}), 400
    except (ValueError, TypeError):
        print("[API] Validation failed: Invalid price format")
        return jsonify({'error': 'Invalid price format'}), 400

    # Validate quantity
    try:
        quantity = int(data['quantity'])
        if quantity < 0:
            print("[API] Validation failed: Quantity cannot be negative")
            return jsonify({'error': 'Quantity cannot be negative'}), 400
    except (ValueError, TypeError):
        print("[API] Validation failed: Invalid quantity format")
        return jsonify({'error': 'Invalid quantity format'}), 400

    # Get other fields with defaults
    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Product name cannot be empty'}), 400

    category_id = data.get('category_id')
    vendor_id = data.get('vendor_id', 2)  # Default vendor_id (usually 2)
    description = data.get('description', '').strip()

    # Connect to database
    db_conn = get_db_connection()
    if not db_conn.connect():
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Verify vendor exists
        success, vendor_result = db_conn.execute_query(
            "SELECT id FROM users WHERE id = %s AND role = 'vendor'",
            (vendor_id,)
        )
        if not success or not vendor_result:
            db_conn.disconnect()
            print(f"[API] Validation failed: Invalid vendor_id={vendor_id}")
            return jsonify({'error': 'Invalid vendor_id'}), 400

        # Resolve category_id from category name when needed
        if not category_id:
            category_name = (data.get('category') or '').strip() or 'Vegetables'
            success, category_result = db_conn.execute_query(
                "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s) LIMIT 1",
                (category_name,)
            )
            if success and category_result:
                category_id = category_result[0]['id']
            else:
                db_conn.disconnect()
                return jsonify({'error': 'Invalid category/category_id'}), 400

        # Insert new product
        insert_query = """
            INSERT INTO products (name, category_id, price, stock_quantity, vendor_id, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        success, result = db_conn.execute_query(
            insert_query,
            (name, category_id, price, quantity, vendor_id, description),
            fetch=False
        )

        if success:
            # Get the created product
            product_id = db_conn.connection.insert_id()
            success, product_result = db_conn.execute_query(
                """SELECT p.id, p.name, p.category_id, c.name AS category_name, p.price, p.stock_quantity, p.vendor_id, p.description, p.created_at
                   FROM products p
                   LEFT JOIN categories c ON p.category_id = c.id
                   WHERE p.id = %s""",
                (product_id,)
            )

            db_conn.disconnect()

            if success and product_result:
                print(f"[API] Product added successfully: id={product_id}, name=\"{name}\", category_id={category_id}, price={price}, quantity={quantity}")
                return jsonify({
                    'success': True,
                    'product': product_result[0]
                }), 201
            else:
                print(f"[API] Product added successfully: id={product_id}, name=\"{name}\"")
                return jsonify({
                    'success': True,
                    'message': 'Product created successfully'
                }), 201
        else:
            db_conn.disconnect()
            print(f"[API] Insert failed: {result}")
            return jsonify({'error': f'Failed to create product: {result}'}), 500

    except Exception as e:
        db_conn.disconnect()
        print(f"[API] Error adding product: {e}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get a specific product by ID
    """
    product = Product.query.get_or_404(product_id)
    return jsonify(_product_dict(product))

@api.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Update a product
    """
    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update fields if provided
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = data['price']
    if 'stock_quantity' in data:
        product.stock_quantity = data['stock_quantity']
    if 'category_id' in data:
        # Verify category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Invalid category_id'}), 400
        product.category_id = data['category_id']

    db.session.commit()

    return jsonify(_product_dict(product))

@api.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Delete a product
    """
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': f'Product {product.name} deleted successfully'})

    
