from flask import request, jsonify, g
from functools import wraps
from .models import User
from . import db

# Alias: login_required = token_required for route protection
def token_required(f):
    """
    Decorator to require authentication token (login_required).
    Use on protected routes; sets g.current_user and g.token_payload.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        # Verify token
        payload = User.verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401

        # Get user from database
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401

        # Add user to request context
        g.current_user = user
        g.token_payload = payload

        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    """
    Decorator to require admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'token_payload') or g.token_payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def vendor_required(f):
    """
    Role-based access: only vendors (and admin) can access.
    Must be used after token_required. Admin can manage all products; vendors only their own.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'token_payload'):
            return jsonify({'error': 'Authentication required'}), 401

        user_role = g.token_payload.get('role')
        # Accept both 'user' (legacy) and 'customer' for clarity; restrict to vendor/admin for panel
        if user_role not in ('admin', 'vendor'):
            return jsonify({'error': 'Vendor or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# Alias for protecting routes with login + role check
login_required = token_required


