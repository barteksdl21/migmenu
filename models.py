# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(150), unique=True, nullable=False)
  email = db.Column(db.String(150), unique=True, nullable=False)
  password = db.Column(db.String(200), nullable=False)
  menus = db.relationship('Menu', backref='owner', lazy=True)

class Menu(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(150), nullable=False)
  shareable_link = db.Column(db.String(200), unique=True, nullable=False)
  qr_code = db.Column(db.String(200), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  categories = db.relationship('Category', backref='menu', lazy=True, cascade="all, delete-orphan", order_by="Category.order")

class Category(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  order = db.Column(db.Integer, nullable=False)
  menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
  items = db.relationship('MenuItem', backref='category', lazy=True, cascade="all, delete-orphan", order_by="MenuItem.order")

class MenuItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(150), nullable=False)
  description = db.Column(db.Text, nullable=True)
  price = db.Column(db.Float, nullable=False)
  order = db.Column(db.Integer, nullable=False)
  category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)