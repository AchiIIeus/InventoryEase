from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///inventoryease.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        from models import User, Product  # noqa
        db.create_all()

    # ---- helpers ----
    def login_required(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper

    # ---- auth ----
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        from models import User
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not username or not password:
                flash('Username and password are required.', 'error')
                return render_template('register.html')
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'error')
                return render_template('register.html')
            u = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(u)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        from models import User
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('dashboard'))
            flash('Invalid credentials.', 'error')
        return render_template('login.html')

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # ---- core ----
    @app.route('/')
    def index():
        return redirect(url_for('dashboard') if 'user_id' in session else 'login')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        from models import Product
        count = Product.query.count()
        total_value = db.session.query(db.func.coalesce(db.func.sum(Product.quantity * Product.price), 0)).scalar() or 0
        return render_template('dashboard.html', count=count, total_value=total_value)

    # ---- inventory CRUD ----
    @app.route('/inventory')
    @login_required
    def inventory_list():
        from models import Product
        q = request.args.get('q', '').strip()
        items = (Product.query.filter(Product.name.ilike(f'%{q}%')) if q else Product.query).order_by(Product.created_at.desc()).all()
        return render_template('inventory_list.html', items=items, q=q)

    @app.route('/inventory/add', methods=['GET', 'POST'])
    @login_required
    def inventory_add():
        from models import Product
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '').strip()
            quantity = int(request.form.get('quantity', 0) or 0)
            price = float(request.form.get('price', 0) or 0)
            if not name:
                flash('Name is required.', 'error')
                return render_template('product_form.html', item=None)
            db.session.add(Product(name=name, category=category, quantity=quantity, price=price))
            db.session.commit()
            flash('Product added.', 'success')
            return redirect(url_for('inventory_list'))
        return render_template('product_form.html', item=None)

    @app.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
    @login_required
    def inventory_edit(item_id):
        from models import Product
        item = Product.query.get_or_404(item_id)
        if request.method == 'POST':
            item.name = request.form.get('name', '').strip()
            item.category = request.form.get('category', '').strip()
            item.quantity = int(request.form.get('quantity', 0) or 0)
            item.price = float(request.form.get('price', 0) or 0)
            db.session.commit()
            flash('Product updated.', 'success')
            return redirect(url_for('inventory_list'))
        return render_template('product_form.html', item=item)

    @app.route('/inventory/<int:item_id>/delete', methods=['POST'])
    @login_required
    def inventory_delete(item_id):
        from models import Product
        item = Product.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash('Product deleted.', 'success')
        return redirect(url_for('inventory_list'))

    # ---- reports ----
    @app.route('/reports')
    @login_required
    def reports():
        from models import Product
        total_value = db.session.query(db.func.coalesce(db.func.sum(Product.quantity * Product.price), 0)).scalar() or 0
        low_stock = Product.query.filter(Product.quantity <= 5).order_by(Product.quantity.asc()).all()
        return render_template('report.html', total_value=total_value, low_stock=low_stock)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
