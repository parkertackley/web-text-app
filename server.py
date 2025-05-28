import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, send_from_directory
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from uuid import uuid4
from bson import ObjectId, json_util
from datetime import datetime, timezone, timedelta
import os
import bcrypt
import hashlib
import html
import uuid

# Loading environtment variable
load_dotenv()

# Setting up flask to use "public" as the static folder
app = Flask(__name__, template_folder="public", static_folder="public")
socketio = SocketIO(app, logger=True, engineio_logger=True)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('post')
def handle_post(post):
    emit('posted', post)

# Setting up MongoDB
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/user-creds")
mongo = PyMongo(app)

# Favion
@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='/public/images/favicon.ico')

# COMMENT THIS OUT FOR LOCAL TESTING
# @app.before_request
# def before_request():
#     url = request.url.replace('http://', 'https://', 1)
#     code = 301
#     return redirect(url, code=code)

@app.after_request
def apply_caching(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Homepage
@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template("index.html")

@app.route('/account', methods=['POST', 'GET'])
def account():

    users = mongo.db.users

    if 'auth_token' in request.cookies:
        token = request.cookies.get('auth_token')
        hashedToken = hashlib.sha256(token.encode()).hexdigest()
        user = users.find_one({'tokenHash': hashedToken})

        if user:
            return render_template('account.html', username=user['username'])
    else:
        print("No auth token")
        return redirect('/')

# Changing password
@app.route('/change-password', methods=['POST'])
def change_password():
    # Users collection
    users = mongo.db.users

    if 'auth_token' not in request.cookies:
        return jsonify(message = "Not authenticated"), 401
    
    newPassword = request.form.get('password')
    confirmPassword = request.form.get('confirmPassword')

    if newPassword != confirmPassword:
        return jsonify(message = "Passwords do not match"), 403
    
    token = request.cookies.get('auth_token')
    hashedToken = hashlib.sha256(token.encode()).hexdigest()
    user = users.find_one({'tokenHash': hashedToken})

    if user:
        # Encoding password to bytes
        newPassword = newPassword.encode('utf-8')

        # Salting and hashing the password
        hashed_password = bcrypt.hashpw(newPassword, bcrypt.gensalt())

        # Updating DB
        users.update_one({'_id': user['_id']}, {'$set': {'password': hashed_password}})
        
        return jsonify(message = "Password changed successfully"), 200
    else:
        return jsonify(message = "User not found"), 404
    

# Getting username
@app.route('/get-username', methods=['GET'])
def get_username():
    # Users collection
    users = mongo.db.users

    if 'auth_token' not in request.cookies:
        return jsonify(username=None, message = "Not authenticated"), 401
    else:
        # Getting username from DB using auth token
        token = request.cookies.get('auth_token')
        hashedToken = hashlib.sha256(token.encode()).hexdigest()
        user = users.find_one({'tokenHash': hashedToken})
        if user:
            return jsonify(username=user['username']), 200
        else:
            return jsonify(username=None, message = "Not authenticated"), 401


# Changing username
@app.route('/update-username', methods=['POST'])
def update_username():
    # Users collection
    users = mongo.db.users

    if 'auth_token' not in request.cookies:
        return jsonify(message = "Not authenticated"), 401
    
    newName = request.form.get('username')
    if not newName:
        return jsonify(message = "New username is required"), 400
    
    token = request.cookies.get('auth_token')
    hashedToken = hashlib.sha256(token.encode()).hexdigest()
    user = users.find_one({'tokenHash': hashedToken})

    if user:
        users.update_one({'_id': user['_id']}, {'$set': {'username': newName}})
        return jsonify(message = "Username updated successfully"), 200
    
    else:
        return jsonify(message = "User not found"), 404

# Registration
@app.route('/register', methods=['POST'])
def register():
    # Users collection
    users = mongo.db.users

    # Getting usrename and password from the form
    username = request.json.get('username')
    password = request.json.get('password')
    passwordConfirm = request.json.get('confirmPassword')

    # Checking if passwords match
    if not password == passwordConfirm:
        return jsonify(message="Passwords don't match"), 403
    
    # Encoding password to bytes
    password = password.encode('utf-8')

    # Checking if the username is already taken
    userExists = users.find_one({'username': username})
    if userExists:
        return jsonify(message="Username already taken"), 403

    # Salting and hashing the password
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    # Inserting into database and sending 200 response
    users.insert_one({'username': username, 'password': hashed_password})
    return jsonify(message="Success"), 200

# Login
@app.route('/login', methods=['POST'])
def login():
    # Users collection
    users = mongo.db.users

    # Getting username and password from the form
    username = request.json.get('username')
    password = request.json.get('password')

    # Encoding password to bytes
    password = password.encode('utf-8')

    # Getting user from database
    user = users.find_one({'username': username})

    # Checking if password is correct
    if user and bcrypt.checkpw(password, user['password']):
        # Generage auth token and its hash
        token = os.urandom(16).hex()
        tokenHash = hashlib.sha256(token.encode('utf-8')).hexdigest()

        # Storing the hashed token in the db
        users.update_one({'username': username}, {'$set': {'tokenHash': tokenHash}})

        # Sending token to the user as 'auth_token' cookie
        response = make_response(jsonify(message="Login Successful", username=username), 200)
        response.set_cookie('auth_token', token, httponly=True, max_age=3600)
        return response
    
    else:
        return jsonify(message="Invalid username or password"), 401

# Authentication
@app.route('/auth', methods=['GET'])
def auth():
    # Users collection
    users = mongo.db.users

    # Getting auth token from cookies, if it exists
    if 'auth_token' in request.cookies:
        token = request.cookies.get('auth_token')
    else:
        return jsonify(message="No auth token"), 401
    
    # Hashing token and using it to retrieve user form db
    tokenHash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    user = users.find_one({'tokenHash': tokenHash})

    # Checking if token and user are valid
    if not user:
        return jsonify(message="Invalid User"), 401
    
    return jsonify(status='ok', username=user['username']), 200

# Logout
@app.route('/logout', methods=['POST'])
def logout():
    # Users collection
    users = mongo.db.users

    # Getting auth token from cookies, if it exists
    if 'auth_token' in request.cookies:
        token = request.cookies.get('auth_token')
    else:
        return jsonify(message="No auth token"), 401
    
    # Invalidating token
    tokenHash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    users.update_one({'tokenHash': tokenHash}, {'$unset': {'tokenHash': 1}})

    
    # Clearning auth token cookie and sending back 200 response
    response = make_response(jsonify(message="Logout Successful"), 200)
    response.set_cookie('auth_token', '', max_age=0)
    return response

# Create Posts
@app.route('/createpost', methods=['POST'])
def createpost():
    # users collection
    users = mongo.db.users
    # posts collection
    postsCollection = mongo.db.posts
    delayCollection = mongo.db.delay

    # Checking for auth token
    if 'auth_token' not in request.cookies:
        return jsonify(message = "Not authenticated"), 401
    

    token = request.cookies.get('auth_token')
    tokenHash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    user = users.find_one({'tokenHash': tokenHash})

    # Check if user was found
    if not user:
        return jsonify(message = "Not authenticated"), 401
    
    # Generating random post ID
    postID = str(uuid.uuid4())

    # Getting data from the form
    postType = request.form.get('type')
    text = request.form.get('text')
    image = request.files.get('image')
    imageURL = None
    # Creating a timestamp that is formatted to ISO 8601 a.k.a. YYYY-MM-DD HH.MM.SS.MMMM
    timestamp = datetime.now(timezone.utc)
    # getting time delay for post
    delay = int(request.form.get('delay', 0))
    # adding delay to timestamp
    posttime = timestamp + timedelta(seconds=delay)

    # Checking if image is in request
    if image:
        # Checking if the file is actually an image
        allowedExtensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        fileType = os.path.splitext(image.filename)[1]
        if fileType in allowedExtensions:
            fileName = f'{uuid4().hex}{fileType}'
            image.save(os.path.join('/app/public/images/user_images', fileName))
            imageURL = f'/public/images/user_images/{fileName}'
        else:
            return jsonify(message = "File type not allowed"), 400
        

    post = {
        'username': user['username'],
        'content': html.escape(text),
        'type': postType,
        'ID': postID,
        'imageURL': imageURL,
        'likes': [], # Initializing array for likes
        'timestamp': timestamp.isoformat(), # .isoformat to convert to time
        'delay': delay,
        'posttime': posttime.isoformat() # ^^
    }   

    # if delay add to delay collection
    if delay > 0:
        delayCollection.insert_one(post)
        post['_id'] = str(post['_id'])
        # create/add post id to list in user collection
        users.update_one({'_id': user['_id']}, {'$addToSet': {'postIDs': postID}})
    else:
        postsCollection.insert_one(post)
        post['_id'] = str(post['_id'])


    socketio.emit('posted', post)
    return jsonify(status='ok', message='Posts created successfully', postID=postID)

# Serving Images
@app.route('/images/user_images/<filename>')
def uploaded_file(filename):
    return send_from_directory('/app/public/images/user_images', filename)

# Get Posts
@app.route('/getposts', methods=['GET'])
def getposts():
    # Posts collection
    postsCollection = mongo.db.posts
    
    # Getting thread type from request
    threadType = request.args.get('threadType')

    # Getting posts from collection
    posts = postsCollection.find({'type': threadType})

    # Converting posts to JSON functional list
    posts_list = [{
        'username': post['username'],
        'content': post['content'],
        'type': post['type'],
        'ID': post['ID'],
        'imageURL': post.get('imageURL'),
        'likeCount': len(post.get('likes', [])),
        'timestamp': post.get('timestamp')
    } for post in posts]

    # Returing post list
    return jsonify(posts_list)

# Like Posts
@app.route('/likepost', methods=['POST'])
def likepost():
    # Getting collections
    users = mongo.db.users
    posts = mongo.db.posts

    # Getting post id from request
    postID = request.json.get('postID')

    if 'auth_token' not in request.cookies:
        return jsonify(message="No auth token"), 401
    
    token = request.cookies.get('auth_token')
    tokenHash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    user = users.find_one({'tokenHash': tokenHash})

    if not user:
        return jsonify(message = "User not found"), 401

    username = user['username']


    # Getting post with id
    post = posts.find_one({'ID': postID})

    # Checking if post doesn't exist
    if not post:
        return jsonify(message = "Post not found"), 404
    
    # Checking if user already like the post
    if username in post.get('likes', []):
        # Remove user from liked list
        posts.update_one({'ID': postID}, {'$pull': {'likes': username}})
        return jsonify(message = "Removed like from post"), 200
    else:
        # Adding user to liked list
        posts.update_one({'ID': postID}, {'$push': {'likes': username}})
        return jsonify(message = "Liked post"), 200


@app.route('/users', methods=['GET'])
def users():
    users = mongo.db.users
    users_list = [user['username'] for user in users.find()]
    return jsonify(users_list)

if __name__ == '__main__':
    print("Listening on port 8080")
    app.run(debug=True)
    # socketio.run(app, debug=True)#, port=8080)
    # , ssl_context=('/nginx/cert.pem', '/nginx/private.key')
    # COMMENT FROM ', PORT=8080' TO THE END FOR LOCAL TESTING