import jwt
from flask import request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from functools import wraps

class CustomJSONEndocer(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
    
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_token = request.headers.get("Authorization")
        if access_token is not None:
            try:
                payload = jwt.decode(
                    access_token, current_app.config["JWT_SECRET_KEY"], "HS256"
                )
            except jwt.InvalidTokenError:
                return Response(status=401)

            user_id = payload["user_id"]
            g.user_id = user_id  # g 는 flask의 전역공간.
        else:
            return Response(status=401)

        return func(*args, **kwargs)

    return wrapper


def create_endpoints(app, services):
    app.json_encoder = CustomJSONEndocer

    user_service = services.user_service
    tweet_service = services.tweet_service

    @app.route('/ping', methods = ['POST'])
    def ping():
        return 'pong'
    
    @app.route('/signup', methods = ['POST'])
    def signup():
        new_user = request.json
        new_user_id = user_service.create_new_user(new_user)
        new_user = user_service.get_user(new_user_id)

        return jsonify(new_user)
    

    @app.route('/login', methods = ['POST'])
    def login():
        credential = request.json
        authorized : bool = user_service.login(credential)

        if authorized:
            user_credential = user_service.get_user_id_and_password(credential['email'])
            user_id = user_credential['id']
            token = user_service.generate_access_token(user_id)

            return jsonify({
                'user_id': user_id,
                'access_token' : token
            })
        else:
            return '', 401
        
    @app.route('/tweet', methods = ['POST'])
    @login_required
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']
        user_id = g.user_id


        result = tweet_service.tweet(user_id, tweet)

        if result is None:
            return '300 자를 초과했습니다.', 400
        
        return '',200
    

    @app.route('/follow', methods = ['POST'])
    @login_required
    def follow():
        payload = request.json
        user_id = g.user_id
        followee = payload['follow']

        result = user_service.follow(user_id,followee)

        return '', 200
    

    @app.route('/unfollow', methods = ['POST'])
    @login_required
    def unfollow():
        payload = request.json
        user_id = g.user_id
        followee = payload['unfollow']

        result = user_service.unfollow(user_id,followee)

        return '', 200
    
    @app.route('/timeline/<int:user_id>', methods = ['GET'])
    def timeline(user_id):
        timeline = tweet_service.timeline(user_id)

        return jsonify({
            'user_id' : user_id,
            'timeline' : timeline
        })
    

    @app.route('/timeline', methods = ['GET'])
    @login_required
    def user_timeline():
        timeline = tweet_service.timeline(g.user_id)

        return jsonify({
            'user_id' : g.user_id,
            'timeline' : timeline
        })