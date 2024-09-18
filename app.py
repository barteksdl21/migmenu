# app.py
import os
import string
import random
from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, Menu, MenuItem, Category, User  # Import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, TextAreaField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import qrcode
from flask import send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask import jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'menu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to 'login' when login is required

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Create the database tables
with app.app_context():
  db.create_all()

# Ensure the qr_codes directory exists
QR_DIR = os.path.join(basedir, 'qr_codes')
if not os.path.exists(QR_DIR):
  os.makedirs(QR_DIR)

# Forms
class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
  email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
  password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

  def validate_username(self, username):
      user = User.query.filter_by(username=username.data).first()
      if user:
          raise ValidationError('Username already exists. Please choose a different one.')

  def validate_email(self, email):
      email = User.query.filter_by(email=email.data).first()
      if email:
          raise ValidationError('Email already registered. Please choose a different one.')

class LoginForm(FlaskForm):
  email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
  password = PasswordField('Password', validators=[DataRequired()])
  submit = SubmitField('Login')


class MenuItemForm(FlaskForm):
  category = StringField('Category', validators=[DataRequired(), Length(max=100)])
  name = StringField('Dish Name', validators=[DataRequired(), Length(max=150)])
  description = TextAreaField('Description')
  price = FloatField('Price', validators=[DataRequired()])

class CreateMenuForm(FlaskForm):
  title = StringField('Menu Title', validators=[DataRequired(), Length(max=150)])
  submit_button = SubmitField('Create Menu')

class EditMenuForm(FlaskForm):
  title = StringField('Menu Title', validators=[DataRequired(), Length(max=150)])
  submit_button = SubmitField('Update Menu')  

# Utility function to generate random string for shareable link
def generate_unique_link(length=8):
  characters = string.ascii_letters + string.digits
  while True:
      rand_str = ''.join(random.choice(characters) for _ in range(length))
      if not Menu.query.filter_by(shareable_link=rand_str).first():
          break
  return rand_str

# Routes for Authentication

@app.route('/register', methods=['GET', 'POST'])
def register():
  if current_user.is_authenticated:
      return redirect(url_for('index'))
  form = RegistrationForm()
  if form.validate_on_submit():
      hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
      new_user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
      db.session.add(new_user)
      try:
          db.session.commit()
          flash('Account created successfully! You can now log in.', 'success')
          return redirect(url_for('login'))
      except Exception as e:
          db.session.rollback()
          flash('Error creating account. Please try again.', 'danger')
  return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
      return redirect(url_for('index'))
  form = LoginForm()
  if form.validate_on_submit():
      user = User.query.filter_by(email=form.email.data).first()
      if user and bcrypt.check_password_hash(user.password, form.password.data):
          login_user(user)
          flash('Logged in successfully!', 'success')
          next_page = request.args.get('next')
          return redirect(next_page) if next_page else redirect(url_for('index'))
      else:
          flash('Login Unsuccessful. Please check email and password.', 'danger')
  return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
  logout_user()
  flash('You have been logged out.', 'info')
  return redirect(url_for('index'))

# Existing Routes with Authentication

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_menu():
  form = CreateMenuForm()
  if form.validate_on_submit():
      title = form.title.data
      shareable_link = generate_unique_link()
      menu_url = url_for('view_menu', link=shareable_link, _external=True)
      
      # Generate QR code
      qr = qrcode.QRCode(version=1, box_size=10, border=5)
      qr.add_data(menu_url)
      qr.make(fit=True)
      img = qr.make_image(fill='black', back_color='white')
      qr_filename = f"{shareable_link}.png"
      qr_path = os.path.join(QR_DIR, qr_filename)
      img.save(qr_path)
      
      # Create Menu entry linked to current user
      new_menu = Menu(title=title, shareable_link=shareable_link, qr_code=qr_filename, owner=current_user)
      db.session.add(new_menu)
      db.session.flush()  # To get the new_menu.id
      
      print(f"Created menu: {new_menu.id} - {new_menu.title}")  # Debug print
      
      # Process categories and items
      categories_data = request.form.to_dict(flat=False)
      print(f"Categories data: {categories_data}")  # Debug print
      
      category_indices = sorted(set(key.split('[')[1].split(']')[0] for key in categories_data.keys() if key.startswith('categories[') and key.endswith('][name]')))
      
      categories = {}
      for category_index in category_indices:
          category_name = categories_data.get(f'categories[{category_index}][name]', [''])[0]
          category_order = int(categories_data.get(f'categories[{category_index}][order]', [0])[0])
          if category_name:
              category = Category(name=category_name, menu_id=new_menu.id, order=category_order)
              db.session.add(category)
              db.session.flush()  # To get the category.id
              categories[category_index] = category
              print(f"Created category: {category.id} - {category.name} - Order: {category_order}")  # Debug print
      
      item_indices = sorted(set(key.split('[')[1].split(']')[0] for key in categories_data.keys() if key.startswith('items[') and key.endswith('][name]')))
      
      for item_index in item_indices:
          name = categories_data.get(f'items[{item_index}][name]', [''])[0]
          description = categories_data.get(f'items[{item_index}][description]', [''])[0]
          price = categories_data.get(f'items[{item_index}][price]', ['0'])[0]
          item_order = int(categories_data.get(f'items[{item_index}][order]', [0])[0])
          category_index = categories_data.get(f'items[{item_index}][category_id]', [''])[0]
          
          if name and price and category_index in categories:
              try:
                  price_val = float(price)
              except ValueError:
                  price_val = 0.0
              item = MenuItem(name=name, description=description, price=price_val,
                              category_id=categories[category_index].id, order=item_order)
              db.session.add(item)
              print(f"Created item: {item.name} - {item.price} - Order: {item_order} - Category: {categories[category_index].name}")  # Debug print
      
      try:
          db.session.commit()
          print("Database commit successful")  # Debug print
      except Exception as e:
          db.session.rollback()
          print(f"Error during commit: {str(e)}")  # Debug print
          flash('An error occurred while creating the menu.', 'error')
          return render_template('create_menu.html', form=form)
      
      flash('Menu created successfully!', 'success')
      return redirect(url_for('view_menu', link=shareable_link))
  return render_template('create_menu.html', form=form)

@app.route('/menu/<link>')
def view_menu(link):
  menu = Menu.query.filter_by(shareable_link=link).first_or_404()
  categories = Category.query.filter_by(menu_id=menu.id).order_by(Category.order).all()
  qr_code_url = url_for('serve_qr_code', filename=menu.qr_code)
  return render_template('view_menu.html', menu=menu, categories=categories, qr_code_url=qr_code_url)


@app.route('/edit/<link>', methods=['GET', 'POST'])
@login_required
def edit_menu(link):
  menu = Menu.query.filter_by(shareable_link=link).first_or_404()
  if menu.owner != current_user:
      flash('You do not have permission to edit this menu.', 'danger')
      return redirect(url_for('view_menu', link=link))
  
  form = EditMenuForm(obj=menu)
  
  if form.validate_on_submit():
      menu.title = form.title.data
      
      # Process categories and items
      categories_data = request.form.to_dict(flat=False)
      print(f"Categories data: {categories_data}")  # Debug print
      
      # Update or create categories
      category_indices = sorted(set(key.split('[')[1].split(']')[0] for key in categories_data.keys() if key.startswith('categories[') and key.endswith('][name]')))
      
      existing_category_ids = set(category.id for category in menu.categories)
      updated_category_ids = set()
      
      for category_index in category_indices:
          category_name = categories_data.get(f'categories[{category_index}][name]', [''])[0]
          category_order = int(categories_data.get(f'categories[{category_index}][order]', [0])[0])
          
          if category_index.startswith('category-'):
              category_id = int(category_index.split('-')[-1])
              # Update existing category
              category = Category.query.get(category_id)
              if category:
                  category.name = category_name
                  category.order = category_order
                  updated_category_ids.add(category.id)
          elif category_name:
              # Create new category
              category = Category(name=category_name, menu_id=menu.id, order=category_order)
              db.session.add(category)
              db.session.flush()  # To get the category.id
              updated_category_ids.add(category.id)
          
          print(f"Updated/Created category: {category.id} - {category.name} - Order: {category_order}")  # Debug print
      
      # Delete categories that were removed
      for category_id in existing_category_ids - updated_category_ids:
          category_to_delete = Category.query.get(category_id)
          db.session.delete(category_to_delete)
      
      # Update or create items
      item_indices = sorted(set(key.split('[')[1].split(']')[0] for key in categories_data.keys() if key.startswith('items[') and key.endswith('][name]')))
      
      existing_item_ids = set(item.id for category in menu.categories for item in category.items)
      updated_item_ids = set()
      
      for item_index in item_indices:
          name = categories_data.get(f'items[{item_index}][name]', [''])[0]
          description = categories_data.get(f'items[{item_index}][description]', [''])[0]
          price = categories_data.get(f'items[{item_index}][price]', ['0'])[0]
          item_order = int(categories_data.get(f'items[{item_index}][order]', [0])[0])
          category_id_str = categories_data.get(f'items[{item_index}][category_id]', [''])[0]
          
          # Extract the numeric part of the category_id
          category_id = int(category_id_str.split('-')[-1]) if category_id_str.startswith('category-') else int(category_id_str)
          
          if item_index.startswith('item-'):
              item_id = int(item_index.split('-')[-1])
              # Update existing item
              item = MenuItem.query.get(item_id)
              if item:
                  item.name = name
                  item.description = description
                  item.price = float(price)
                  item.order = item_order
                  item.category_id = category_id
                  updated_item_ids.add(item.id)
          elif name and price:
              # Create new item
              item = MenuItem(name=name, description=description, price=float(price),
                              category_id=category_id, order=item_order)
              db.session.add(item)
              db.session.flush()  # To get the item.id
              updated_item_ids.add(item.id)
          
          print(f"Updated/Created item: {name} - {price} - Order: {item_order} - Category: {category_id}")  # Debug print
      
      # Delete items that were removed
      for item_id in existing_item_ids - updated_item_ids:
          item_to_delete = MenuItem.query.get(item_id)
          db.session.delete(item_to_delete)
      
      try:
          db.session.commit()
          print("Database commit successful")  # Debug print
          flash('Menu updated successfully!', 'success')
          return redirect(url_for('view_menu', link=link))
      except Exception as e:
          db.session.rollback()
          print(f"Error during commit: {str(e)}")  # Debug print
          flash('An error occurred while updating the menu.', 'error')
  
  categories = Category.query.filter_by(menu_id=menu.id).order_by(Category.order).all()
  return render_template('edit_menu.html', form=form, menu=menu, categories=categories)

@app.route('/delete/<link>', methods=['POST'])
@login_required
def delete_menu(link):
  menu = Menu.query.filter_by(shareable_link=link).first_or_404()
  if menu.owner != current_user:
      return jsonify({'success': False, 'message': 'You do not have permission to delete this menu.'}), 403
  
  # Delete associated QR code file
  qr_file_path = os.path.join(QR_DIR, menu.qr_code)
  if os.path.exists(qr_file_path):
      os.remove(qr_file_path)
  
  # Delete the menu and all associated categories and items
  db.session.delete(menu)
  
  try:
      db.session.commit()
      return jsonify({'success': True, 'message': 'Menu deleted successfully!'})
  except Exception as e:
      db.session.rollback()
      return jsonify({'success': False, 'message': 'An error occurred while deleting the menu.'}), 500

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
  user_menus = current_user.menus
  return render_template('dashboard.html', menus=user_menus)

# Home Route
@app.route('/')
def index():
  return render_template('index.html')

@app.route('/qr_codes/<filename>')
def serve_qr_code(filename):
  return send_from_directory(QR_DIR, filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
  app.run(debug=True)