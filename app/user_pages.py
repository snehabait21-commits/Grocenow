from flask import Blueprint, render_template, abort, session, redirect, url_for, flash

user_pages_bp = Blueprint("user_pages", __name__)

def _get_customer_user():
    user = session.get('customer_user')
    return user if isinstance(user, dict) else None

@user_pages_bp.route("/")
def index():
    return render_template("index.html", customer_user=_get_customer_user())

@user_pages_bp.route("/<page>")
def load_page(page):
    try:
        return render_template(f"{page}.html", customer_user=_get_customer_user())
    except:
        abort(404)


@user_pages_bp.route("/logout")
def logout():
    # Clear customer session and show success message on home
    session.pop('customer_user', None)
    flash('You logged out successfully.', 'success')
    return redirect(url_for('user_pages.index', logout='1'))