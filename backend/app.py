# mainapp.py
import boto3
import subprocess
import json
import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect
import shutil
import shlex

# --------------------------
# ENSURE AWS CLI INSTALLED
# --------------------------
def ensure_aws_cli():
    aws_path = "/usr/local/bin/aws"
    if shutil.which("aws") is None:
        print("AWS CLI not found. Installing...")
        try:
            subprocess.run([
                "curl", "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip", "-o", "awscliv2.zip"
            ], check=True)
            subprocess.run(["unzip", "-o", "awscliv2.zip"], check=True)
            subprocess.run(["sudo", "./aws/install"], check=True)
            print("AWS CLI installed successfully.")
        except subprocess.CalledProcessError as e:
            print("Failed to install AWS CLI:", e)
    else:
        print(f"AWS CLI already installed at {aws_path}")

ensure_aws_cli()

# --------------------------
# APP
# --------------------------
app = Flask(__name__, static_folder="frontend", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# --------------------------
# DEPLOYER BLUEPRINT
# --------------------------
try:
    from deployer.backend import deployer_bp
    app.register_blueprint(deployer_bp)
    print("✅ Successfully registered 'deployer_bp' blueprint.")
except Exception as e:
    print(f"⚠️ Could not register 'deployer_bp' blueprint. Error: {e}")

# --------------------------
# DB INIT
# --------------------------
def init_db():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            output TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_to_history(query, output):
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (query, output, timestamp) VALUES (?, ?, ?)",
        (query, output, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT query, output, timestamp FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"query": r[0], "output": r[1], "timestamp": r[2]} for r in rows]

# --------------------------
# AWS CLIENT / BEDROCK
# --------------------------
def get_bedrock_client():
    if "aws_access_key" not in session:
        return None
    return boto3.client(
        "bedrock-runtime",
        region_name=session["aws_region"],
        aws_access_key_id=session["aws_access_key"],
        aws_secret_access_key=session["aws_secret_key"],
    )

def ask_bedrock(prompt):
    bedrock_runtime = get_bedrock_client()
    if not bedrock_runtime:
        return "Not logged in to AWS."
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.7,
    }
    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"].strip()

# --------------------------
# RUN AWS CLI COMMAND SAFELY
# --------------------------
def run_command_from_claude(prompt):
    command_prompt = (
        f'You are an expert in AWS CLI. Return a valid, complete AWS CLI command for: "{prompt}". '
        f'Do not include explanations or placeholders. Default region: {session.get("aws_region", "us-east-1")}'
    )
    command = ask_bedrock(command_prompt)

    if command.strip().startswith("aws "):
        command = command.replace("aws", AWS_CLI_PATH, 1)

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = session["aws_access_key"]
    env["AWS_SECRET_ACCESS_KEY"] = session["aws_secret_key"]
    env["AWS_DEFAULT_REGION"] = session["aws_region"]
    env["PATH"] = "/usr/local/bin:" + env.get("PATH", "")

    try:
        output = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT,
            env=env
        )
        return command, output.decode()
    except subprocess.CalledProcessError as e:
        return command, e.output.decode()



# --------------------------
# ROUTES
# --------------------------
@app.route("/login/<path:filename>")
def login_static(filename):
    return send_from_directory("login", filename)

@app.route("/")
def index():
    if "aws_access_key" not in session:
        return redirect("/login")
    return send_from_directory(app.static_folder, "index.html")

@app.route("/login")
def login_page():
    return send_from_directory("login", "login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    access_key = data.get("access_key")
    secret_key = data.get("secret_key")
    region = data.get("region")

    try:
        sts_client = boto3.client(
            "sts",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        identity = sts_client.get_caller_identity()
        session["aws_access_key"] = access_key
        session["aws_secret_key"] = secret_key
        session["aws_region"] = region
        session["aws_username"] = identity.get("Arn", "Unknown").split("/")[-1]
        session["aws_account_id"] = identity.get("Account", "")
        return jsonify({"success": True, "username": session["aws_username"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/user", methods=["GET"])
def api_user():
    if "aws_username" in session:
        return jsonify({
            "logged_in": True,
            "username": session["aws_username"],
            "region": session.get("aws_region", "")
        })
    return jsonify({"logged_in": False})

@app.route("/api/ask", methods=["POST"])
def api_handler():
    if "aws_access_key" not in session:
        return jsonify({"error": "Not logged in"}), 403
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    action = query.lower()
    if any(word in action for word in ["create", "delete", "modify", "update"]):
        return jsonify({"confirmation_needed": True, "query": query})
    command, output = run_command_from_claude(query)
    formatted_output = f"Command: {command}\n{output.strip()}"
    save_to_history(query, formatted_output)
    return jsonify({"confirmation_needed": False, "output": formatted_output})

@app.route("/api/confirm", methods=["POST"])
def api_confirm():
    if "aws_access_key" not in session:
        return jsonify({"error": "Not logged in"}), 403
    data = request.get_json()
    query = data.get("query")
    decision = data.get("decision")
    if decision.lower() != "accept":
        return jsonify({"output": "Action declined."})
    command, output = run_command_from_claude(query)
    formatted_output = f"Command: {command}\n{output.strip()}"
    save_to_history(query, formatted_output)
    return jsonify({"output": formatted_output})

@app.route("/api/history", methods=["GET"])
def api_history():
    if "aws_access_key" not in session:
        return jsonify({"error": "Not logged in"}), 403
    return jsonify(get_history())

# --------------------------
# DEPLOYER STATIC
# --------------------------
@app.route("/deployer")
def deployer_index():
    if "aws_access_key" not in session:
        return redirect("/login")
    return send_from_directory("deployer_frontend", "index.html")

@app.route("/deployer/<path:filename>")
def deployer_static(filename):
    return send_from_directory("deployer_frontend", filename)

# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
