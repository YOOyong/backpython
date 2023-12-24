from flask import Flask, jsonify ,request, current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text

class CustomJSONEndocer(JSONEncoder):
    def default(self, obj):
        if isinstance(obj,set):
            return list(obj)
        return super().default(obj)


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

    if test_config is None:
        app.config.from_pyfile('config.py')
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0)
    app.database = database # Flask 객체를 넣어줌. 외부에서도 사용 가능

    @app.route('/signup', methods = ['POST'])
    def signup():
        new_user = request.json
        new_user_id = insert_user(new_user)
        created_user_id = get_user(new_user_id)
        return jsonify(created_user_id)

    @app.route('/tweet', methods = ['POST'])
    def tweet():
        new_tweet = request.json
        
        if not get_user(new_tweet['id']):
            return '없는 유저입니다.', 400

        if len(new_tweet['tweet']) > 300:
            return '300 자를 초과', 400

        insert_tweet(new_tweet)

        return '', 200
    

    @app.route('/timeline/<int:user_id>', methods = ['GET'])
    def timeline(user_id):

        timeline = get_timeline(user_id)

        return jsonify(timeline)

    @app.route('/follow', methods = ['POST'])
    def follow():
        requests = request.json

        if not get_user(requests['id']) or not get_user(requests['follow']):
            return '없는 유저입니다.' , 400

        insert_follow(requests)

        return '', 200
    
    @app.route('/unfollow', methods = ['POST'])
    def unfollow():
        requests = request.json

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


    