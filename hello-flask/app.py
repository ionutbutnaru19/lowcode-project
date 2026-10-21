
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "<!DOCTYPE html><html><head><title>Hello</title></head><body><h1>Hello from ChatGPT</h1></body></html>"


if __name__ == "__main__":
    app.run(debug=True)
