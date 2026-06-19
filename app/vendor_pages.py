"""
Vendor blueprint: serves Vendor Panel pages.
All dashboard routes serve the same SPA; protection is login_required + role check (client-side).
Routes: /vendor/login, /vendor/dashboard, /vendor/add-product, /vendor/edit-product/<id>,
        /vendor/delete-product/<id>, /vendor/orders
"""
import os
from flask import Blueprint, send_from_directory

# Project root (parent of app package)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
VENDOR_HTML_DIR = os.path.join(PROJECT_ROOT, 'vendor')

vendor_pages_bp = Blueprint('vendor_pages', __name__, url_prefix='/vendor')


def _send_dashboard():
    """Serve vendor dashboard SPA. Auth and role check done client-side."""
    return send_from_directory(VENDOR_HTML_DIR, 'dashboard.html')


@vendor_pages_bp.route('/login')
def login_page():
    """Vendor login page. No auth required."""
    return send_from_directory(VENDOR_HTML_DIR, 'login.html')


@vendor_pages_bp.route('/dashboard')
@vendor_pages_bp.route('/')
def dashboard_page():
    """Vendor dashboard (overview). Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/add-product')
def add_product_page():
    """Add product page. Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/my-products')
def my_products_page():
    """My products list. Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/edit-product/<int:product_id>')
def edit_product_page(product_id):
    """Edit product page. Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/delete-product/<int:product_id>')
def delete_product_page(product_id):
    """Delete product page (optional; SPA also has delete in list). Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/delete-product')
def delete_product_list_page():
    """Delete product list page. Protected client-side."""
    return _send_dashboard()


@vendor_pages_bp.route('/orders')
def orders_page():
    """Vendor orders page. Protected client-side."""
    return _send_dashboard()
