from typing import Any
from flask import Flask, jsonify ,request
from flask.json import JSONEncoder

app = Flask(__name__) # flask의 웹 애플리케이션
app.id_count = 1
app.users = {}
app.tweets = []


class CustomJSONEncoder(JSONEncoder):
    """
    default json encoder는 set을 json으로 변환할 수 없음.
    custom encoder 를 작성하여 set 을 list로 변환한다.
    """
    def default(self,obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.route("/ping", methods = ['GET']) # flask는 route decorator로 endpoint 를 등록함
def ping():
    return 'pong'


@app.route("/signup", methods = ['POST'])
def sign_up():
    new_user = request.json
    new_user['id'] = app.id_count
    app.users[app.id_count] = new_user
    app.id_count  += 1

    return jsonify(new_user)

@app.route('/tweet', methods = ['POST'])
def tweet():
    new_tweet = request.json

    if int(new_tweet['id']) not in app.users:
        return '사용자 없음', 400 

    if len(new_tweet['tweet']) > 300:
        return '300 자를 초과', 400

    app.tweets.append({
        "user_id" : new_tweet['id'],
        "tweet" : new_tweet['tweet']
    })

    return '', 200


@app.route('/follow', methods = ['POST'])
def follow():
    payload = request.json

    req_user_id = int(payload["id"])
    followed_user_id = int(payload["follow"])

    if req_user_id not in app.users or followed_user_id not in app.users:
        return "없는 유저입니다.", 400
    
    user : dict= app.users[req_user_id]
    user.setdefault('follow', set()).add(followed_user_id)

    return jsonify(user)


@app.route('/unfollow', methods = ['POST'])
def unfollow():
    payload = request.json

    req_user_id = int(payload["id"])
    unfollowed_user_id = int(payload["follow"])

    if req_user_id not in app.users or unfollowed_user_id not in app.users:
        return "없는 유저입니다.", 400
    
    user : dict = app.users[req_user_id]
    user.setdefault('follow', set()).discard(unfollowed_user_id)

    return jsonify(user)


@app.route('/timeline/<int:user_id>', methods = ['GET'])
def timeline(user_id):
    if user_id not in app.users:
        return '유저 없음', 400
    
    user = app.users[user_id]
    follow_list: set = user.get('follow', set()) # dict key를 찾는데 없으면 empty set
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    response = {
        "user_id" : user_id,
        "timeline" : timeline
    }

    return jsonify(response)