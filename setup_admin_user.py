#!/usr/bin/env python3
"""
Setup/Verify Admin User
Creates or updates admin user with correct password hash.
Run this if admin login fails with "invalid credentials".
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def setup_admin_user():
    """Create or update admin user with correct password"""
    app = create_app()

    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Ensure MySQL is running")
            print("2. Check .env file has correct DB credentials")
            return 1

        email = 'admin@grocenow.com'
        password = 'adminpassword123'
        name = 'GroceNow Admin'

        print("\n" + "="*60)
        print("SETTING UP ADMIN USER")
        print("="*60 + "\n")

        user = User.query.filter_by(email=email).first()

        if user:
            print(f"✅ User found: {email}")
            print(f"   ID: {user.id}, Name: {user.name}, Role: {user.role}")

            try:
                password_ok = user.check_password(password)
            except Exception:
                password_ok = False

            if not password_ok:
                print("⚠️  Updating password hash...")
                user.set_password(password)
                db.session.commit()
                print("✅ Password hash updated")

            if user.role != 'admin':
                print(f"⚠️  Role is '{user.role}'. Updating to 'admin'...")
                user.role = 'admin'
                db.session.commit()
                print("✅ Role updated to 'admin'")
        else:
            print("Creating new admin user...")
            user = User(name=name, email=email, role='admin')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print("✅ Admin user created")

        user = User.query.filter_by(email=email).first()
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        print(f"Email: {user.email}\nName: {user.name}\nRole: {user.role}")
        print(f"Password check: {'✅ PASS' if user.check_password(password) else '❌ FAIL'}")
        print("="*60 + "\n")

        if user.check_password(password) and user.role == 'admin':
            print("✅ Admin user is ready!")
            print(f"\nLogin: {email}\nPassword: {password}")
            print("\nAdmin panel: http://localhost:5000/admin/login")
        else:
            print("❌ Setup incomplete.")
            return 1

    return 0

if __name__ == '__main__':
    sys.exit(setup_admin_user())
