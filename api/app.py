from flask import Flask

app = Flask(__name__) # flask의 웹 애플리케이션

@app.route("/ping", methods = ['GET'])
def ping():
    return 'pong'


