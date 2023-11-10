
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
CORS(app, resource={r'*': {'origins': '*'}})

text_data = []


@app.route("/text", methods=['GET'])
def getText():
    text = ""
    if len(text_data) > 0:
        text = text_data.pop(0)
    return text

@app.route("/text", methods=['POST'])
def postText():
    text_data.append(request.data)
    return ""

app.run(host="172.21.119.171", port="8888", debug=True)