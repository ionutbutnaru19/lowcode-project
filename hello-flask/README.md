# Hello Flask

A minimal web application built with Flask 3.x and Python. It serves a single route (`/`) that displays a simple HTML page saying **"Hello from ChatGPT"**.

## Features

- Built with Flask 3.x.
- Serves a single route at `/`.
- Returns a simple HTML page.
- Uses a pinned dependency version for reproducible installation.

## Requirements

- Python 3.10 or later.
- pip (Python package installer).

## Project Structure

```text
hello-flask/
├── app.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone or navigate to the project

Open a terminal and navigate to the project directory:

```bash
cd ~/lowcode-project/hello-flask
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows — Git Bash:**

```bash
source .venv/Scripts/activate
```

**Windows — Command Prompt:**

```bat
.venv\Scripts\activate.bat
```

**Windows — PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Running the Application

Start the Flask development server:

```bash
python app.py
```

By default, the application runs at:

http://127.0.0.1:5000/

Open this URL in your web browser to see the greeting.

## Available Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Returns an HTML page displaying "Hello from ChatGPT". |

## Stopping the Application

Press `Ctrl+C` in the terminal where the server is running.

## Development Notes

The application runs in Flask debug mode for local development. Debug mode should be disabled when deploying to production, and a production-ready WSGI server should be used.

## License

This project is provided for learning and demonstration purposes.
