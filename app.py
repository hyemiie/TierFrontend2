
from flask import Flask, jsonify, session, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy.orm import relationship
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt
from sqlalchemy.dialects.postgresql import JSON 
import os





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://tier_user:R1Jm8lPVucA19TvVgmZoJbhClWxyN6aA@dpg-cnl2fkol5elc73dopl7g-a.oregon-postgres.render.com/tier'
 
app.config['SECRET_KEY'] = 'your_strong_secret_key'  
app.config["JWT_SECRET_KEY"] = 'your_jwt_secret_key'  
app.config['JWT_TOKEN_LOCATION'] = ['headers' ]  
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
blacklist = set()  # Define the blacklist

# postgres://tier_user:R1Jm8lPVucA19TvVgmZoJbhClWxyN6aA@dpg-cnl2fkol5elc73dopl7g-a.oregon-postgres.render.com/tier
CORS(app)
 
 


class Products(db.Model):
    productID = db.Column(db.Integer, primary_key=True)
    productName = db.Column(db.String(20), nullable=False)
    productImage = db.Column(db.String(80), nullable=False)
    productPrice = db.Column(db.String(80), nullable=False)
    productDesc = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            'product_ID' : self.productID,
            'product_name': self.productName,
            'product_image': url_for('static', filename=f'{self.productImage}'),
            'product_price': self.productPrice,
            'product_desc': self.productDesc
        }
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    cart = db.Column(JSON, nullable=True, default=list)  # Make cart nullable

    # Define the relationship between User and CartProducts
    cart_products = relationship('CartProducts', backref="user", lazy="dynamic")
    # Define the relationship between User and Wishlists
    wishlists = db.relationship('Wishlists', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'





class CartProducts(db.Model):
    productID = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    productName = db.Column(db.String(20), unique=True, nullable=False)
    productImage = db.Column(db.String(80), nullable=False)
    productDesc = db.Column(db.String(80), nullable=False)
    productPrice = db.Column(db.String(80), nullable=False)
    productQuantity = db.Column(db.Integer , nullable=False)

    def to_dict(self):
        return {
            'product_ID': self.productID,
            'product_Name': self.productName,
            'product_Img': self.productImage,
            'product_Desc': self.productDesc,
            'product_Price': self.productPrice,
            'product_Quantity': self.productQuantity,
         }

class Wishlists(db.Model):
    productID = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    productName = db.Column(db.String(20), unique=True, nullable=False)
    productImage = db.Column(db.String(80), nullable=False)
    productDesc = db.Column(db.String(80), nullable=False)
    productPrice = db.Column(db.String(80), nullable=False)
    productQuantity = db.Column(db.Integer , nullable=False)

    def to_dict(self):
        return {
            'product_ID': self.productID,
            'product_Nme': self.productName,
            'product_Image': self.productImage,
            'product_Descrip': self.productDesc,
            'product_Prices': self.productPrice,
            'product_QTY': self.productQuantity,
         }         
 
@app.route('/')
def index():
    return 'Hello World'

@app.route('/products')
def products():
    ProductsLists = Products.query.all()
    products_dict_list = [product.to_dict() for product in ProductsLists]
    return jsonify(products=products_dict_list)
 

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    print('Received data:', username , password)

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'message': 'Login Success', 'access_token': access_token})
    else:
        return jsonify({'message': 'Login Failed'}), 401

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the JWT ID
    # Add jti to a blacklist (in-memory, database, or Redis)
    blacklist.add(jti)  # Example using in-memory blacklist
    return jsonify({'message': 'Successfully logged out'}), 200

@app.route('/api/cart/add', methods=['POST'])
@jwt_required() 
def add_to_cart():
    if request.method == 'POST':
        data = request.get_json()
        user_id = get_jwt_identity()
        PRODUCTID = data['productId']
        PRODUCTNAME=  data['name']
        PRODUCTIMAGE= data['imageUrl']
        PRODUCTDESC=  data['Description'] 
        PRODUCTPRICE=  data['price']
        PRODUCTQUANTITY=  data['QTY']
        
        existing_product = CartProducts.query.filter_by(productID=PRODUCTID).first()

        print("userID:", user_id)

        if existing_product:
            print("Product exists")

        # Update quantity and price if the product already exists
            existing_product.productQuantity += PRODUCTQUANTITY
            existing_product.productPrice = PRODUCTPRICE
            db.session.commit()
            message ='Quantity updated.'
            print(message)
            # print('Quantity updated.')
            return jsonify({'message': 'Quantity updated'})
        else:
        # Add the product to the user's cart if it doesn't exist
            cart_item = CartProducts(
            user_id=user_id,
            productName=PRODUCTNAME,
            productImage=PRODUCTIMAGE,
            productDesc=PRODUCTDESC,
            productPrice=PRODUCTPRICE,
            productQuantity=PRODUCTQUANTITY,
        )
     
        print('cart_item' , cart_item)

        db.session.add(cart_item)
        db.session.commit()
        print('Product added to cart successfully.')
    return jsonify({'message': 'Product added to cart successfully'})
        
 
# def addProduct(user_id, product_id, productname, productimage, productdesc, productprice, productquantity):
#     print('Adding product to cart...')
#     print('User ID:', user_id)
#     print('Product ID:', product_id)
#     print('Product Name:', productname)
#     print('Product Quantity:', productquantity)

#     existing_product = CartProducts.query.filter_by(productID=product_id).first()

#     if existing_product:
#         # Update quantity and price if the product already exists
#         existing_product.productQuantity += productquantity
#         existing_product.productPrice = productprice
#         db.session.commit()
#         print('Quantity updated.')
#         return jsonify({'message': 'Quantity updated'})
#     else:
#         # Add the product to the user's cart if it doesn't exist
#         cart_item = CartProducts(
#             user_id=user_id,
#             productName=productname,
#             productImage=productimage,
#             productDesc=productdesc,
#             productPrice=productprice,
#             productQuantity=productquantity,
#         )

#         print('cart_item' , cart_item)

#         db.session.add(cart_item)
#         db.session.commit()
#         print('Product added to cart successfully.')
#         return jsonify({'message': 'Product added to cart successfully'})

 
        
# @app.route('/Cart', methods=['GET'])
# @jwt_required() 
# def viewCart():
#     user_id = get_jwt_identity()
     
#     CartView = CartProducts.query.filter_by(user_id= user_id).all()
#     Cart_dict_list = [cart.to_dict() for cart in CartView]
#     return jsonify(Carts=Cart_dict_list)


@app.route('/Cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    print(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Refresh user object to ensure latest cart data (optional)
    db.session.refresh(user)
    user_cart = CartProducts.query.filter_by(user_id= user_id).all()
    print('all carts:', user_cart)

    # cart_items = user.cart_products.all()  # Now you can use .all() correctly
    cart_data = [item.to_dict() for item in user_cart]
    print('cart_data is:' , cart_data)
    return jsonify({'cart_items': cart_data})

# @app.route('/tasks', methods=['GET'])
# @jwt_required() 
# def tasks():
#     user_id = get_jwt_identity()  # Retrieve user ID from JWT

#     CartView = CartProducts.query.filter_by(user_id=user_id).all()
#     CartList = [{'id': Produ.id, 'title': task.title} for task in user_tasks]
#     return jsonify({'Cart': tasks_data})


@app.route('/api/cart/delete', methods=['DELETE'])
def delete_from_cart():
    product_id = request.args.get('product_id')
    print('product id is' , product_id)  # Fix: Retrieve product_id from request parameters

    existing_product = CartProducts.query.filter_by(productID=product_id).first()

    if existing_product:
        db.session.delete(existing_product)
        db.session.commit()
        return jsonify({'message': 'Product Deleted'})
    else:
        return jsonify({"message": "Product doesn't exist"})
 
@app.route('/users')
def users():
    UserLists = User.query.all()
    userLists = [user.__dict__ for user in UserLists]
    return jsonify(users=userLists)

 
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()

        print('Received data:', data)  # Add this line to print the received data

        username = data[ 'username' ]
        password = data[ 'password' ]

        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400

        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'})


@app.route('/get_name', methods=['GET'])
@jwt_required()
def get_name():
    # Extract the user ID from the JWT
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    # Check if user exists
    if user:
        return jsonify({'message': 'User found', 'name': user.username})
    else:
        return jsonify({'message': 'User not found'}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Populate Products table
        # new_Cart = Cart( productID = 2, productName= 'Fan Charger', productQuantity= 3  )
        # db.session.add(new_Cart)
        # db.session.commit()

        # new_product = Products(  productName= 'Brown Sofa ' , productImage='images/Image7.jpg', productPrice='19000.00', productDesc='brown Sofa wih feathery ruffles'  )
        # db.session.add(new_product)
        # db.session.commit()

        # new_product = Products(  productName= 'Table Drawer' , productImage='images/ProductImage8.png', productPrice='700.00', productDesc='Drawer' )
        # db.session.add(new_product)
        # db.session.commit()

        # new_product = Products(  productName= 'Single Chair' , productImage='images/ProductImage7.png', productPrice='820.00', productDesc='Chair'  )
        # db.session.add(new_product)
        # db.session.commit()

        # new_product = Products(  productName= 'Light Table Drawers' , productImage='images/ProductImage9.png', productPrice='79000.00', productDesc='Drawer'  )
        # db.session.add(new_product)
        # db.session.commit()


        # new_product = Products(  productName= ' BedSide Drawers' , productImage='images/ProductImage10.png', productPrice='21000.00', productDesc='Drawer'  )
        # db.session.add(new_product)
        # db.session.commit()


        # new_product = Products(  productName= 'Studio Desk' , productImage='images/ProductImage11.png', productPrice='92000.00', productDesc='Desk'  )
        # db.session.add(new_product)
        # db.session.commit()

        # new_product = Products(  productName= 'Sofia Lounge Chair' , productImage='images/ProductImage12.png', productPrice='8000.00', productDesc='Chair'  )
        # db.session.add(new_product)
        # db.session.commit()






        # new_product = CartProducts( productID=6, user_id=5, productName= 'Blue Sofa ' , productImage='../Images//Image6.png', productPrice='17000.00', productDesc='Blue Sofa wih feathery ruffles', productQuantity = 2 )
        # db.session.add(new_product)
        # db.session.commit()

        
        # new_product = CartProducts(  user_id= 4 ,productName= 'Brows Sofa ' , productImage='images/Image7.jpg', productPrice='19000.00', productDesc='brown Sofa wih feathery ruffles', productQuantity = 2 )
        # db.session.add(new_product)
        # db.session.commit()

        # new_product = Products( productID= 4, productName= 'Phone Pouch' , productImage=f'images/{image_url}', productPrice='400.00', productDesc='A sleek and stylish Phone Pouch')
        # db.session.add(new_product)
        # db.session.commit()

        # Populate User table


        # db.session.query(Products).delete()
        # db.session.commit()
        

        # db.drop_all()
        # db.session.commit()

        # db.session.delete(User)
        # db.commit()

        app.run(debug=True)
