
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "<!DOCTYPE html><html><head><title>Hello</title></head><body><h1>Hello from ChatGPT</h1></body></html>"


@app.route("/about")
def about():
    return """
    <!DOCTYPE html>
    <html>
        <head><title>About</title></head>
        <body>
            <h1>What would you build if it took an evening instead of a quarter?</h1>
            <p>
            If building a product took an evening instead of a quarter, I’d build small tools that remove everyday friction: a personal dashboard that gathers scattered tasks, notes, and deadlines into one calm view. It would connect only the services people already use, highlight the next meaningful action, and let users finish workflows without navigating five apps. I’d begin with one narrow audience, interview a few people, and ship a working prototype that same evening. The goal wouldn’t be to cram in features; it would be to test whether the tool genuinely saves time. I’d make privacy, accessibility, and easy export part of the first version, not a later promise. Then I’d watch people use it, learn where they hesitate, and improve the most valuable interaction. A short build cycle makes experimentation cheap: ideas become tangible, assumptions meet real feedback, and useful projects can grow through evidence rather than long plans.
            </p>
        </body>
    </html>
    """



if __name__ == "__main__":
    app.run(debug=True)
