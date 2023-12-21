from flask import Flask, jsonify ,request
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text

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
        new_user_id = app.database.execute(text("""
                            insert into users (
                                name, email, profile, hashed_password
                            ) values (
                                :name,
                                :email,
                                :profile,
                                :password
                            )"""), new_user).lastrowid
        
        row = app.database.execute(text("""
        select * from users
        where id = :id
        """), {'id' : new_user_id}).fetchone()


        created_user_id = {
            'id' : row['id'],
            'name' : row['name'],
            'email' : row['email'],
            'profile' : row['profile']
        } if row else None

        return jsonify(created_user_id)

    @app.route('/tweet', methods = ['POST'])
    def tweet():
        new_tweet = request.json
        
        if not app.database.execute(text("select * from users where id = :id"),\
                                     {'id': new_tweet['id']}).fetchone():
            return '없는 유저입니다.' , 400

        if len(new_tweet['tweet']) > 300:
            return '300 자를 초과', 400


        app.database.execute(text("""
            insert into tweets (user_id, tweet)
                values (:id, :tweet)                           
        """), new_tweet)

        return '', 200
    

    @app.route('/timeline/<int:user_id>', methods = ['GET'])
    def timeline(user_id):
        rows = app.database.execute(text("""
            select t.user_id, t.tweet
            from tweets t
            left join users_follow_list ufl on ufl.user_id = :id
            where t.user_id = :id
            or t.user_id = ufl.follow_user_id
        """), {'id' : user_id}).fetchall()

        timeline = [
            {
                'user_id' : row['user_id'],
                'tweet' : row['tweet']
            } for row in rows
        ]

        return jsonify(timeline)

    @app.route('/follow', methods = ['POST'])
    def follow():
        following = request.json

        if not app.database.execute(text("select * from users where id = :id"),\
                                     {'id': following['id']}).fetchone() \
            or not app.database.execute(text("select * from users where id = :id"),{'id' : following['follow']}).fetchone():
            return '없는 유저입니다.' , 400

        app.database.execute(text("""
            insert into users_follow_list (user_id, follow_user_id)
            values(:id, :follow)
            """
        ), following)


        return '', 200
    
    @app.route('/unfollow', methods = ['POST'])
    def unfollow():
        requests = request.json

        if not app.database.execute(text("select * from users where id = :id"),\
                                     {'id': requests['id']}).fetchone() \
            or not app.database.execute(text("select * from users where id = :id"),{'id' : requests['unfollow']}).fetchone():
            return '없는 유저입니다.' , 400

        app.database.execute(text("""
            delete from users_follow_list
            where user_id = :id
            and follow_user_id = :unfollow
            """
        ), requests)


        return '', 200


    return app


    