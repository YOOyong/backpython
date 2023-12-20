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

    return app


