from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # auto-increment is implied by primary_key
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    cart_items = db.relationship('Cart',back_populates='user')
    wishlist_items = db.relationship('Wishlist',back_populates='user')
    commented_by = db.relationship('Reviews',back_populates='user')
    def __repr__(self):
        return f'User {self.id}'
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    image = db.Column(db.String(255),nullable = False)

    cart_items = db.relationship('Cart',back_populates='product')
    wishlisted_by = db.relationship('Wishlist',back_populates='product')
    def __repr__(self):
        return f'<Product {self.name}>'

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float)

    user = db.relationship('User', back_populates = 'cart_items')
    product = db.relationship('Product',back_populates = 'cart_items')

    def __repr__(self):
        return f'<Cart Product ID: {self.product_id}, Quantity: {self.quantity}>'

class Wishlist(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey('product.id'),nullable = False)

    user = db.relationship('User',back_populates = 'wishlist_items')
    product = db.relationship('Product',back_populates = 'wishlisted_by')

    def __repr__(self):
        return f'<Wishlist Product ID {self.product_id}>'
    
class Reviews(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    review_content = db.Column(db.String(1000),nullable = False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    user = db.relationship('User',back_populates ='commented_by')

    def __repr__(self):
        return f'Reviews {self.id}'