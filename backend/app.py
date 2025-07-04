from pymongo import MongoClient
from flask import Flask, redirect, url_for, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
import requests
from bson.objectid import ObjectId


static_path = os.getenv('STATIC_PATH','static')
template_path = os.getenv('TEMPLATE_PATH','templates')
#Mongo connection
mongo_uri = os.getenv("MONGO_URI")
mongo = MongoClient(mongo_uri)
db = mongo.get_default_database("mydatabase")

app = Flask(__name__)
app.secret_key = os.urandom(24)
oauth = OAuth(app)
nonce = generate_token()

oauth.register(
    name=os.getenv('OIDC_CLIENT_NAME'),
    client_id=os.getenv('OIDC_CLIENT_ID'),
    client_secret=os.getenv('OIDC_CLIENT_SECRET'),
    #server_metadata_url='http://dex:5556/.well-known/openid-configuration',
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/')
def home():
    return redirect('http://localhost:5173')

@app.route('/login')
def login():
    session['nonce'] = nonce
    redirect_uri = 'http://localhost:8000/authorize'
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/authorize')
def authorize():
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get('nonce')

    user_info = oauth.flask_app.parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
    session['user'] = user_info
    return redirect('/')

@app.route('/api/user')
def user():
    user = session.get('user')
    if user:
        return jsonify(user)
    else:
        return jsonify({'error': 'Not logged in'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/api/key')
def get_key():
    return jsonify({'apiKey': os.getenv('NYT_API_KEY')})

@app.route("/api/articles")
def get_articles():
    section = request.args.get("section", "").lower()
    user_info = session.get('user', {})
    is_moderator = user_info.get('name') == 'moderator'
    is_publisher = user_info.get('name') == 'publisher'

    query_base = {"section_name": {"$regex": section, "$options": "i"}} if section else {}
    if not (is_moderator or is_publisher):
        query_base["approved"] = True

    # First, get publisher articles without NYT web_url
    pub_query = {**query_base, "web_url": {"$exists": False}}
    publisher_articles = list(db.articles.find(pub_query).sort("cached_at", -1))

    # Then, if fewer than 9, fetch NYT articles
    nyt_articles = []
    if len(publisher_articles) < 9:
        api_key = os.getenv("NYT_API_KEY")
        if section == 'local':
            url = (
                "https://api.nytimes.com/svc/search/v2/articlesearch.json"
                "?q=Sacramento"
                f"&api-key={api_key}"
            )
        else:
            url = (
                "https://api.nytimes.com/svc/search/v2/articlesearch.json"
                f"?fq={section}"
                f"&api-key={api_key}"
            )

        try:
            response = requests.get(url)
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            for article in docs:
                article['section_name'] = section
                article['approved'] = True
                if db.articles.find_one({'web_url': article['web_url']}) is None:
                    db.articles.insert_one(article)
            nyt_articles = docs[:9 - len(publisher_articles)]
        except Exception as e:
            print("NYT API error:", e)

    combined = publisher_articles + nyt_articles
    for a in combined:
        a['_id'] = str(a['_id'])

    return jsonify({"articles": combined})


@app.route("/test-mongo")
def test_mongo():
    return jsonify({"collections": db.list_collection_names()})

from flask import request

@app.route('/api/comments', methods=['POST'])
def post_comment():
    data = request.get_json()
    article_id = data.get('article_id')
    text = data.get('text')
    parent_id = data.get('parent_id') 
    user_info = session.get('user', {})

    if not user_info:
        return jsonify({"error": "Unauthorized"}), 401

    comment = {
        "article_id": article_id,
        "text": text,
        "user": user_info.get("name"),
        "redacted_text": None,
        "parent_id": ObjectId(parent_id) if parent_id else None
    }
    db.comments.insert_one(comment)
    
    return jsonify({"message": "Comment added"}), 201


@app.route('/api/comments')
def get_comments():
    article_id = request.args.get('article_id')
    comments = list(db.comments.find({"article_id": article_id}))
    for c in comments:
        c['_id'] = str(c['_id'])
        if c.get('parent_id'):
            c['parent_id'] = str(c['parent_id'])
    return jsonify(comments)


@app.route('/api/comments', methods=['DELETE'])
def delete_comment():
    user_info = session.get('user', {})
    if not user_info:
        return jsonify({'error': 'Unauthorized'}), 401

    comment_id = request.args.get('id')
    comment = db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if comment.get('user') == user_info.get('name') or user_info.get('name') == 'moderator':
        db.comments.delete_one({"_id": ObjectId(comment_id)})
        return jsonify({'message': 'Deleted'}), 200
    else:
        return jsonify({'error': 'Forbidden'}), 403


@app.route('/api/comments', methods=['PATCH'])
def redact_comment():
    if not session.get('user', {}).get('name') == 'moderator':
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    comment_id = data.get('id')
    redacted = data.get('text')

    #redacted = '█' * len(original_text)
    db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"redacted_text": redacted}}
    )
    return jsonify({'message': 'Redacted'}), 200

@app.route('/api/articles', methods=['POST'])
def publish_article():
    user_info = session.get('user', {})
    if not user_info or user_info.get('name') != 'publisher':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['headline', 'abstract', 'section_name', 'body']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields'}), 400

    article = {
        "headline": {"main": data['headline']},
        "abstract": data['abstract'],
        "section_name": data['section_name'],
        "body": data['body'], 
        "byline": {"original": f"By {user_info.get('name')}"},
        "multimedia": data.get('multimedia', None),
        "approved": False,
    }

    db.articles.insert_one(article)
    return jsonify({"message": "Article published"}), 201

@app.route('/api/articles/pending')
def get_pending_articles():
    user_info = session.get('user', {})
    if not user_info or user_info.get('name') != 'moderator':
        return jsonify({'error': 'Unauthorized'}), 401

    articles = list(db.articles.find({"approved": False}))
    for article in articles:
        article['_id'] = str(article['_id'])
    return jsonify({"articles": articles})


@app.route('/api/article/approve', methods=['PATCH'])
def approve_article():
    user_info = session.get('user', {})
    if not user_info or user_info.get('name') != 'moderator':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    article_id = data.get('article_id')
    if not article_id:
        return jsonify({'error': 'Missing article_id'}), 400

    result = db.articles.update_one(
        {'_id': ObjectId(article_id)},
        {'$set': {'approved': True}}
    )

    if not db.articles.find_one({'_id': ObjectId(article_id)}):
        return jsonify({'error': 'Article not found'}), 404

    return jsonify({'message': 'Article approved'}), 200

# Delete article (moderator only)
@app.route('/api/article', methods=['DELETE'])
def delete_article():
    user_info = session.get('user', {})
    if not user_info or user_info.get('name') != 'moderator':
        return jsonify({'error': 'Unauthorized'}), 401
    
    article_id = request.args.get('article_id', [])
    result = db.articles.delete_one({'_id':ObjectId(article_id)})

    if not result:
        return jsonify({'error': 'Comment not found'}), 404
    
    return jsonify({'message': 'Article deleted'}), 200

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)),debug=debug_mode)