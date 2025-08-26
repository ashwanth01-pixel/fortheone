# app.py
import boto3
import subprocess
import json
import os
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect
import requests

# --------------------------
# ENSURE AWS CLI INSTALLED
# --------------------------
def ensure_aws_cli():
    aws_path = shutil.which("aws")
    if aws_path is None:
        print("AWS CLI not found. Installing...")
        try:
            subprocess.run([
                "curl", "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip", "-o", "awscliv2.zip"
            ], check=True)
            subprocess.run(["unzip", "-o", "awscliv2.zip"], check=True)
            subprocess.run(["sudo", "./aws/install"], check=True)
            aws_path = shutil.which("aws")
            print(f"AWS CLI installed successfully at {aws_path}")
        except subprocess.CalledProcessError as e:
            print("Failed to install AWS CLI:", e)
            aws_path = None
    else:
        print(f"AWS CLI already installed at {aws_path}")
    return aws_path

AWS_CLI_PATH = ensure_aws_cli()

# --------------------------
# FLASK APP
# --------------------------
app = Flask(__name__, static_folder="frontend", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# --------------------------
# DEPLOYER FRONTEND PATH
# --------------------------
deployer_frontend_path = os.path.join(os.path.dirname(__file__), "deployer_frontend")

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
# SPRING BOOT URL
# --------------------------
SPRING_BOOT_URL = os.environ.get("SPRING_BOOT_URL", "http://localhost:8081")

# --------------------------
# HISTORY FUNCTIONS
# --------------------------
def save_to_history(query, output):
    """Save history via Spring Boot service directly."""
    payload = {"query": query, "output": output}
    try:
        response = requests.post(f"{SPRING_BOOT_URL}/history/save", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error saving history:", e)
        return None

def get_history():
    """Get history from Spring Boot service directly."""
    try:
        response = requests.get(f"{SPRING_BOOT_URL}/history/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error fetching history:", e)
        return []

# --------------------------
# AWS CLIENT / BEDROCK
# --------------------------
def get_bedrock_client():
    if "aws_access_key" not in session or "aws_secret_key" not in session:
        return None
    return boto3.client(
        "bedrock-runtime",
        region_name=session.get("aws_region", "us-east-1"),
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

    if command.strip().startswith("aws ") and AWS_CLI_PATH:
        command = command.replace("aws", AWS_CLI_PATH, 1)

    aws_access = session.get("aws_access_key")
    aws_secret = session.get("aws_secret_key")
    aws_region = session.get("aws_region", "us-east-1")

    if not aws_access or not aws_secret:
        session.clear()
        return command, "AWS credentials missing. Session cleared. Please login again."

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = aws_access
    env["AWS_SECRET_ACCESS_KEY"] = aws_secret
    env["AWS_DEFAULT_REGION"] = aws_region
    env["PATH"] = f"{os.path.dirname(AWS_CLI_PATH)}:" + env.get("PATH", "")

    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, env=env)
        return command, output.decode()
    except subprocess.CalledProcessError as e:
        if "InvalidClientTokenId" in e.output.decode() or "AuthFailure" in e.output.decode():
            session.clear()
            return command, "AWS session invalid. Cleared session. Please login again."
        return command, e.output.decode()

# --------------------------
# ROUTES
# --------------------------
@app.route("/login/<path:filename>")
def login_static(filename):
    return send_from_directory("login", filename)

@app.route("/")
def index():
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
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
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
        return jsonify({"logged_in": False, "error": "AWS session missing. Please login again."})
    return jsonify({
        "logged_in": True,
        "username": session.get("aws_username", ""),
        "region": session.get("aws_region", "")
    })

@app.route("/api/ask", methods=["POST"])
def api_handler():
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
        return jsonify({"error": "AWS credentials missing. Please login again."}), 403

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
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
        return jsonify({"error": "AWS credentials missing. Please login again."}), 403

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
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
        return jsonify({"error": "AWS credentials missing. Please login again."}), 403
    history = get_history()
    return jsonify(history)

# --------------------------
# DEPLOYER STATIC
# --------------------------
@app.route("/deployer")
def deployer_index():
    if not session.get("aws_access_key") or not session.get("aws_secret_key"):
        session.clear()
        return redirect("/login")
    return send_from_directory(deployer_frontend_path, "index.html")

@app.route("/deployer/<path:filename>")
def deployer_static(filename):
    return send_from_directory(deployer_frontend_path, filename)

# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

