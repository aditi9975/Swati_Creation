from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from urllib.parse import urlparse as url_parse
from models import db, User, Product, Cart
from forms import LoginForm, SignupForm, AddProductForm
from config import Config
import os
from werkzeug.utils import secure_filename


app = Flask(__name__, static_folder='static')

app.config.from_object(Config)
db.init_app(app)
login = LoginManager(app)
login.login_view = 'login'

# Variable to track whether tables have been created
tables_created = False
@app.before_request
def create_tables():
    global tables_created
    if not tables_created:
        db.create_all()
        tables_created = True

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    products = Product.query.all()
    return render_template('admin/dashboard.html', products=products)


# Ensure the upload folder exists
UPLOAD_FOLDER = 'static/images/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add Product Functionality
@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    form = AddProductForm()
    
    if form.validate_on_submit():
        filepath = None  # Initialize filepath variable
        
        if form.image.data:  # Check if image was uploaded
            file = form.image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Convert to consistent relative path with forward slashes
                filepath = filepath.replace('\\', '/').replace('static/', '')
            else:
                flash('Invalid image format. Allowed formats are: png, jpg, jpeg, gif')
                return redirect(url_for('add_product'))
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=filepath  # Store consistent relative path
        )
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_product.html', form=form)

# Edit Product Functionality
@app.route('/admin/dashboard/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    form = AddProductForm(obj=product)
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data and hasattr(form.image.data, 'filename'):
            file = form.image.data
            if file and allowed_file(file.filename):
                # Delete old image if it exists
                if product.image:
                    old_file = os.path.join('static', product.image.replace('/', os.sep))
                    if os.path.exists(old_file):
                        os.remove(old_file)
                
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Convert to consistent relative path with forward slashes
                product.image = filepath.replace('\\', '/').replace('static/', '')
        
        # Update other product fields
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        
        db.session.commit()
        flash('Product updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_product.html', form=form, product=product)

# Delete Product Functionality
@app.route('/admin/dashboard/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    if product.image:
        old_file = os.path.join('static', product.image.replace('/', os.sep))
        if os.path.exists(old_file):
            os.remove(old_file)
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!')
    return redirect(url_for('admin_dashboard'))



@app.route('/user/dashboard')
@login_required
def user_dashboard():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('user/dashboard.html', cart_items=cart_items, total=total)


@app.route('/my_cart')
@login_required
def my_cart():
    # Get the user's cart items
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Render the cart page with the cart items and total price
    return render_template('my_cart.html', cart_items=cart_items, total=total)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('user/product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    db.session.commit()
    flash('Product added to cart!')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    flash('Product removed from cart!')
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
