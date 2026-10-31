import re

from flask import Flask, render_template, request

app = Flask(__name__)

# Deliberately simple: something@something.tld, no spaces, a single "@".
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_NAME = 100
MAX_EMAIL = 254
MAX_MESSAGE = 5000


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
            If building a product took an evening instead of a quarter, I’d build small tools that remove everyday friction: a personal dashboard that gathers scattered tasks, notes,and deadlines into one calm view. It would connect only the services people already use, highlight the next meaningful action, and let users finish workflows without navigating five apps. I’d begin with one narrow audience, interview a few people, and ship a working prototype that same evening. The goal wouldn’t be to cram in features; it would be to test whetherthe tool genuinely saves time. I’d make privacy, accessibility, and easy export part of the first version, not a later promise. Then I’d watch people use it, learn where they hesitate, and improve the most valuable interaction. A short build cycle makes experimentation cheap: ideas become tangible, assumptions meet real feedback, and useful projects can grow through evidence rather than long plans.
            </p>
        </body>
    </html>
    """


def validate_contact(form):
    """Return a dict of {field: error message}. Empty dict means valid."""
    errors = {}

    if not form["name"]:
        errors["name"] = "Please enter your name."
    elif len(form["name"]) > MAX_NAME:
        errors["name"] = f"Name must be at most {MAX_NAME} characters."

    if not form["email"]:
        errors["email"] = "Please enter your email address."
    elif len(form["email"]) > MAX_EMAIL or not EMAIL_RE.match(form["email"]):
        errors["email"] = "Please enter a valid email address."

    if not form["message"]:
        errors["message"] = "Please enter a message."
    elif len(form["message"]) > MAX_MESSAGE:
        errors["message"] = f"Message must be at most {MAX_MESSAGE} characters."

    return errors


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html", form={}, errors={})

    form = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "message": request.form.get("message", "").strip(),
    }

    errors = validate_contact(form)
    if errors:
        return render_template("contact.html", form=form, errors=errors), 400

    # TODO: do something with the message (send an email, save to a DB, ...).
    # For now it is just logged.
    app.logger.info("Contact form from %s <%s>: %s", form["name"], form["email"], form["message"])

    return render_template("contact_success.html", name=form["name"])


if __name__ == "__main__":
    app.run(debug=True)
