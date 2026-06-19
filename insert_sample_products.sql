-- ============================================
-- Sample Grocery Products Insertion
-- Adds 10 diverse products across 3 categories
-- ============================================

USE groce_now_db;

-- ============================================
-- VERIFY VENDOR EXISTS (should be ID 2)
-- ============================================
SELECT id, name, email, role FROM users WHERE role = 'vendor';

-- ============================================
-- INSERT SAMPLE CATEGORIES (if not exists)
-- Note: Categories are stored as strings in products table
-- ============================================

-- ============================================
-- INSERT SAMPLE PRODUCTS
-- Vendor ID 2 = Fresh Foods Vendor
-- ============================================

-- FRUITS CATEGORY (4 products)
INSERT INTO products (name, category, price, quantity, vendor_id, description) VALUES
('Organic Bananas', 'Fruits', 1.99, 150, 2, 'Fresh organic bananas, perfect for smoothies'),
('Red Apples', 'Fruits', 2.49, 120, 2, 'Crisp red apples, great for snacking'),
('Oranges', 'Fruits', 3.99, 90, 2, 'Juicy navel oranges, rich in vitamin C'),
('Strawberries', 'Fruits', 4.99, 60, 2, 'Fresh strawberries, perfect for desserts')

ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    quantity = VALUES(quantity),
    description = VALUES(description);

-- GROCERIES CATEGORY (4 products)
INSERT INTO products (name, category, price, quantity, vendor_id, description) VALUES
('Whole Wheat Bread', 'Groceries', 3.49, 80, 2, 'Fresh baked whole wheat bread'),
('Organic Milk', 'Groceries', 4.99, 45, 2, 'Organic whole milk, 1 gallon'),
('Brown Rice', 'Groceries', 5.99, 100, 2, 'Premium brown rice, 2kg bag'),
('Olive Oil', 'Groceries', 8.99, 30, 2, 'Extra virgin olive oil, 500ml')

ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    quantity = VALUES(quantity),
    description = VALUES(description);

-- HOUSEHOLD CATEGORY (4 products)
INSERT INTO products (name, category, price, quantity, vendor_id, description) VALUES
('Dish Soap', 'Household', 2.99, 200, 2, 'Lemon scented dish soap, 500ml'),
('Laundry Detergent', 'Household', 7.99, 75, 2, 'Concentrated laundry detergent, 2L'),
('Paper Towels', 'Household', 4.49, 120, 2, 'Absorbent paper towels, 6 rolls'),
('Toilet Paper', 'Household', 6.99, 90, 2, 'Soft toilet paper, 12 rolls')

ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    quantity = VALUES(quantity),
    description = VALUES(description);

-- ============================================
-- VERIFY INSERTION
-- ============================================

-- Count products by category
SELECT
    category,
    COUNT(*) as product_count,
    SUM(quantity) as total_stock,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products
GROUP BY category
ORDER BY category;

-- Show all products with vendor info
SELECT
    p.id,
    p.name,
    p.category,
    CONCAT('$', FORMAT(p.price, 2)) as price,
    p.quantity as stock,
    u.name as vendor_name,
    p.created_at
FROM products p
JOIN users u ON p.vendor_id = u.id
ORDER BY p.category, p.name;

-- Total products count
SELECT
    COUNT(*) as total_products,
    SUM(quantity) as total_stock_value,
    CONCAT('$', FORMAT(SUM(price * quantity), 2)) as inventory_value
FROM products;

-- ============================================
-- OPTIONAL: ADD MORE PRODUCTS
-- ============================================

-- Example of adding a single product
-- INSERT INTO products (name, category, price, quantity, vendor_id, description)
-- VALUES ('New Product Name', 'Category', 9.99, 50, 2, 'Product description');

-- Example of updating existing product
-- UPDATE products SET price = 3.99, quantity = 75 WHERE name = 'Organic Bananas';

-- Example of deleting a product (be careful!)
-- DELETE FROM products WHERE name = 'Product Name' AND vendor_id = 2;


