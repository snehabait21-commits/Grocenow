#!/usr/bin/env python3
"""
Setup/Verify Vendor User
Creates or updates vendor user with correct password hash.
Run this if vendor login fails with "invalid credentials".
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash

# Use pbkdf2:sha256 method for compatibility with Werkzeug 2.3+
def generate_hash(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def setup_vendor_user():
    """Create or update vendor user with correct password"""
    app = create_app()
    
    with app.app_context():
        # Test database connection
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Ensure MySQL is running")
            print("2. Check .env file has correct DB credentials")
            print("3. Verify database 'groce_now_db' exists")
            return 1
        email = 'vendor@grocenow.com'
        password = 'vendorpassword123'
        name = 'Fresh Foods Vendor'
        
        print("\n" + "="*60)
        print("SETTING UP VENDOR USER")
        print("="*60 + "\n")
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            print(f"✅ User found: {email}")
            print(f"   ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Role: {user.role}")
            
            # Test password
            try:
                password_ok = user.check_password(password)
            except Exception as e:
                print(f"⚠️  Error checking password (old hash format?): {e}")
                print(f"   Regenerating password hash...")
                password_ok = False
            
            if password_ok:
                print(f"✅ Password is correct")
            else:
                print(f"⚠️  Password doesn't match or hash format incompatible. Updating password hash...")
                user.set_password(password)  # This will use pbkdf2:sha256
                db.session.commit()
                print(f"✅ Password hash updated to pbkdf2:sha256 format")
            
            # Check role
            if user.role not in ('vendor', 'admin'):
                print(f"⚠️  Role is '{user.role}' but needs 'vendor' or 'admin'. Updating...")
                user.role = 'vendor'
                db.session.commit()
                print(f"✅ Role updated to 'vendor'")
            
        else:
            print(f"❌ User not found. Creating new vendor user...")
            user = User(
                name=name,
                email=email,
                role='vendor'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"✅ Vendor user created successfully")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Role: vendor")
        
        # Verify final state
        user = User.query.filter_by(email=email).first()
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        print(f"Email: {user.email}")
        print(f"Name: {user.name}")
        print(f"Role: {user.role}")
        print(f"Password check: {'✅ PASS' if user.check_password(password) else '❌ FAIL'}")
        print("="*60 + "\n")
        
        if user.check_password(password) and user.role in ('vendor', 'admin'):
            print("✅ Vendor user is ready!")
            print(f"\nLogin credentials:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"\nTry logging in at: http://localhost:5000/vendor/login")
        else:
            print("❌ Setup incomplete. Check errors above.")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(setup_vendor_user())
