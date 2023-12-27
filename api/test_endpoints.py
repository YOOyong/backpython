from app import create_app
import pytest
import config
from sqlalchemy import create_engine, text
import json
import bcrypt

database = create_engine(config.test_config["DB_URL"], encoding="utf-8", max_overflow=0)


@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config["TEST"] = True
    api = app.test_client()

    return api


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


def setup_function():
    ## create a test user
    hashed_password = bcrypt.hashpw(b"test_password", bcrypt.gensalt())

    new_user = {
        "id": 1,
        "name": "유용준",
        "email": "pytest@new.com",
        "profile": "test profile",
        "hashed_password": hashed_password,
    }

    database.execute(
        text(
            """
insert into users (id, name, email, profile, hashed_password) values (
:id, :name, :email, :profile, :hashed_password
)
"""),
        new_user,
    )


def teardown_function():
    database.execute(text("set foreign_key_checks = 0"))
    database.execute(text("truncate users"))
    database.execute(text("truncate tweets"))
    database.execute(text("truncate users_follow_list"))
    database.execute(text("set foreign_key_checks = 1"))
