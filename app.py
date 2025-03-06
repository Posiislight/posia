from flask import Flask,redirect,url_for,flash,render_template,request,jsonify,Response
from models import User,Product,Cart,Wishlist,Reviews,db
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user,login_required,LoginManager,logout_user,current_user
import requests
import uuid
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/posia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
from llamaapi import LlamaAPI
from dotenv import load_dotenv
import os
from openai import OpenAI
import json

client = OpenAI(base_url = "https://openrouter.ai/api/v1",api_key = "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")

load_dotenv()
api_key = os.getenv('TOGETHER_AI_API_KEY')
db.init_app(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if user_id is None or user_id == None:
        return None
    return User.query.get(int(user_id))

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html',products=products)

@app.route('/transaction/initialize',methods=['GET','POST'])
def checkout():
    api_url = "https://api.paystack.co/transaction/initialize"

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    kobo_total_price = int(total_price*100)
    headers = {
        "Authorization": "Bearer sk_test_3eb305b07b37a2738671ff84a9cac6218d0d92fa",
        "Content-Type": "application/json"
    }
    data = {
        'email':'adelekeolamiposi@gmail.com',
        'amount':kobo_total_price,
        'currency': 'NGN'
        }
    
    response = requests.post(api_url,json=data,headers=headers)
    response.json(),response.status_code
    
    result = response.json()
    authorization_url = result['data']['authorization_url']
    return redirect(authorization_url)
@app.route('/flutterwave',methods = ['GET','POST'])
def flutterwave():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer FLWSECK_TEST-8c3e54e705f4feb8245ee74f90f94877-X",
        "Content-Type": "application/json"
    }
    data = {
        'tx_ref': str(uuid.uuid4()),
        'amount': total_price,
        'currency':'NGN',
        'redirect_url': 'localhost:5000/cart',
        'customer' : {
            'email':'adelekeolamiposi@gmail.com'
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Failed to initiate transfer: {response.text}")

    transfer_response = response.json()
    
    return redirect(transfer_response['data']['link'])

@app.route('/register',methods = ['GET','POST'])
def register():
    if request.method ==  'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username,password=password).first()
        if existing_user:
            flash('User already exits')
            return redirect(url_for('register'))
        else:
            new_user = User(username=username,password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return(redirect(url_for('index')))
        else:
            flash('Username of password is incorrect')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/cart',methods = ['GET','POST'])
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html',cart_items=cart_items,total_price = total_price)

@app.route('/cart/add/<int:product_id>',methods =['POST','GET'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    quantity = int(request.form.get('quantity',1))

    
    existing_product = Cart.query.filter_by(user_id=current_user.id,product_id=product.id).first()
    if existing_product:
        existing_product.quantity += quantity
        db.session.commit()
        flash('Item quantity updated')
    else:
        new_product = Cart(user_id = current_user.id,product_id = product_id,quantity = quantity)
        db.session.add(new_product)
        db.session.commit()
        flash('Item added to cart')
    return redirect(url_for('index'))

@app.route('/cart/delete_from_cart/<int:product_id>',methods=['POST'])
@login_required
def delete_from_cart(product_id):
    cart_to_delete = Cart.query.filter_by(user_id = current_user.id,product_id = product_id).first()
    if cart_to_delete:
        db.session.delete(cart_to_delete)
        db.session.commit()
        flash('Item deleted')
    return redirect(url_for('cart'))

@app.route('/cart/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if not cart_item:
        flash('Item not found in cart')
        return redirect(url_for('cart'))

    action = request.form.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    
    db.session.commit()
    flash('Cart updated successfully')
    return redirect(url_for('cart'))



@app.route('/wishlist',methods = ['POST','GET'])
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html',wishlist_items=wishlist_items)

@app.route('/wishlist/add_to_wishlist/<int:product_id>',methods=['GET','POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    existing_product = Wishlist.query.filter_by(user_id = current_user.id,product_id = product.id).first()
    if existing_product:
        flash('product already in wishlist')
    else:
        new_product = Wishlist(user_id = current_user.id,product_id = product.id)
        flash('successfully added to wishlist')
        db.session.add(new_product)
        db.session.commit()
    return (redirect(url_for('index')))

@app.route('/wishlist/remove_from_wishlist/<int:product_id>',methods = ['GET','POST'])
@login_required
def remove_from_wishlist(product_id):
    product = Product.query.get(product_id)
    product_to_delete = Wishlist.query.filter_by(user_id = current_user.id,product_id = product.id).first()
    db.session.delete(product_to_delete)
    db.session.commit()
    flash('removed from wishlist')
    return(redirect(url_for('wishlist')))

@app.route('/product_view/<int:product_id>',methods=['GET','POST'])
def product_view(product_id):
    product = Product.query.get(product_id)
    commented_by = Reviews.query.all()
    return render_template('product_view.html',product = product,commented_by=commented_by)
@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return(redirect(url_for('index')))

@app.route('/search',methods=['POST','GET'])
def search():
    search_item = request.form.get('search_item',' ')
    if search_item:
        products = Product.query.filter(Product.name.like(f'%{search_item}%')).all()
        return render_template('index.html',products = products)
    else:
        
        return (redirect(url_for('index')))

@app.route('/initialize/chatbot', methods=['POST','GET'])
def chatbot():
    chatbot_reply = None
    if request.method == 'POST':
        user_message = request.form.get('message')
        
        headers = {
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen/qwq-32b:free",
            "messages": [
                {
                    "role": "user",
                    "content": user_message  # Use the actual user message
                }
            ]
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data  # Use json parameter instead of data with json.dumps
            )
            
            response_data = response.json()
            print(response_data)  # Add this to debug the response structure
            
            # The correct structure for OpenRouter responses
            chatbot_reply = response_data.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        except Exception as e:
            chatbot_reply = f"Error: {str(e)}"
            print(f"Error: {str(e)}")
            
    return render_template('chatbot.html', chatbot_reply=chatbot_reply)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)