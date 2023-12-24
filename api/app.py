from flask import Flask, jsonify ,request, current_app, Response, g
from flask.json import JSONEncoder
from functools import wraps
from sqlalchemy import create_engine, text
import bcrypt
import jwt
from datetime import datetime , timedelta
from flask_cors import CORS

class CustomJSONEndocer(JSONEncoder):
    def default(self, obj):
        if isinstance(obj,set):
            return list(obj)
        return super().default(obj)

def hash_password(password):
    return bcrypt.hashpw(password.encode('UTF-8'),bcrypt.gensalt())


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                return Response(status=401)

            user_id = payload['user_id']
            g.user_id = user_id #g 는 flask의 전역공간.
            g.user = get_user(user_id) if user_id else None
        else:
            return Response(status = 401)
            
        return func(*args, **kwargs)

    return wrapper

def get_user(user_id):
    user = current_app.database.execute(text("""
        select id, name, email, profile
        from users
        where id = :user_id
    """),{'user_id':user_id}).fetchone()

    return {'id' : user['id'],
            'name': user['name'],
            'email': user['email'],
            'profile': user['profile']
            } if user else None

def get_user_id_password(email):
    row = current_app.database.execute(text("""
    select id, hashed_password
    from users
    where email = :email
    """), {'email' : email}).fetchone()

    return { 'id' : row['id'], 'hashed_password' : row['hashed_password']} if row else None


def insert_tweet(new_tweet):
    return current_app.database.execute(text("""
    insert into tweets (user_id, tweet)
    values (:id, :tweet)   
    """),new_tweet).rowcount

def insert_user(new_user):
    return current_app.database.execute(text("""
    insert into users (name, email, profile, hashed_password)
    values(:name, :email, :profile ,:password)
    """), new_user).lastrowid

def insert_follow(user_follow):
    return current_app.database.execute(text("""
    insert into users_follow_list(user_id, follow_user_id)
    values(:id , :follow)
    """),user_follow).rowcount


def delete_follow(user_unfollow):
    return current_app.database.execute(text("""
    delete from users_follow_list
    where user_id = :id
    and follow_user_id = :unfollow
    """), user_unfollow).rowcount


def get_timeline(user_id):
    timeline = current_app.database.execute(text("""
    select t.user_id, t.tweet
    from tweets t
    left join users_follow_list ufl on ufl.user_id = :user_id
    where t.user_id = :user_id
    or t.user_id = ufl.follow_user_id
    """),{'user_id' : user_id}).fetchall()

    return [{
        'user_id': tweet['user_id'],
        'tweet' : tweet['tweet']
    } for tweet in timeline]


# 이 안에 엔드포인트들을 구현한다.
# create_app을 팩토리함수로 자동으로 인식하여 flask를 실행시킨다.
def create_app(test_config = None):
    app = Flask(__name__)

    CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py')
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0)
    app.database = database # Flask 객체를 넣어줌. 외부에서도 사용 가능

    @app.route('/signup', methods = ['POST'])
    def signup():
        new_user = request.json
        # password 암호화
        new_user['password'] = hash_password(new_user['password'])

        new_user_id = insert_user(new_user)
        new_user_info = get_user(new_user_id)
        return jsonify(new_user_info)

    @app.route('/login', methods =['POST']) 
    def login():
        requests = request.json

        # get password
        user = get_user_id_password(requests['email'])

        if user and bcrypt.checkpw(requests['password'].encode('UTF-8'), user['hashed_password'].encode('UTF-8')):
            user_id = user['id']
            payload = {
                'user_id' : user_id,
                'exp' : datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)
            }

            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')
            return jsonify({
                'access_token': token
            })

        else: return '', 401





    @app.route('/tweet', methods = ['POST'])
    @login_required
    def tweet():
        new_tweet = request.json
        new_tweet['id'] = g.user_id

        if not get_user(new_tweet['id']):
            return '없는 유저입니다.', 400

        if len(new_tweet['tweet']) > 300:
            return '300 자를 초과', 400

        insert_tweet(new_tweet)

        return '', 200
    

    @app.route('/timeline/<int:user_id>', methods = ['GET'])
    def timeline(user_id):
        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })

    @app.route('/timeline', methods = ['GET'])
    @login_required
    def user_timeline():
        user_id = g.user_id
        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })

    @app.route('/follow', methods = ['POST'])
    @login_required
    def follow():
        requests = request.json
        requests['id'] = g.user_id

        if not get_user(requests['id']) or not get_user(requests['follow']):
            return '없는 유저입니다.' , 400

        insert_follow(requests)

        return '', 200
    
    @app.route('/unfollow', methods = ['POST'])
    @login_required
    def unfollow():
        requests = request.json
        requests['id'] = g.user_id

        if not get_user(requests['id']) or not get_user(requests['unfollow']):
            return '없는 유저입니다.' , 400

        app.database.execute(text("""
            delete from users_follow_list
            where user_id = :id
            and follow_user_id = :unfollow
            """
        ), requests)

        delete_follow(requests)

        return '', 200

    return app


    