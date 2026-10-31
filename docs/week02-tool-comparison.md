# Week 2 — AI Tool Comparison

## The requirement
A contact form for my Flask app with name, email and message. If a field is empty or the email looks wrong, the form must show an error and not go through. If everything is fine, the user sees a confirmation page.

## Prompts used
### Claude
```
Write a contact form for a Flask 3.x application. Give me templates/contact.html and the route in app.py. Validate name, email and message on the server — not only in the browser. Reject an empty field and a malformed email address, re-rendering the form with an error message and an HTTP 400. On success show a confirmation page. Do not use any package outside Flask and the Python standard library. Output each file separately with its full path.
```
### ChatGPT
```
Write a contact form for a Flask 3.x application. Give me templates/contact.html and the route in app.py. Validate name, email and message on the server — not only in the browser. Reject an empty field and a malformed email address, re-rendering the form with an error message and an HTTP 400. On success show a confirmation page. Do not use any package outside Flask and the Python standard library. Output each file separately with its full path.
```

## Scores
Scale: 1 (poor) to 5 (excellent).

| Criterion | Claude | ChatGPT |
|---|---|---|
| Correctness | 4 | 4 |
| Code quality | 4 | 3 |
| Completeness | 4 | 3 |
| Security | 3 | 2 |

## What each got wrong
**Claude.** The thank-you page looks plain next to the form.

**ChatGPT.** When something is wrong it only shows one general message ("All fields are required"), so you can't see which field to fix. It also puts no limit on how much text you can type, and its thank-you page is plain and doesn't greet you by name.

## Which I kept, and why
I kept Claude. The deciding criterion was completeness: when I submitted the form wrong, it showed a red message under each field that needed fixing and kept what I had already typed, and the thank-you page greeted me by name. ChatGPT's single general error was less helpful. Correctness was a tie, because both stopped empty fields and bad emails.
