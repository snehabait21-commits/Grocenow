# GroceNow - Flask Backend API

A simple Flask backend API for a grocery management system built with Python Flask and MySQL.

## Project Structure

```
GroceNow/
├── app/                      # Flask application package
│   ├── __init__.py           # Application factory & blueprint registration
│   ├── config.py             # Database and app configuration
│   ├── models.py             # SQLAlchemy models
│   ├── routes.py             # Public API (products, categories, health)
│   ├── auth.py               # JWT decorators (token_required, admin_required)
│   ├── auth_routes.py        # Customer registration & login
│   ├── user_routes.py        # Cart, orders, addresses
│   ├── admin_routes.py       # Admin API + session-based admin UI
│   ├── vendor_routes.py      # Vendor API
│   ├── vendor_pages.py       # Vendor panel HTML routes
│   ├── user_pages.py         # Customer storefront pages
│   ├── mysql_connection.py   # Direct MySQL helper (demo routes)
│   ├── mysql_routes.py       # MySQL demonstration routes
│   ├── templates/            # Jinja2 HTML (storefront + admin)
│   └── static/               # CSS, JS, images
├── vendor/                   # Vendor panel SPA (login + dashboard)
├── database_schema.sql       # MySQL schema
├── insert_sample_products.sql
├── setup_admin_user.py       # Create/update admin login
├── setup_vendor_user.py      # Create/update vendor login
├── manage_products.py        # Interactive product CLI
├── test_all_apis.py          # API test suite
├── requirements.txt
├── .env.example              # Copy to .env and configure
├── API_DOCUMENTATION.md      # Complete API reference
├── run.py                    # Application entry point
└── README.md
```

## File Explanations

### `run.py`
- **Purpose**: Entry point to start the Flask application
- **What it does**: Creates the app instance and runs it on port 5000 with debug mode enabled
- **Usage**: Run `python run.py` to start the server

### `app/__init__.py`
- **Purpose**: Flask application factory pattern
- **What it does**:
  - Creates and configures the Flask app
  - Initializes database connection
  - Sets up CORS for cross-origin requests
  - Registers API routes
  - Creates database tables automatically

### `app/config.py`
- **Purpose**: Configuration management
- **What it does**:
  - Loads environment variables from .env file
  - Sets up database connection string
  - Configures Flask settings

### `app/models.py`
- **Purpose**: Database models using SQLAlchemy
- **Contains**:
  - `User`: For user authentication
  - `Category`: For organizing products (e.g., Fruits, Vegetables)
  - `Product`: For grocery items with price, stock, and category

### `app/routes.py`
- **Purpose**: API endpoints for the application (using SQLAlchemy ORM)
- **Endpoints**:
  - `GET /api/health`: Check if API is running
  - `GET /api/categories`: Get all categories
  - `POST /api/categories`: Create new category
  - `GET /api/products`: Get all products (optional category filter)
  - `POST /api/products`: Create new product
  - `GET /api/products/<id>`: Get specific product
  - `PUT /api/products/<id>`: Update product
  - `DELETE /api/products/<id>`: Delete product

### `app/mysql_connection.py`
- **Purpose**: Direct MySQL connection using mysql-connector-python
- **Features**:
  - Connection management with error handling
  - Query execution with prepared statements
  - Transaction management (commit/rollback)
  - Comprehensive error handling for different MySQL errors

### `app/mysql_routes.py`
- **Purpose**: Demonstration API routes using direct MySQL queries
- **Endpoints**:
  - `GET /mysql/test`: Test MySQL connection
  - `GET /mysql/users`: Get all users with direct SQL
  - `POST /mysql/users`: Create user with direct SQL
  - `GET /mysql/products/search`: Search products with filters

### `database_schema.sql`
- **Purpose**: Complete MySQL database schema for the grocery system
- **Contains**: Table creation, indexes, and sample data

### `requirements.txt`
- **Purpose**: Lists all Python dependencies
- **Dependencies**:
  - Flask: Web framework
  - Flask-SQLAlchemy: Database ORM (for high-level operations)
  - Flask-CORS: Cross-origin resource sharing
  - PyMySQL: MySQL connector for SQLAlchemy
  - mysql-connector-python: Direct MySQL connector (for raw SQL queries)
  - python-dotenv: Environment variable management

## Setup Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL Database
1. Install MySQL if not already installed
2. Create a database named `groce_now_db`
3. Update database credentials in `.env` file (create one based on `.env.example`)

### 3. Environment Variables
Create a `.env` file in the root directory:
```
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_DEBUG=True
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=groce_now_db
```

### 4. Run the Application
```bash
python run.py
```

The API will be available at `http://localhost:5000`

### 5. Create Test Users & Sample Data
```bash
# Create admin and vendor users (recommended)
python setup_admin_user.py
python setup_vendor_user.py

# Optional: load sample products from SQL
mysql -u root -p groce_now_db < insert_sample_products.sql

# Or use the interactive product manager
python manage_products.py
```

**Default panel logins:**
- Admin: `admin@grocenow.com` / `adminpassword123` → http://localhost:5000/admin/login
- Vendor: `vendor@grocenow.com` / `vendorpassword123` → http://localhost:5000/vendor/login

### 6. Quick API Testing
```bash
# Full API test suite (server must be running)
python test_all_apis.py
```

This tests the complete user flow: Register → Login → Browse → Cart → Order

## API Usage Examples

### SQLAlchemy ORM Endpoints (Recommended for most operations)

#### Get all products
```bash
curl http://localhost:5000/api/products
```

#### Create a category
```bash
curl -X POST http://localhost:5000/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Fruits", "description": "Fresh fruits"}'
```

#### Create a product
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apple",
    "description": "Fresh red apple",
    "price": 2.50,
    "stock_quantity": 100,
    "category_id": 1
  }'
```

### User Authentication APIs

#### Register a new user
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "role": "user"
  }'
```

#### Login user
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### User Functionality APIs (Require Authentication)

#### Fetch products
```bash
curl http://localhost:5000/api/user/products \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Add product to cart
```bash
curl -X POST http://localhost:5000/api/user/cart \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

#### View cart
```bash
curl http://localhost:5000/api/user/cart \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Place order
```bash
curl -X POST http://localhost:5000/api/user/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### View order history
```bash
curl http://localhost:5000/api/user/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Clear entire cart
```bash
curl -X DELETE http://localhost:5000/api/user/cart/clear \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Add multiple items to cart
```bash
curl -X POST http://localhost:5000/api/user/cart/bulk \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'
```

#### Cancel pending order
```bash
curl -X PUT http://localhost:5000/api/user/orders/123/cancel \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Reorder from previous order
```bash
curl -X POST http://localhost:5000/api/user/orders/123/reorder \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Admin Panel APIs (Admin Role Required)

#### Admin login
```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@grocenow.com",
    "password": "adminpassword123"
  }'
```

#### View admin dashboard
```bash
curl http://localhost:5000/api/admin/dashboard \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

#### View all users (admin only)
```bash
curl http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

#### View all products (admin only)
```bash
curl http://localhost:5000/api/admin/products \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

#### View all orders (admin only)
```bash
curl http://localhost:5000/api/admin/orders \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### Vendor Panel APIs (Vendor Role Required)

#### Vendor login
```bash
curl -X POST http://localhost:5000/api/vendor/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendor@grocenow.com",
    "password": "vendorpassword123"
  }'
```

#### View vendor dashboard
```bash
curl http://localhost:5000/api/vendor/dashboard \
  -H "Authorization: Bearer VENDOR_JWT_TOKEN"
```

#### Add new product (vendor only)
```bash
curl -X POST http://localhost:5000/api/vendor/products \
  -H "Authorization: Bearer VENDOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Organic Bananas",
    "category_id": 1,
    "price": 2.99,
    "stock_quantity": 50,
    "description": "Fresh organic bananas"
  }'
```

#### Update product price/quantity (vendor only)
```bash
curl -X PUT http://localhost:5000/api/vendor/products/123 \
  -H "Authorization: Bearer VENDOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 3.49,
    "stock_quantity": 75
  }'
```

#### View vendor's orders
```bash
curl http://localhost:5000/api/vendor/orders \
  -H "Authorization: Bearer VENDOR_JWT_TOKEN"
```

## 🛒 Sample Data Included

The project includes sample data for testing:

### Users
- **Admin**: admin@grocenow.com / adminpassword123
- **Vendor**: vendor@grocenow.com / vendorpassword123
- **Customer**: test@example.com / testpassword123

### Products (12 items across 3 categories)
- **Fruits**: Organic Bananas, Red Apples, Oranges, Strawberries
- **Groceries**: Whole Wheat Bread, Organic Milk, Brown Rice, Olive Oil
- **Household**: Dish Soap, Laundry Detergent, Paper Towels, Toilet Paper

### How to Add More Products
- Run `python manage_products.py` for interactive product management
- Use `insert_sample_products.sql` for bulk sample data
- Vendors can add products from the vendor panel or `POST /api/vendor/products`

## 📋 API Endpoints Explanation

### 1. **User Registration** - `POST /api/auth/register`
**Purpose**: Create a new user account
**Input**: name, email, password (required), role (optional)
**Security**: Password is hashed using Werkzeug
**Returns**: User data + JWT token for immediate login
**Validation**: Email uniqueness, password strength (min 6 chars)

### 2. **User Login** - `POST /api/auth/login`
**Purpose**: Authenticate user and get access token
**Input**: email, password
**Security**: Password verification using secure hashing
**Returns**: User data + JWT token (24-hour expiry)
**Error Handling**: Invalid credentials return 401

### 3. **Fetch Products** - `GET /api/user/products`
**Purpose**: Get all products or filter by category
**Authentication**: Required (JWT token)
**Query Params**: `category_id` (optional)
**Returns**: Product list with category information
**Features**: Includes stock quantity and pricing

### 4. **Add to Cart** - `POST /api/user/cart`
**Purpose**: Add products to shopping cart
**Authentication**: Required
**Input**: product_id (required), quantity (optional, defaults to 1)
**Validation**: Stock availability check, quantity validation
**Features**: Updates existing cart items if product already added

### 5. **View Cart** - `GET /api/user/cart`
**Purpose**: Display user's shopping cart
**Authentication**: Required
**Returns**: Cart items with product details and total amount
**Features**: Calculates total price, shows item subtotals

### 6. **Place Order** - `POST /api/user/orders`
**Purpose**: Convert cart items to orders
**Authentication**: Required
**Input**: cart_item_ids (optional - orders specific items)
**Processing**:
- Validates stock availability
- Creates order records
- Reduces product stock
- Removes items from cart
- Calculates total amount

### 7. **Order History** - `GET /api/user/orders`
**Purpose**: View user's order history
**Authentication**: Required
**Query Params**: `status` (optional filter)
**Returns**: Orders with product details and totals
**Features**: Chronological order (newest first)

## 🔐 Authentication System

### JWT Token Usage
- **Format**: `Authorization: Bearer <token>`
- **Expiry**: 24 hours
- **Payload**: user_id, email, role, expiry time
- **Security**: HMAC-SHA256 signed with SECRET_KEY

### User Roles
- **admin**: Full system access
- **vendor**: Can manage products
- **user**: Standard customer access

### Protected Routes
All `/api/user/*` endpoints require authentication. Use the JWT token from login/registration.

## 🛡️ Security Features

- **Password Hashing**: Werkzeug security for passwords
- **JWT Authentication**: Stateless token-based auth
- **Input Validation**: Email format, password strength
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: JSON responses, input sanitization
- **Role-Based Access Control**: Admin, vendor, and user roles

## 🌐 Cross-Origin Resource Sharing (CORS)

### Why CORS is Needed
CORS allows your frontend (React/Vue/Angular) running on `localhost:3000` to communicate with your Flask backend on `localhost:5000`. Without CORS, browsers block cross-origin requests for security.

### CORS Configuration
Your Flask app is already configured with CORS for development:
- **Allowed Origins**: `localhost:3000`, `localhost:3001`, `127.0.0.1:3000`
- **Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- **Allowed Headers**: `Content-Type`, `Authorization`, `X-Requested-With`
- **Credentials**: Enabled (for JWT authentication)

### Test CORS
With the server running, call any API from the storefront or use browser dev tools. CORS is configured in `app/__init__.py`.

### Production CORS
For production, update the origins in `app/__init__.py`:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"]
    }
})
```

## 🚨 Error Handling & Database Safety

### Error Types & Responses

**HTTP Status Codes:**
- `200` - Success
- `201` - Created (new resource)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (duplicate data)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error (server/database error)

### Common Error Scenarios

**Authentication Errors:**
- **Invalid token**: `401 Unauthorized` - Token expired or malformed
- **Missing token**: `401 Unauthorized` - No Authorization header
- **Wrong credentials**: `401 Unauthorized` - Invalid email/password

**Permission Errors:**
- **Insufficient role**: `403 Forbidden` - User lacks required role
- **Access denied**: `403 Forbidden` - Trying to modify others' data

**Validation Errors:**
- **Missing fields**: `400 Bad Request` - Required data not provided
- **Invalid data**: `400 Bad Request` - Wrong data format/type
- **Duplicate email**: `409 Conflict` - Email already registered

**Business Logic Errors:**
- **Product not found**: `404 Not Found` - Invalid product ID
- **Insufficient stock**: `400 Bad Request` - Not enough inventory
- **Empty cart**: `400 Bad Request` - No items to order

**Database Errors:**
- **Connection failed**: `500 Internal Server Error` - DB unreachable
- **Transaction failed**: `500 Internal Server Error` - Rollback performed
- **Constraint violation**: `400/500` - Data integrity issues

### Error Response Format

```json
{
  "error": "Error Type",
  "message": "Human-readable description"
}
```

### Database Safety Features

**Transaction Management:**
- Automatic rollback on errors
- Prevents partial updates
- Maintains data consistency

**Connection Handling:**
- Connection pooling
- Timeout management
- Graceful degradation

**Input Validation:**
- SQL injection prevention
- Data type checking
- Range validation

**Logging:**
- Error details logged for debugging
- User-friendly messages for clients
- Security-sensitive data not logged

## 👑 Role-Based Access Control (RBAC)

### How Role-Based Access Works

**1. User Roles:**
- **admin**: Full system access (manage users, products, orders, analytics)
- **vendor**: Product management (add/update their products, view their orders)
- **user**: Standard customer access (browse, cart, orders)

**2. Access Control Decorators:**
```python
@token_required      # Requires any authenticated user
@admin_required      # Requires admin role only
@vendor_required     # Requires admin or vendor role
```

**3. JWT Token Payload:**
```json
{
  "user_id": 1,
  "email": "admin@grocenow.com",
  "role": "admin",
  "exp": 1640995200
}
```

**4. Access Levels:**
- **Public**: Health check, registration, login
- **User**: Product browsing, cart, orders (any authenticated user)
- **Vendor**: Product management (admin + vendor roles)
- **Admin**: User management, system analytics (admin only)

**5. Permission Enforcement:**
- Server-side validation on every request
- JWT token verification + role checking
- HTTP 403 Forbidden for insufficient permissions
- Clean error messages for unauthorized access

### Example Access Matrix:

| Feature | admin | vendor | user |
|---------|-------|--------|------|
| Browse products | ✅ | ✅ | ✅ |
| Add to cart | ❌ | ❌ | ✅ |
| Place orders | ❌ | ❌ | ✅ |
| **Add products** | ❌ | ✅ | ❌ |
| **Update my products** | ❌ | ✅ | ❌ |
| **View my orders** | ❌ | ✅ | ❌ |
| View all users | ✅ | ❌ | ❌ |
| View all products | ✅ | ❌ | ❌ |
| View all orders | ✅ | ❌ | ❌ |
| System analytics | ✅ | ❌ | ❌ |
| **Vendor analytics** | ✅ | ✅ | ❌ |

### Direct MySQL Connection Endpoints (For learning raw SQL)

#### Test MySQL connection
```bash
curl http://localhost:5000/mysql/test
```

#### Get all users with direct SQL
```bash
curl http://localhost:5000/mysql/users
```

#### Create a user with direct SQL
```bash
curl -X POST http://localhost:5000/mysql/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "hashed_password_here",
    "role": "user"
  }'
```

#### Search products with filters
```bash
curl "http://localhost:5000/mysql/products/search?category=Fruits&min_price=1&max_price=5"
```

## Database Schema

The application supports two database connection methods:

### SQLAlchemy ORM (Automatic)
Creates three main tables automatically:
- `users`: User authentication data
- `categories`: Product categories
- `products`: Grocery items linked to categories

### Direct MySQL Schema (Manual)
Complete schema in `database_schema.sql` with 4 tables:
- `users`: Users (admin/vendor/customer)
- `products`: Grocery products
- `cart`: Shopping cart items
- `orders`: Order history

## MySQL Connection

Direct MySQL demo routes are available under `/mysql/`. Configure credentials in `.env` (see `.env.example`).

### Quick Connection Test
```bash
# Test MySQL connection
curl http://localhost:5000/mysql/test

# Should return: {"status": "success", "mysql_version": "8.x.x"}
```

## Next Steps

This is a basic foundation. You can extend it by:
- Adding user authentication and authorization
- Implementing shopping cart functionality
- Adding order management
- Creating more complex product features (images, reviews, etc.)
- Adding data validation and error handling
- Implementing pagination for large datasets

## Notes for Beginners

- **Two database approaches**: SQLAlchemy ORM (easy) and direct MySQL (educational)
- CORS is enabled so you can connect a frontend later
- Database tables are created automatically when you run the app
- All API responses are in JSON format
- **MySQL Connection Guide**: Learn raw SQL queries with comprehensive error handling
- Error handling covers connection issues, query errors, and data validation
- Great for learning both ORM abstraction and direct database programming
