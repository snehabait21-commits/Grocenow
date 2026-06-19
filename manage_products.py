#!/usr/bin/env python3
"""
Product Management Script
Add, update, delete, and query products in the database
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app import create_app
from app.models import Product, User, db

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"📦 {title}")
    print(f"{'='*60}")

def print_product(product):
    """Print product details"""
    print(f"ID: {product.id}")
    print(f"Name: {product.name}")
    print(f"Category: {product.category}")
    print(f"Price: ${product.price}")
    print(f"Stock: {product.quantity}")
    print(f"Vendor ID: {product.vendor_id}")
    print(f"Created: {product.created_at}")
    print(f"Updated: {product.updated_at}")
    print("-" * 40)

def add_sample_products():
    """Add the 10 sample products to database"""
    print_header("Adding Sample Products")

    # Get vendor (assuming Fresh Foods Vendor exists)
    vendor = User.query.filter_by(email='vendor@grocenow.com').first()
    if not vendor:
        print("❌ Vendor not found. Please run create_vendor_user.sql first")
        return False

    print(f"✅ Using vendor: {vendor.name} (ID: {vendor.id})")

    # Sample products data
    products_data = [
        # Fruits
        {"name": "Organic Bananas", "category": "Fruits", "price": 1.99, "quantity": 150,
         "description": "Fresh organic bananas, perfect for smoothies"},
        {"name": "Red Apples", "category": "Fruits", "price": 2.49, "quantity": 120,
         "description": "Crisp red apples, great for snacking"},
        {"name": "Oranges", "category": "Fruits", "price": 3.99, "quantity": 90,
         "description": "Juicy navel oranges, rich in vitamin C"},
        {"name": "Strawberries", "category": "Fruits", "price": 4.99, "quantity": 60,
         "description": "Fresh strawberries, perfect for desserts"},

        # Groceries
        {"name": "Whole Wheat Bread", "category": "Groceries", "price": 3.49, "quantity": 80,
         "description": "Fresh baked whole wheat bread"},
        {"name": "Organic Milk", "category": "Groceries", "price": 4.99, "quantity": 45,
         "description": "Organic whole milk, 1 gallon"},
        {"name": "Brown Rice", "category": "Groceries", "price": 5.99, "quantity": 100,
         "description": "Premium brown rice, 2kg bag"},
        {"name": "Olive Oil", "category": "Groceries", "price": 8.99, "quantity": 30,
         "description": "Extra virgin olive oil, 500ml"},

        # Household
        {"name": "Dish Soap", "category": "Household", "price": 2.99, "quantity": 200,
         "description": "Lemon scented dish soap, 500ml"},
        {"name": "Laundry Detergent", "category": "Household", "price": 7.99, "quantity": 75,
         "description": "Concentrated laundry detergent, 2L"},
        {"name": "Paper Towels", "category": "Household", "price": 4.49, "quantity": 120,
         "description": "Absorbent paper towels, 6 rolls"},
        {"name": "Toilet Paper", "category": "Household", "price": 6.99, "quantity": 90,
         "description": "Soft toilet paper, 12 rolls"}
    ]

    added_count = 0
    updated_count = 0

    for product_data in products_data:
        try:
            # Check if product already exists
            existing_product = Product.query.filter_by(
                name=product_data['name'],
                vendor_id=vendor.id
            ).first()

            if existing_product:
                # Update existing product
                existing_product.price = product_data['price']
                existing_product.quantity = product_data['quantity']
                existing_product.description = product_data.get('description', '')
                updated_count += 1
                print(f"✓ Updated: {product_data['name']}")
            else:
                # Create new product
                new_product = Product(
                    name=product_data['name'],
                    category=product_data['category'],
                    price=product_data['price'],
                    quantity=product_data['quantity'],
                    vendor_id=vendor.id,
                    description=product_data.get('description', '')
                )
                db.session.add(new_product)
                added_count += 1
                print(f"✓ Added: {product_data['name']}")

        except Exception as e:
            print(f"❌ Error with {product_data['name']}: {str(e)}")
            continue

    try:
        db.session.commit()
        print(f"\n✅ Success! Added: {added_count}, Updated: {updated_count}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database error: {str(e)}")
        return False

def list_all_products():
    """List all products with vendor information"""
    print_header("All Products in Database")

    try:
        products = Product.query.join(User).order_by(Product.category, Product.name).all()

        if not products:
            print("❌ No products found in database")
            return

        current_category = None
        for product in products:
            if current_category != product.category:
                current_category = product.category
                print(f"\n📂 {current_category}")
                print("-" * 50)

            vendor_name = product.user.name if hasattr(product, 'user') and product.user else "Unknown"
            print(f"• {product.name}")
            print(f"  Price: ${product.price}, Stock: {product.quantity}")
            print(f"  Vendor: {vendor_name}")

        print(f"\n📊 Total: {len(products)} products")

    except Exception as e:
        print(f"❌ Error listing products: {str(e)}")

def add_single_product():
    """Add a single product interactively"""
    print_header("Add Single Product")

    try:
        # Get vendor
        vendor = User.query.filter_by(email='vendor@grocenow.com').first()
        if not vendor:
            print("❌ Vendor not found. Please run create_vendor_user.sql first")
            return

        print(f"Using vendor: {vendor.name}")

        # Get product details
        name = input("Product name: ").strip()
        if not name:
            print("❌ Name is required")
            return

        category = input("Category (Fruits/Groceries/Household): ").strip()
        if not category:
            print("❌ Category is required")
            return

        try:
            price = float(input("Price: $").strip())
            if price <= 0:
                print("❌ Price must be greater than 0")
                return
        except ValueError:
            print("❌ Invalid price")
            return

        try:
            quantity = int(input("Stock quantity: ").strip())
            if quantity < 0:
                print("❌ Quantity cannot be negative")
                return
        except ValueError:
            print("❌ Invalid quantity")
            return

        description = input("Description (optional): ").strip()

        # Check if product exists
        existing_product = Product.query.filter_by(
            name=name,
            vendor_id=vendor.id
        ).first()

        if existing_product:
            # Update existing
            existing_product.category = category
            existing_product.price = price
            existing_product.quantity = quantity
            existing_product.description = description
            print(f"✓ Updated existing product: {name}")
        else:
            # Create new
            new_product = Product(
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                vendor_id=vendor.id,
                description=description
            )
            db.session.add(new_product)
            print(f"✓ Added new product: {name}")

        db.session.commit()
        print("✅ Product saved successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")

def update_product_price():
    """Update product price"""
    print_header("Update Product Price")

    try:
        # List products first
        products = Product.query.join(User).order_by(Product.name).all()

        if not products:
            print("❌ No products found")
            return

        print("Available products:")
        for i, product in enumerate(products, 1):
            vendor_name = product.user.name if hasattr(product, 'user') and product.user else "Unknown"
            print(f"{i}. {product.name} (${product.price}) - {product.category} by {vendor_name}")

        try:
            choice = int(input("\nSelect product number: ").strip())
            if choice < 1 or choice > len(products):
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid input")
            return

        selected_product = products[choice - 1]

        try:
            new_price = float(input(f"Current price: ${selected_product.price}\nNew price: $").strip())
            if new_price <= 0:
                print("❌ Price must be greater than 0")
                return
        except ValueError:
            print("❌ Invalid price")
            return

        selected_product.price = new_price
        db.session.commit()

        print(f"✅ Updated {selected_product.name} price to ${new_price}")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")

def delete_product():
    """Delete a product"""
    print_header("Delete Product")
    print("⚠️  WARNING: This will permanently delete the product!")

    try:
        # List products
        products = Product.query.join(User).order_by(Product.name).all()

        if not products:
            print("❌ No products found")
            return

        print("Available products:")
        for i, product in enumerate(products, 1):
            vendor_name = product.user.name if hasattr(product, 'user') and product.user else "Unknown"
            print(f"{i}. {product.name} (${product.price}) - {product.category} by {vendor_name}")

        try:
            choice = int(input("\nSelect product number to delete: ").strip())
            if choice < 1 or choice > len(products):
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid input")
            return

        selected_product = products[choice - 1]

        # Confirm deletion
        confirm = input(f"Are you sure you want to delete '{selected_product.name}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Deletion cancelled")
            return

        db.session.delete(selected_product)
        db.session.commit()

        print(f"✅ Deleted product: {selected_product.name}")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")

def show_statistics():
    """Show product statistics"""
    print_header("Product Statistics")

    try:
        # Total products
        total_products = Product.query.count()
        print(f"📊 Total Products: {total_products}")

        # Products by category
        from sqlalchemy import func
        category_stats = db.session.query(
            Product.category,
            func.count(Product.id).label('count'),
            func.sum(Product.quantity).label('total_stock'),
            func.avg(Product.price).label('avg_price')
        ).group_by(Product.category).all()

        print("
📂 By Category:"        for category, count, total_stock, avg_price in category_stats:
            print(f"  • {category}: {count} products, {total_stock or 0} total stock, avg ${avg_price:.2f}")

        # Price statistics
        price_stats = db.session.query(
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price'),
            func.avg(Product.price).label('avg_price')
        ).first()

        print("
💰 Price Range:"        print(f"  • Lowest: ${price_stats.min_price}")
        print(f"  • Highest: ${price_stats.max_price}")
        print(f"  • Average: ${price_stats.avg_price:.2f}")

        # Stock alerts
        low_stock = Product.query.filter(Product.quantity < 10).count()
        out_of_stock = Product.query.filter(Product.quantity == 0).count()

        print("
📦 Stock Status:"        print(f"  • Low stock (< 10): {low_stock} products")
        print(f"  • Out of stock (= 0): {out_of_stock} products")

    except Exception as e:
        print(f"❌ Error getting statistics: {str(e)}")

def main():
    """Main menu"""
    app = create_app()

    with app.app_context():
        while True:
            print_header("Product Management System")
            print("1. Add sample products (10 items)")
            print("2. List all products")
            print("3. Add single product")
            print("4. Update product price")
            print("5. Delete product")
            print("6. Show statistics")
            print("7. Exit")

            try:
                choice = input("\nSelect option (1-7): ").strip()

                if choice == '1':
                    add_sample_products()
                elif choice == '2':
                    list_all_products()
                elif choice == '3':
                    add_single_product()
                elif choice == '4':
                    update_product_price()
                elif choice == '5':
                    delete_product()
                elif choice == '6':
                    show_statistics()
                elif choice == '7':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")

            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()


