from os import access
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from src.constants.http_status_code import *
from src.database import *
from flasgger import swag_from
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity


auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post('/register')
@swag_from('./docs/auth/register.yml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    
    if len(password) < 6:
        data = {
            'error': "Password is too short"
        }
        return jsonify(data), HTTP_400_BAD_REQUEST
    
    elif len(username) < 3:
        data = {
            'error': "Username is too short"
        }
        return jsonify(data), HTTP_400_BAD_REQUEST
    
    elif not username.isalnum() or " " in username:
        data = {
            'error': "Username should be alphanumeric and also no spaces"
        }
        return jsonify(data), HTTP_400_BAD_REQUEST
    
    elif not validators.email(email):
        data = {
            'error': "Invalid email"
        }
        return jsonify(data), HTTP_400_BAD_REQUEST
    
    
    elif User.query.filter_by(email=email).first() is not None:
        data = {
            'error': "Email is Taken"
        }
        return jsonify(data), HTTP_409_CONFLICT
    
    elif User.query.filter_by(username=username).first() is not None:
        data = {
            'error': "Username is Taken"
        }
        return jsonify(data), HTTP_409_CONFLICT
    
    else:
        pwd_hash = generate_password_hash(password)
        user = User(username=username, password=pwd_hash, email=email)
        db.session.add(user)
        db.session.commit()
        
        data = {
            'message': "User Created",
            'user': {
                'username': username,
                'email': email
            }
        }
    
        return jsonify(data), HTTP_201_CREATED


@auth.post('/login')
@swag_from('./docs/auth/login.yml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        is_pass_correct = check_password_hash(user.password, password)
        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)
            
            data = {
                "user": {
                    "refresh": refresh,
                    "access": access,
                    "username": user.username,
                    "email": user.email
                }
            }
            return jsonify(data), HTTP_200_OK
        else:
            data = {
                "error": "Wrong Credentials"
            }
            return jsonify(data), HTTP_401_UNAUTHORIZED
        
    else:
        data = {
            "error": "User Not Found"
        }
        return jsonify(data), HTTP_404_NOT_FOUND
            
    

@auth.get('/current_user')
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    data = {
        "currentUser": {
            "username": user.username,
            "email": user.email
        }
    }
    return jsonify(data), HTTP_200_OK


@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_user_access_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)
    
    data = {
        "access": access
    }
    return jsonify(data)

