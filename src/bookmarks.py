from flask import Blueprint, request, jsonify
from flask_jwt_extended.view_decorators import jwt_required
from src.database import *
import validators
from flask_jwt_extended import get_jwt_identity
from src.constants.http_status_code import *
from flasgger import swag_from


bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()
    if request.method == "POST":
        body = request.get_json().get('body', '')
        url = request.get_json().get('url', '')
        
        if not validators.url(url):
            data = {
                "error": "Kindly enter Valid Url"
            }
            return jsonify(data), HTTP_400_BAD_REQUEST
        elif Bookmark.query.filter_by(url=url).first():
            data = {
                "error": "URL already exist"
            }
            return jsonify(data), HTTP_409_CONFLICT 
        
        else:
            bmk = Bookmark(url=url, body=body, user_id=current_user)
            db.session.add(bmk)
            db.session.commit()
            
            data = {
                "id": bmk.id,
                "url": bmk.url,
                "short_url": bmk.short_url,
                "visit": bmk.visit,
                "body": bmk.body,
                "create_at": bmk.created_at,
                "updated_at": bmk.updated_at
            }
            return jsonify(data), HTTP_201_CREATED
    
    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        bmks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        
        datas = []
        
        for bmk in bmks.items:
            datas.append({
                "id": bmk.id,
                "url": bmk.url,
                "short_url": bmk.short_url,
                "visit": bmk.visit,
                "body": bmk.body,
                "create_at": bmk.created_at,
                "updated_at": bmk.updated_at
            })
            meta = {
                "page": bmks.page,
                "pages": bmks.pages,
                "total_count": bmks.total,
                "prev": bmks.prev_num,
                "next": bmks.next_num,
                "has_next": bmks.has_next,
                "has_prev": bmks.has_prev,
            }
        return jsonify({"data":datas, "meta": meta}), HTTP_200_OK
    

@bookmarks.get('/<int:id>')
@jwt_required()
def get_bookmarks_by_id(id):
    current_user = get_jwt_identity()
    bmk = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bmk:
        data = {
            "error": "Not found"
        }
        return jsonify(data), HTTP_404_NOT_FOUND
    
    else:
        data = {
            "id": bmk.id,
            "url": bmk.url,
            "short_url": bmk.short_url,
            "visit": bmk.visit,
            "body": bmk.body,
            "create_at": bmk.created_at,
            "updated_at": bmk.updated_at
        }
        return jsonify(data), HTTP_302_FOUND
           
            

@bookmarks.put('/<int:id>')
@bookmarks.patch('/<int:id>')
@jwt_required()
def update_bookmark(id):
    current_user = get_jwt_identity()
    
    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')
    
    bmk = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bmk:
        data = {
            "error": "Not found"
        }
        return jsonify(data), HTTP_404_NOT_FOUND
    
    else:
        if not validators.url(url):
            data = {
                "error": "Kindly enter Valid Url"
            }
            return jsonify(data), HTTP_400_BAD_REQUEST
        
        else:
            bmk.body = body
            bmk.url = url
            db.session.commit()
            
            data = {
                "id": bmk.id,
                "url": bmk.url,
                "short_url": bmk.short_url,
                "visit": bmk.visit,
                "body": bmk.body,
                "create_at": bmk.created_at,
                "updated_at": bmk.updated_at
            }
            return jsonify(data), HTTP_200_OK
        
        
@bookmarks.delete('/<int:id>')
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()
    
    bmk = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bmk:
        data = {
            "error": "Not found"
        }
        return jsonify(data), HTTP_404_NOT_FOUND
    
    else:
        db.session.delete(bmk)
        db.session.commit()
        data = {
            "message": "bookmark with ID: {} deleted".format(bmk.id)
        }
        return jsonify(data), HTTP_200_OK
    
    

@bookmarks.get('/stat')
@jwt_required()
@swag_from('./docs/bookmarks/stats.yml')
def get_url_stat():
    current_user = get_jwt_identity()
    
    items = Bookmark.query.filter_by(user_id=current_user).all()
    
    data = []
    for item in items:
        
        links = {
            "id": item.id,
            "visits": item.visit,
            "url": item.url,
            "short_url": item.short_url
        }
        data.append(links)
    
    return jsonify({"data": data}), HTTP_200_OK