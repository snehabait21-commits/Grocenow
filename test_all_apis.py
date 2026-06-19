#!/usr/bin/env python3
"""
Comprehensive API Test Suite for GroceNow
Tests all APIs: Authentication, User, Admin, Vendor, Cart, Orders
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

class APITester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []

    def log_result(self, test_name, success, message="", response=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        if response:
            result['status_code'] = response.status_code
            result['response_time'] = getattr(response, 'elapsed', None)

        self.test_results.append(result)
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        print()

    def run_test(self, test_func):
        """Run a test function with error handling"""
        try:
            return test_func()
        except Exception as e:
            self.log_result(test_func.__name__, False, f"Exception: {str(e)}")
            return False

    # Authentication Tests
    def test_user_registration(self):
        """Test user registration"""
        data = {
            "name": "Test User API",
            "email": f"test_api_{int(time.time())}@example.com",
            "password": "testpass123",
            "role": "user"
        }

        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 201 and result and 'token' in result:
            self.tokens['user'] = result['token']
            self.log_result("User Registration", True, f"User created: {result['user']['email']}", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("User Registration", False, f"Failed: {error_msg}", response)
            return False

    def test_user_login(self):
        """Test user login"""
        data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'token' in result:
            self.tokens['user'] = result['token']
            self.log_result("User Login", True, f"Login successful for: {result['user']['email']}", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("User Login", False, f"Failed: {error_msg}", response)
            return False

    def test_admin_login(self):
        """Test admin login"""
        data = {
            "email": "admin@grocenow.com",
            "password": "adminpassword123"
        }

        response = requests.post(f"{BASE_URL}/api/admin/login", json=data)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'token' in result:
            self.tokens['admin'] = result['token']
            self.log_result("Admin Login", True, f"Admin login successful", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Admin Login", False, f"Failed: {error_msg}", response)
            return False

    def test_vendor_login(self):
        """Test vendor login"""
        data = {
            "email": "vendor@grocenow.com",
            "password": "vendorpassword123"
        }

        response = requests.post(f"{BASE_URL}/api/vendor/login", json=data)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'token' in result:
            self.tokens['vendor'] = result['token']
            self.log_result("Vendor Login", True, f"Vendor login successful", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Vendor Login", False, f"Failed: {error_msg}", response)
            return False

    # User/Cart/Order Tests
    def test_browse_products(self):
        """Test browsing products"""
        headers = {"Authorization": f"Bearer {self.tokens.get('user', '')}"}

        response = requests.get(f"{BASE_URL}/api/user/products", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'products' in result:
            products_count = len(result['products'])
            self.log_result("Browse Products", True, f"Found {products_count} products", response)
            return result['products'][0]['id'] if result['products'] else None
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Browse Products", False, f"Failed: {error_msg}", response)
            return None

    def test_add_to_cart(self, product_id):
        """Test adding item to cart"""
        if not self.tokens.get('user'):
            self.log_result("Add to Cart", False, "No user token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['user']}"}
        data = {
            "product_id": product_id,
            "quantity": 2
        }

        response = requests.post(f"{BASE_URL}/api/user/cart", json=data, headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 201 and result and 'cart_item' in result:
            self.log_result("Add to Cart", True, f"Added product {product_id} to cart", response)
            return result['cart_item']['id']
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Add to Cart", False, f"Failed: {error_msg}", response)
            return None

    def test_view_cart(self):
        """Test viewing cart"""
        if not self.tokens.get('user'):
            self.log_result("View Cart", False, "No user token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['user']}"}

        response = requests.get(f"{BASE_URL}/api/user/cart", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result:
            items_count = result.get('total_items', 0)
            total_amount = result.get('total_amount', 0)
            self.log_result("View Cart", True, f"Cart has {items_count} items, total: ${total_amount}", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("View Cart", False, f"Failed: {error_msg}", response)
            return False

    def test_place_order(self):
        """Test placing order"""
        if not self.tokens.get('user'):
            self.log_result("Place Order", False, "No user token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['user']}"}

        response = requests.post(f"{BASE_URL}/api/user/orders", json={}, headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 201 and result and 'orders' in result:
            orders_count = len(result['orders'])
            total_amount = result.get('total_amount', 0)
            self.log_result("Place Order", True, f"Created {orders_count} orders, total: ${total_amount}", response)
            return result['orders'][0]['id'] if result['orders'] else None
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Place Order", False, f"Failed: {error_msg}", response)
            return None

    # Admin Tests
    def test_admin_dashboard(self):
        """Test admin dashboard"""
        if not self.tokens.get('admin'):
            self.log_result("Admin Dashboard", False, "No admin token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}

        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'summary' in result:
            users_count = result['summary'].get('total_users', 0)
            products_count = result['summary'].get('total_products', 0)
            self.log_result("Admin Dashboard", True, f"Dashboard: {users_count} users, {products_count} products", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Admin Dashboard", False, f"Failed: {error_msg}", response)
            return False

    def test_admin_users(self):
        """Test admin viewing users"""
        if not self.tokens.get('admin'):
            self.log_result("Admin View Users", False, "No admin token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}

        response = requests.get(f"{BASE_URL}/api/admin/users?page=1&per_page=5", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'users' in result:
            users_count = len(result['users'])
            total_users = result['pagination']['total_users']
            self.log_result("Admin View Users", True, f"Retrieved {users_count} users (total: {total_users})", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Admin View Users", False, f"Failed: {error_msg}", response)
            return False

    # Vendor Tests
    def test_vendor_dashboard(self):
        """Test vendor dashboard"""
        if not self.tokens.get('vendor'):
            self.log_result("Vendor Dashboard", False, "No vendor token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['vendor']}"}

        response = requests.get(f"{BASE_URL}/api/vendor/dashboard", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 200 and result and 'summary' in result:
            products_count = result['summary'].get('total_products', 0)
            revenue = result['summary'].get('total_revenue', 0)
            self.log_result("Vendor Dashboard", True, f"Dashboard: {products_count} products, ${revenue} revenue", response)
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Vendor Dashboard", False, f"Failed: {error_msg}", response)
            return False

    def test_vendor_add_product(self):
        """Test vendor adding product"""
        if not self.tokens.get('vendor'):
            self.log_result("Vendor Add Product", False, "No vendor token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['vendor']}"}

        # Get a category first
        cat_response = requests.get(f"{BASE_URL}/api/categories")
        category_id = 1  # Default fallback

        if cat_response.status_code == 200:
            categories = cat_response.json()
            if categories:
                category_id = categories[0]['id']

        data = {
            "name": f"Test Product {int(time.time())}",
            "category_id": category_id,
            "price": 9.99,
            "stock_quantity": 10,
            "description": "Test product from vendor API"
        }

        response = requests.post(f"{BASE_URL}/api/vendor/products", json=data, headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 201 and result and 'product' in result:
            product_name = result['product']['name']
            self.log_result("Vendor Add Product", True, f"Product created: {product_name}", response)
            return result['product']['id']
        else:
            error_msg = result.get('error', 'Unknown error') if result else f"HTTP {response.status_code}"
            self.log_result("Vendor Add Product", False, f"Failed: {error_msg}", response)
            return None

    # Error Handling Tests
    def test_invalid_authentication(self):
        """Test invalid authentication"""
        headers = {"Authorization": "Bearer invalid_token"}

        response = requests.get(f"{BASE_URL}/api/user/products", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 401:
            self.log_result("Invalid Authentication", True, "Correctly rejected invalid token", response)
            return True
        else:
            self.log_result("Invalid Authentication", False, f"Expected 401, got {response.status_code}", response)
            return False

    def test_insufficient_permissions(self):
        """Test insufficient permissions (user trying admin)"""
        if not self.tokens.get('user'):
            self.log_result("Insufficient Permissions", False, "No user token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['user']}"}

        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 403:
            self.log_result("Insufficient Permissions", True, "Correctly denied user access to admin API", response)
            return True
        else:
            self.log_result("Insufficient Permissions", False, f"Expected 403, got {response.status_code}", response)
            return False

    def test_invalid_product_id(self):
        """Test invalid product ID"""
        if not self.tokens.get('user'):
            self.log_result("Invalid Product ID", False, "No user token available")
            return False

        headers = {"Authorization": f"Bearer {self.tokens['user']}"}
        data = {
            "product_id": 99999,  # Non-existent product
            "quantity": 1
        }

        response = requests.post(f"{BASE_URL}/api/user/cart", json=data, headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 404 or (result and 'not found' in result.get('error', '').lower()):
            self.log_result("Invalid Product ID", True, "Correctly handled invalid product ID", response)
            return True
        else:
            self.log_result("Invalid Product ID", False, f"Expected error for invalid product, got {response.status_code}", response)
            return False

    def test_insufficient_stock(self):
        """Test insufficient stock error"""
        if not self.tokens.get('user'):
            self.log_result("Insufficient Stock", False, "No user token available")
            return False

        # Find a product and try to order more than available stock
        headers = {"Authorization": f"Bearer {self.tokens['user']}"}

        # Get products first
        products_response = requests.get(f"{BASE_URL}/api/user/products", headers=headers)
        if products_response.status_code != 200:
            self.log_result("Insufficient Stock", False, "Could not get products")
            return False

        products = products_response.json().get('products', [])
        if not products:
            self.log_result("Insufficient Stock", False, "No products available")
            return False

        # Use first product and try to order 999 units
        product_id = products[0]['id']
        data = {
            "product_id": product_id,
            "quantity": 999
        }

        response = requests.post(f"{BASE_URL}/api/user/cart", json=data, headers=headers)
        result = response.json() if response.status_code < 400 else None

        if response.status_code == 400 and result and 'insufficient stock' in result.get('error', '').lower():
            self.log_result("Insufficient Stock", True, "Correctly handled insufficient stock", response)
            return True
        else:
            self.log_result("Insufficient Stock", False, f"Expected stock error, got {response.status_code}", response)
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE API TEST SUMMARY")
        print("="*80)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(".1f")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")

        print(f"\n🔐 Authentication Tokens Acquired:")
        for role, token in self.tokens.items():
            print(f"  • {role}: {'✓' if token else '✗'}")

        print("\n" + "="*80)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Test Suite")
        print("Make sure your Flask server is running on http://localhost:5000")
        print("="*80)

        # Authentication Tests
        print("🔐 Testing Authentication...")
        self.run_test(self.test_user_login)
        self.run_test(self.test_admin_login)
        self.run_test(self.test_vendor_login)
        self.run_test(self.test_user_registration)

        # User/Cart/Order Tests
        print("🛒 Testing User/Cart/Order APIs...")
        product_id = self.run_test(self.test_browse_products)
        if product_id:
            cart_item_id = self.run_test(lambda: self.test_add_to_cart(product_id))
            self.run_test(self.test_view_cart)
            order_id = self.run_test(self.test_place_order)

        # Admin Tests
        print("👑 Testing Admin APIs...")
        self.run_test(self.test_admin_dashboard)
        self.run_test(self.test_admin_users)

        # Vendor Tests
        print("🏪 Testing Vendor APIs...")
        self.run_test(self.test_vendor_dashboard)
        product_id = self.run_test(self.test_vendor_add_product)

        # Error Handling Tests
        print("🚨 Testing Error Handling...")
        self.run_test(self.test_invalid_authentication)
        self.run_test(self.test_insufficient_permissions)
        self.run_test(self.test_invalid_product_id)
        self.run_test(self.test_insufficient_stock)

        # Print summary
        self.print_summary()

def main():
    """Run the comprehensive test suite"""
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()


