from flask import Flask,jsonify
from worker import predict


app = Flask(__name__)



@app.route("/status")
def status():
    return jsonify(status=200,ok='Ok')


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=4000)
    predict()