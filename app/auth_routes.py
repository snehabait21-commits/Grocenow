from flask import Blueprint, request, jsonify, session, g
from . import db
from .models import User
from .auth import token_required

# Create blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration API

    POST /api/auth/register
    Body: {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepassword123",
        "role": "customer"  // optional, defaults to "customer" (admin, vendor, customer)
    }

    Returns: User data with JWT token
    """
    data = request.get_json()

    # Validate required fields
    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({
            'error': 'Name, email, and password are required'
        }), 400

    # Validate email format (basic check)
    if '@' not in data['email'] or '.' not in data['email']:
        return jsonify({'error': 'Invalid email format'}), 400

    # Check password strength (minimum 6 characters)
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 409

    # Create new user
    new_user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'customer')  # Default: customer (admin, vendor, customer)
    )
    new_user.set_password(data['password'])

    try:
        db.session.add(new_user)
        db.session.commit()

        # Generate token for immediate login
        token = new_user.generate_token()

        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict(),
            'token': token,
            'token_type': 'Bearer'
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")  # Log for debugging
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login API

    POST /api/auth/login
    Body: {
        "email": "john@example.com",
        "password": "securepassword123"
    }

    Returns: User data with JWT token
    """
    data = request.get_json()

    # Validate required fields
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({
            'error': 'Email and password are required'
        }), 400

    # Find user by email
    user = User.query.filter_by(email=data['email']).first()

    # Check if user exists and password is correct
    if not user or not user.check_password(data['password']):
        return jsonify({
            'error': 'Invalid email or password'
        }), 401

    # Generate JWT token
    token = user.generate_token()

    # Keep lightweight customer session data for template rendering
    session['customer_user'] = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    }

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'token': token,
        'token_type': 'Bearer'
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """
    Get current user profile

    GET /api/auth/profile
    Headers: Authorization: Bearer <token>

    Returns: Current user data
    """
    return jsonify({
        'user': g.current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """
    Update current user profile

    PUT /api/auth/profile
    Headers: Authorization: Bearer <token>
    Body: {
        "name": "Updated Name",
        "email": "newemail@example.com"
    }

    Returns: Updated user data
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update allowed fields
    if 'name' in data and data['name'].strip():
        g.current_user.name = data['name'].strip()

    if 'email' in data and data['email'].strip():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != g.current_user.id:
            return jsonify({'error': 'Email already taken'}), 409
        g.current_user.email = data['email'].strip()

    try:
        db.session.commit()

        # Generate new token in case email changed
        token = g.current_user.generate_token()

        return jsonify({
            'message': 'Profile updated successfully',
            'user': g.current_user.to_dict(),
            'token': token
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verify if a token is valid

    POST /api/auth/verify-token
    Body: {
        "token": "jwt_token_here"
    }

    Returns: Token validity and user data if valid
    """
    data = request.get_json()

    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400

    payload = User.verify_token(data['token'])
    if not payload:
        return jsonify({
            'valid': False,
            'error': 'Token is invalid or expired'
        }), 401

    # Get user data
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({
            'valid': False,
            'error': 'User not found'
        }), 401

    return jsonify({
        'valid': True,
        'user': user.to_dict(),
        'token_data': {
            'user_id': payload['user_id'],
            'email': payload['email'],
            'role': payload['role']
        }
    }), 200
