from app import create_app
import pytest
import config
from sqlalchemy import create_engine, text
import json
import bcrypt

database = create_engine(config.test_config["DB_URL"], encoding="utf-8", max_overflow=0)


def setup_function():
    ## create a test user
    hashed_password = bcrypt.hashpw(b"test_password", bcrypt.gensalt())

    new_users = [
        {
            "id": 1,
            "name": "유용준",
            "email": "pytest@new.com",
            "profile": "test profile",
            "hashed_password": hashed_password,
        },
        {
            "id": 2,
            "name": "김보람",
            "email": "pytest@boram.com",
            "profile": "test profile",
            "hashed_password": hashed_password,
        },
    ]

    database.execute(
        text(
            """
insert into users (id, name, email, profile, hashed_password) values (
:id, :name, :email, :profile, :hashed_password
)
"""
        ),
        new_users,
    )

    # user 2 의 twwet 생성
    database.execute(
        text(
            """
insert into tweets (user_id, tweet) values(2, "hello world")    
"""
        )
    )


def teardown_function():
    database.execute(text("set foreign_key_checks = 0"))
    database.execute(text("truncate users"))
    database.execute(text("truncate tweets"))
    database.execute(text("truncate users_follow_list"))
    database.execute(text("set foreign_key_checks = 1"))


@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config["TEST"] = True
    api = app.test_client()

    return api


def test_login(api):
    resp = api.post(
        "/login",
        data=json.dumps({"email": "pytest@new.com", "password": "test_password"}),
        content_type="application/json",
    )

    assert b"access_token" in resp.data

def test_unautorized(api):
    # access token이 없이는 401을 리턴하는지 확인
    resp = api.post('/tweet',
                    data = json.dumps({'tweet' : 'hello world'}),
                    content_type = 'application/json')
    
    assert resp.status_code == 401

    resp = api.post('/follow',
                    data = json.dumps({'follow' : 2}),
                    content_type = 'application/json')
    
    assert resp.status_code == 401

    resp = api.post('/unfollow',
                    data = json.dumps({'unfollow' : 2}),
                    content_type = 'application/json')
    
    assert resp.status_code == 401

def test_tweet(api):
    ## 로그인
    resp = api.post(
        "/login",
        data=json.dumps({"email": "pytest@new.com", "password": "test_password"}),
        content_type="application/json",
    )

    resp_json = json.loads(resp.data.decode("utf-8"))
    access_token = resp_json["access_token"]

    ## tweet
    resp = api.post(
        "/tweet",
        data=json.dumps({"tweet": "hello world"}),
        content_type="application/json",
        headers={"Authorization": access_token},
    )

    assert resp.status_code == 200

    ## tweet 확인
    resp = api.get(f"/timeline/1")
    tweets = json.loads(resp.data.decode("utf-8"))

    assert resp.status_code == 200
    assert tweets == {
        "user_id": 1,
        "timeline": [{"user_id": 1, "tweet": "hello world"}],
    }

def test_follow(api):
    # 로그인
    resp = api.post(
        "/login",
        data=json.dumps({"email": "pytest@new.com", "password": "test_password"}),
        content_type="application/json",
    )

    resp_json = json.loads(resp.data.decode("utf-8"))
    access_token = resp_json["access_token"]

    resp = api.get('/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline' : []
    }

    # follow 사용자 아이디 2 
    resp = api.post('/follow',
                    data = json.dumps({'follow' : 2}),
                    content_type = 'application/json',
                    headers = {'Authorization' : access_token}
                    )
    
    assert resp.status_code == 200

    ## 사용자 1 의 타임라인 확인
    resp = api.get('/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets   == {
        'user_id': 1,
        'timeline' : [
            {'user_id': 2,
             'tweet' : 'hello world'}
        ]
    }

def test_unfollow(api):
    # 로그인
    resp = api.post(
        "/login",
        data=json.dumps({"email": "pytest@new.com", "password": "test_password"}),
        content_type="application/json",
    )

    resp_json = json.loads(resp.data.decode("utf-8"))
    access_token = resp_json["access_token"]

    # follow 사용자 아이디 2 
    resp = api.post('/follow',
                    data = json.dumps({'follow' : 2}),
                    content_type = 'application/json',
                    headers = {'Authorization' : access_token}
                    )
    
    assert resp.status_code == 200

    ## 사용자 1 의 타임라인 확인
    resp = api.get('/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets   == {
        'user_id': 1,
        'timeline' : [
            {'user_id': 2,
             'tweet' : 'hello world'}
        ]
    }

    # unfollow
    # follow 사용자 아이디 2 
    resp = api.post('/unfollow',
                    data = json.dumps({'unfollow' : 2}),
                    content_type = 'application/json',
                    headers = {'Authorization' : access_token}
                    )
    
    assert resp.status_code == 200

    ## 사용자 1 의 타임라인 확인
    resp = api.get('/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets   == {
        'user_id': 1,
        'timeline' : []
    }