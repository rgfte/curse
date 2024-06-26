from sqlalchemy import ForeignKey
from flask_login import UserMixin


from back.ext import db, manager

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('carts', lazy=True))
    
    product_id = db.Column(db.Integer, ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('carts', lazy=True))


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable = False, unique=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dateCreation = db.Column(db.Date, nullable=False)
    dateShipping = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    addres = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))


class OrderProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    order = db.relationship('Order', backref=db.backref('order_products', lazy='dynamic'))
    product = db.relationship('Product', backref=db.backref('order_products', lazy='dynamic'))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable = False)
    price = db.Column(db.Integer, nullable=False)
    img = db.Column(db.String(100), nullable=False)

    category_id = db.Column(db.Integer, ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable = True)
    email = db.Column(db.String(50), nullable = True, unique=True)
    password = db.Column(db.String(200), nullable = True)
    phone = db.Column(db.String(12), nullable = True)
    surname = db.Column(db.String(45), nullable = True)
    role = db.Column(db.String(50), nullable=False, default='user')


@manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))