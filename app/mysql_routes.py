from flask import Blueprint, request, jsonify
from .mysql_connection import get_db_connection

# Create blueprint for MySQL demonstration routes
mysql_demo = Blueprint('mysql_demo', __name__)

@mysql_demo.route('/mysql/test', methods=['GET'])
def test_mysql_connection():
    """
    Test MySQL connection endpoint
    """
    db = get_db_connection()

    if db.connect():
        # Test basic query
        success, result = db.execute_query("SELECT VERSION() as version")
        db.disconnect()

        if success:
            return jsonify({
                'status': 'success',
                'message': 'MySQL connection successful',
                'mysql_version': result[0]['version'] if result else 'Unknown'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Query failed: {result}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to MySQL'
        }), 500

@mysql_demo.route('/mysql/users', methods=['GET'])
def get_mysql_users():
    """
    Get all users using direct MySQL queries
    """
    db = get_db_connection()

    if not db.connect():
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500

    try:
        # Execute SELECT query
        success, result = db.execute_query("""
            SELECT id, name, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        db.disconnect()

        if success:
            return jsonify({
                'status': 'success',
                'users': result,
                'count': len(result)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Query failed: {result}'
            }), 500

    except Exception as e:
        db.disconnect()
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500

@mysql_demo.route('/mysql/users', methods=['POST'])
def create_mysql_user():
    """
    Create a new user using direct MySQL queries
    """
    data = request.get_json()

    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({
            'status': 'error',
            'message': 'Name, email, and password are required'
        }), 400

    db = get_db_connection()

    if not db.connect():
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500

    try:
        # Check if email already exists
        success, result = db.execute_query(
            "SELECT id FROM users WHERE email = %s",
            (data['email'],)
        )

        if success and result:
            db.disconnect()
            return jsonify({
                'status': 'error',
                'message': 'Email already exists'
            }), 400

        # Insert new user
        insert_query = """
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """

        success, result = db.execute_query(
            insert_query,
            (data['name'], data['email'], data['password'], data.get('role', 'user')),
            fetch=False
        )

        if success:
            # Get the created user
            user_id = db.connection.insert_id()  # Get last inserted ID
            success, user_result = db.execute_query(
                "SELECT id, name, email, role, created_at FROM users WHERE id = %s",
                (user_id,)
            )

            db.disconnect()

            if success and user_result:
                return jsonify({
                    'status': 'success',
                    'message': 'User created successfully',
                    'user': user_result[0]
                }), 201
            else:
                return jsonify({
                    'status': 'success',
                    'message': 'User created but failed to retrieve data'
                }), 201
        else:
            db.disconnect()
            return jsonify({
                'status': 'error',
                'message': f'Failed to create user: {result}'
            }), 500

    except Exception as e:
        db.disconnect()
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500

@mysql_demo.route('/mysql/products/search', methods=['GET'])
def search_mysql_products():
    """
    Search products with error handling
    """
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    db = get_db_connection()

    if not db.connect():
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500

    try:
        # Build dynamic query
        query = """
            SELECT p.id, p.name, c.name AS category_name, p.price, p.stock_quantity,
                   u.name as vendor_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            JOIN users u ON p.vendor_id = u.id
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND c.name = %s"
            params.append(category)

        if min_price is not None:
            query += " AND p.price >= %s"
            params.append(min_price)

        if max_price is not None:
            query += " AND p.price <= %s"
            params.append(max_price)

        query += " ORDER BY p.name"

        success, result = db.execute_query(query, tuple(params) if params else None)

        db.disconnect()

        if success:
            return jsonify({
                'status': 'success',
                'products': result,
                'count': len(result),
                'filters': {
                    'category': category,
                    'min_price': min_price,
                    'max_price': max_price
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Search failed: {result}'
            }), 500

    except Exception as e:
        db.disconnect()
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500


