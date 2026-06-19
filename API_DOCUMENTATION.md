# GroceNow REST API Documentation

Complete API reference for the GroceNow grocery ordering system.

## 📋 Table of Contents
1. [Authentication APIs](#authentication-apis)
2. [User Functionality APIs](#user-functionality-apis)
3. [Admin Panel APIs](#admin-panel-apis)
4. [Admin/Product Management APIs](#adminproduct-management-apis)
5. [Error Handling](#error-handling)
6. [Data Models](#data-models)

## 🔐 Authentication APIs

All user functionality APIs require JWT authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### 1. Register User
**Endpoint**: `POST /api/auth/register`

**Purpose**: Create a new user account

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "role": "user"
}
```

**Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "created_at": "2024-01-01T10:00:00Z"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer"
}
```

**Validation**:
- Name, email, password required
- Email must be unique
- Password minimum 6 characters
- Role defaults to "user" (admin/vendor/user)

---

### 2. Login User
**Endpoint**: `POST /api/auth/login`

**Purpose**: Authenticate user and get access token

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer"
}
```

**Error Responses**:
- 401: Invalid email or password

---

### 3. Get User Profile
**Endpoint**: `GET /api/auth/profile`

**Purpose**: Get current user profile information

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

---

### 4. Update Profile
**Endpoint**: `PUT /api/auth/profile`

**Purpose**: Update user profile information

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "name": "Updated Name",
  "email": "newemail@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "name": "Updated Name",
    "email": "newemail@example.com",
    "role": "user"
  },
  "token": "new_jwt_token_if_email_changed"
}
```

---

### 5. Verify Token
**Endpoint**: `POST /api/auth/verify-token`

**Purpose**: Verify if a JWT token is valid

**Request Body**:
```json
{
  "token": "jwt_token_here"
}
```

**Response** (200 OK):
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user"
  },
  "token_data": {
    "user_id": 1,
    "email": "john@example.com",
    "role": "user"
  }
}
```

## 🏪 Vendor Panel APIs

**All vendor APIs require vendor or admin role and JWT authentication**

**Logic Overview:**
- **Ownership Check**: Vendors can only manage their own products (`vendor_id` must match authenticated user)
- **Order Tracking**: Shows orders for all products owned by the vendor
- **Revenue Calculation**: Calculates earnings from vendor's products only
- **Stock Management**: Vendors manage inventory for their products
- **Access Control**: `@vendor_required` decorator allows both vendors and admins to access

**Security Principle:** Vendors have full control over their products but cannot access other vendors' data.

### 1. Vendor Login
**Endpoint**: `POST /api/vendor/login`

**Purpose**: Authenticate vendor user and get access token

**Request Body**:
```json
{
  "email": "vendor@grocenow.com",
  "password": "vendorpassword123"
}
```

**Response** (200 OK):
```json
{
  "message": "Vendor login successful",
  "user": {
    "id": 2,
    "name": "Fresh Foods Vendor",
    "email": "vendor@grocenow.com",
    "role": "vendor"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "role": "vendor"
}
```

**Note**: Only users with `role: "vendor"` can login via this endpoint. Admins must use `/api/admin/login`.

---

### 2. Vendor Dashboard
**Endpoint**: `GET /api/vendor/dashboard`

**Purpose**: Get overview statistics for vendor panel

**Headers**: `Authorization: Bearer <vendor_token>`

**Response** (200 OK):
```json
{
  "summary": {
    "total_products": 12,
    "total_orders": 45,
    "total_revenue": 1250.75
  },
  "low_stock_alerts": [
    {
      "id": 5,
      "name": "Organic Apples",
      "stock_quantity": 5,
      "category_name": "Fruits"
    }
  ],
  "recent_orders": [...]
}
```

---

### 3. Add Product
**Endpoint**: `POST /api/vendor/products`

**Purpose**: Add a new product to the catalog

**Headers**: `Authorization: Bearer <vendor_token>`

**Request Body**:
```json
{
  "name": "Organic Bananas",
  "category_id": 1,
  "price": 2.99,
  "stock_quantity": 50,
  "description": "Fresh organic bananas"
}
```

**Response** (201 Created):
```json
{
  "message": "Product added successfully",
  "product": {
    "id": 15,
    "name": "Organic Bananas",
    "description": "Fresh organic bananas",
    "price": 2.99,
    "stock_quantity": 50,
    "category_id": 1,
    "category_name": "Fruits",
    "vendor_id": 2,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

**Logic**: Automatically assigns `vendor_id` from the authenticated vendor's user ID.

---

### 4. View My Products
**Endpoint**: `GET /api/vendor/products`

**Purpose**: Get paginated list of vendor's own products

**Headers**: `Authorization: Bearer <vendor_token>`

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `category_id`: Filter by category
- `low_stock`: Show only low stock items (true)

**Response** (200 OK):
```json
{
  "products": [
    {
      "id": 1,
      "name": "Organic Apples",
      "price": 3.99,
      "stock_quantity": 100,
      "category_name": "Fruits",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 1,
    "total_products": 12,
    "has_next": false,
    "has_prev": false
  },
  "filters": {
    "category_id": null,
    "low_stock": false
  }
}
```

---

### 5. Update Product
**Endpoint**: `PUT /api/vendor/products/{product_id}`

**Purpose**: Update product price or stock quantity

**Headers**: `Authorization: Bearer <vendor_token>`

**Request Body**:
```json
{
  "price": 4.49,
  "stock_quantity": 75
}
```

**Response** (200 OK):
```json
{
  "message": "Product updated successfully",
  "updated_fields": ["price", "stock_quantity"],
  "product": {
    "id": 1,
    "name": "Organic Apples",
    "price": 4.49,
    "stock_quantity": 75,
    "updated_at": "2024-01-01T10:30:00Z"
  }
}
```

**Security**: Vendors can only update their own products (checked via `vendor_id`).

---

### 6. View My Orders
**Endpoint**: `GET /api/vendor/orders`

**Purpose**: Get orders for vendor's products

**Headers**: `Authorization: Bearer <vendor_token>`

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `status`: Filter by order status
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)

**Response** (200 OK):
```json
{
  "orders": [
    {
      "id": 1,
      "user_id": 3,
      "product_id": 1,
      "quantity": 2,
      "status": "delivered",
      "order_date": "2024-01-01T10:00:00Z",
      "order_total": 7.98,
      "product": {
        "id": 1,
        "name": "Organic Apples",
        "price": 3.99
      },
      "user": {
        "id": 3,
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "total_orders": 45,
    "has_next": true,
    "has_prev": false
  },
  "statistics": {
    "total_orders": 45,
    "status_summary": {
      "pending": {"count": 5, "revenue": 125.50},
      "delivered": {"count": 35, "revenue": 1125.25}
    },
    "page_revenue": 350.75
  }
}
```

**Logic**: Shows orders for all products where `product.vendor_id` matches the authenticated vendor.

## 👑 Admin Panel APIs

**All admin APIs require admin role and JWT authentication**

### 1. Admin Login
**Endpoint**: `POST /api/admin/login`

**Purpose**: Authenticate admin user and get access token

**Request Body**:
```json
{
  "email": "admin@grocenow.com",
  "password": "adminpassword123"
}
```

**Response** (200 OK):
```json
{
  "message": "Admin login successful",
  "user": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@grocenow.com",
    "role": "admin"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "role": "admin"
}
```

**Note**: Only users with `role: "admin"` can login via this endpoint

---

### 2. Admin Dashboard
**Endpoint**: `GET /api/admin/dashboard`

**Purpose**: Get overview statistics for admin panel

**Headers**: `Authorization: Bearer <admin_token>`

**Response** (200 OK):
```json
{
  "summary": {
    "total_users": 150,
    "total_products": 75,
    "total_orders": 320,
    "total_categories": 12
  },
  "order_status_summary": {
    "pending": 45,
    "confirmed": 120,
    "shipped": 89,
    "delivered": 66
  },
  "recent_orders": [...],
  "low_stock_alerts": [...]
}
```

---

### 3. View All Users
**Endpoint**: `GET /api/admin/users`

**Purpose**: Get paginated list of all users with filtering

**Headers**: `Authorization: Bearer <admin_token>`

**Query Parameters**:
- `role`: Filter by role (admin/vendor/user)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Response** (200 OK):
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "user",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 8,
    "total_users": 150,
    "has_next": true,
    "has_prev": false
  },
  "role_summary": {
    "admin": 3,
    "vendor": 12,
    "user": 135
  }
}
```

---

### 4. View All Products
**Endpoint**: `GET /api/admin/products`

**Purpose**: Get paginated list of all products with vendor info

**Headers**: `Authorization: Bearer <admin_token>`

**Query Parameters**:
- `category_id`: Filter by category
- `vendor_id`: Filter by vendor
- `low_stock`: Show only low stock items (true/false)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Response** (200 OK):
```json
{
  "products": [
    {
      "id": 1,
      "name": "Organic Apples",
      "price": 3.99,
      "stock_quantity": 100,
      "category_name": "Fruits",
      "vendor": {
        "id": 2,
        "name": "Fresh Foods Vendor",
        "email": "vendor@grocenow.com"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 4,
    "total_products": 75,
    "has_next": true,
    "has_prev": false
  },
  "statistics": {
    "total_products": 75,
    "low_stock_count": 8,
    "out_of_stock_count": 2
  }
}
```

---

### 5. View All Orders
**Endpoint**: `GET /api/admin/orders`

**Purpose**: Get paginated list of all orders with filtering

**Headers**: `Authorization: Bearer <admin_token>`

**Query Parameters**:
- `status`: Filter by order status
- `user_id`: Filter by customer
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Response** (200 OK):
```json
{
  "orders": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": 1,
      "quantity": 2,
      "status": "delivered",
      "order_date": "2024-01-01T10:00:00Z",
      "order_total": 7.98,
      "product": {
        "id": 1,
        "name": "Organic Apples",
        "price": 3.99
      },
      "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 16,
    "total_orders": 320,
    "has_next": true,
    "has_prev": false
  },
  "statistics": {
    "total_orders": 320,
    "status_summary": {
      "pending": {"count": 45, "revenue": 1250.50},
      "confirmed": {"count": 120, "revenue": 8750.25}
    },
    "page_revenue": 450.75
  }
}
```

---

### 6. User Details
**Endpoint**: `GET /api/admin/users/{user_id}`

**Purpose**: Get detailed information about a specific user

**Headers**: `Authorization: Bearer <admin_token>`

**Response** (200 OK):
```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user"
  },
  "statistics": {
    "total_orders": 12,
    "total_spent": 245.67,
    "cart_items_count": 3
  },
  "recent_orders": [...],
  "cart_items": [...]
}
```

---

### 7. Analytics Data
**Endpoint**: `GET /api/admin/analytics`

**Purpose**: Get analytics and insights for admin dashboard

**Headers**: `Authorization: Bearer <admin_token>`

**Response** (200 OK):
```json
{
  "revenue_trends": [
    {
      "date": "2024-01-15",
      "revenue": 1250.50,
      "orders_count": 15
    }
  ],
  "top_products": [
    {
      "id": 1,
      "name": "Organic Apples",
      "total_sold": 150,
      "total_revenue": 598.50
    }
  ],
  "top_customers": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "total_spent": 245.67,
      "orders_count": 12
    }
  ]
}
```

## 🛒 User Functionality APIs

### 1. Fetch Products
**Endpoint**: `GET /api/user/products`

**Purpose**: Get all products or filter by category

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `category_id` (optional): Filter by category

**Response** (200 OK):
```json
{
  "products": [
    {
      "id": 1,
      "name": "Organic Apples",
      "description": "Fresh red apples",
      "price": 3.99,
      "stock_quantity": 100,
      "category_id": 1,
      "category_name": "Fruits"
    }
  ],
  "count": 1,
  "category_filter": null
}
```

---

### 2. Add to Cart
**Endpoint**: `POST /api/user/cart`

**Purpose**: Add product to shopping cart

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "product_id": 1,
  "quantity": 2
}
```

**Response** (201 Created):
```json
{
  "message": "Product added to cart",
  "cart_item": {
    "id": 1,
    "user_id": 1,
    "product_id": 1,
    "quantity": 2,
    "added_at": "2024-01-01T10:00:00Z",
    "product": {
      "id": 1,
      "name": "Organic Apples",
      "price": 3.99
    }
  }
}
```

**Validation**:
- Product must exist
- Sufficient stock must be available
- Quantity must be ≥ 1

---

### 3. View Cart
**Endpoint**: `GET /api/user/cart`

**Purpose**: Get all items in user's cart

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "cart_items": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": 1,
      "quantity": 2,
      "added_at": "2024-01-01T10:00:00Z",
      "product": {
        "id": 1,
        "name": "Organic Apples",
        "price": 3.99
      },
      "item_total": 7.98
    }
  ],
  "total_items": 1,
  "total_amount": 7.98
}
```

---

### 4. Update Cart Item
**Endpoint**: `PUT /api/user/cart/{cart_item_id}`

**Purpose**: Update quantity of cart item

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "quantity": 3
}
```

**Response** (200 OK):
```json
{
  "message": "Cart item updated",
  "cart_item": {
    "id": 1,
    "quantity": 3,
    "item_total": 11.97
  }
}
```

---

### 5. Remove from Cart
**Endpoint**: `DELETE /api/user/cart/{cart_item_id}`

**Purpose**: Remove item from cart

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "message": "Item removed from cart"
}
```

---

### 6. Place Order
**Endpoint**: `POST /api/user/orders`

**Purpose**: Convert cart items to orders

**Headers**: `Authorization: Bearer <token>`

**Request Body** (optional):
```json
{
  "cart_item_ids": [1, 2]  // Order specific cart items only
}
```

**Response** (201 Created):
```json
{
  "message": "Order placed successfully",
  "orders": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": 1,
      "quantity": 2,
      "status": "pending",
      "order_date": "2024-01-01T10:00:00Z",
      "product": {
        "id": 1,
        "name": "Organic Apples",
        "price": 3.99
      }
    }
  ],
  "total_orders": 1,
  "total_amount": 7.98
}
```

**Process**:
1. Validates stock availability
2. Creates order records
3. Reduces product stock
4. Removes items from cart

---

### 7. Get Order History
**Endpoint**: `GET /api/user/orders`

**Purpose**: Get user's order history

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `status` (optional): Filter by order status

**Response** (200 OK):
```json
{
  "orders": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": 1,
      "quantity": 2,
      "status": "pending",
      "order_date": "2024-01-01T10:00:00Z",
      "order_total": 7.98,
      "product": {
        "id": 1,
        "name": "Organic Apples",
        "price": 3.99
      }
    }
  ],
  "total_orders": 1,
  "total_amount": 7.98
}
```

---

### 8. Get Order Details
**Endpoint**: `GET /api/user/orders/{order_id}`

**Purpose**: Get specific order details

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "order": {
    "id": 1,
    "user_id": 1,
    "product_id": 1,
    "quantity": 2,
    "status": "pending",
    "order_date": "2024-01-01T10:00:00Z",
    "order_total": 7.98,
    "product": {
      "id": 1,
      "name": "Organic Apples",
      "price": 3.99
    },
    "user": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

### 9. Clear Entire Cart
**Endpoint**: `DELETE /api/user/cart/clear`

**Purpose**: Remove all items from cart at once

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "message": "Cart cleared successfully",
  "items_removed": 3
}
```

### 10. Add Multiple Items to Cart
**Endpoint**: `POST /api/user/cart/bulk`

**Purpose**: Add multiple products to cart in one request

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 3, "quantity": 1},
    {"product_id": 5, "quantity": 3}
  ]
}
```

**Response** (200 OK):
```json
{
  "message": "Bulk cart update completed",
  "added_items": [
    {"product_id": 3, "quantity": 1}
  ],
  "updated_items": [
    {"product_id": 1, "old_quantity": 1, "new_quantity": 3}
  ],
  "failed_items": [
    {"product_id": 5, "error": "Insufficient stock. Available: 2"}
  ],
  "summary": {
    "added": 1,
    "updated": 1,
    "failed": 1
  }
}
```

### 11. Get Cart Summary
**Endpoint**: `GET /api/user/cart/summary`

**Purpose**: Quick cart summary without full details

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "total_unique_products": 3,
  "total_quantity": 8,
  "total_amount": 45.67,
  "has_items": true
}
```

### 12. Cancel Order
**Endpoint**: `PUT /api/user/orders/{order_id}/cancel`

**Purpose**: Cancel a pending order and restore stock

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "message": "Order cancelled successfully",
  "order": {
    "id": 1,
    "status": "cancelled",
    "order_total": 7.98
  },
  "stock_restored": 2
}
```

**Note**: Only pending orders can be cancelled. Stock is automatically restored.

### 13. Reorder from Previous Order
**Endpoint**: `POST /api/user/orders/{order_id}/reorder`

**Purpose**: Add items from a previous order back to cart

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "message": "Added 2 Organic Apples to cart",
  "action": "added",
  "product": {
    "id": 1,
    "name": "Organic Apples",
    "price": 3.99
  },
  "quantity_added": 2,
  "cart_item": {
    "id": 456,
    "product_id": 1,
    "quantity": 2
  }
}
```

## 🔧 Admin/Product Management APIs

These use the existing `/api/*` endpoints (not requiring authentication for basic operations).

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Products
- `GET /api/products` - List all products
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product details
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

## ❌ Error Handling

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate data)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "error": "Error message description"
}
```

### Common Errors
- **Authentication**: "Token is missing", "Token is invalid or expired"
- **Validation**: "Email already registered", "Password must be at least 6 characters"
- **Business Logic**: "Insufficient stock", "Product not found"
- **Permissions**: "Admin access required", "Vendor access required"

## 📊 Data Models

### User
```json
{
  "id": "integer",
  "name": "string",
  "email": "string (unique)",
  "role": "enum: admin/vendor/user",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Product
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "price": "decimal",
  "stock_quantity": "integer",
  "category_id": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Cart
```json
{
  "id": "integer",
  "user_id": "integer",
  "product_id": "integer",
  "quantity": "integer",
  "added_at": "datetime"
}
```

### Order
```json
{
  "id": "integer",
  "user_id": "integer",
  "product_id": "integer",
  "quantity": "integer",
  "status": "enum: pending/confirmed/shipped/delivered/cancelled",
  "order_date": "datetime"
}
```

## 🧪 Testing

Run the test script to verify all APIs:
```bash
python test_apis.py
```

This will test the complete user flow: Register → Login → Browse → Cart → Order.
