import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from textwrap import dedent
from flask import Blueprint, request, jsonify, session
import boto3

deployer_bp = Blueprint("deployer_bp", __name__, url_prefix="/deployer-api")

# -------- Utils --------
def _aws_clients():
    if "aws_access_key" not in session:
        return None, None, None
    region = session["aws_region"]
    ak = session["aws_access_key"]
    sk = session["aws_secret_key"]
    ecr = boto3.client("ecr", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
    sts = boto3.client("sts", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
    iam = boto3.client("iam", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
    return ecr, sts, iam

def _docker(*args, input_bytes=None, env=None):
    return subprocess.run(["docker", *args], input=input_bytes, capture_output=True, env=env)

def _kubectl_apply(yaml_text: str, env=None):
    p = subprocess.run(["kubectl", "apply", "-f", "-"], input=yaml_text.encode(), capture_output=True, env=env)
    return p

def _compile_check(code: str):
    try:
        compile(code, "app.py", "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

def _sanitize_name(name: str, default="flaskapp"):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or default

def _build_temp_project(app_code: str, app_module: str = "app"):
    tmpdir = tempfile.mkdtemp(prefix="deployer_")
    # Write app.py
    with open(os.path.join(tmpdir, "app.py"), "w") as f:
        f.write(app_code)
    # Minimal wsgi if user code exposes "app"
    with open(os.path.join(tmpdir, "wsgi.py"), "w") as f:
        f.write(dedent(f"""
        from {app_module} import app as application
        if __name__ == "__main__":
            application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
        """))
    # Requirements
    with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
        f.write("Flask==3.0.3\ngunicorn==22.0.0\n")
    # Dockerfile
    with open(os.path.join(tmpdir, "Dockerfile"), "w") as f:
        f.write(dedent("""
        FROM python:3.11-slim
        WORKDIR /app
        ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
        RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .
        EXPOSE 8080
        CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8080", "wsgi:application"]
        """))
    return tmpdir

def _ensure_ecr_repo(ecr, repo_name: str):
    try:
        ecr.describe_repositories(repositoryNames=[repo_name])
    except ecr.exceptions.RepositoryNotFoundException:
        ecr.create_repository(repositoryName=repo_name)

def _ecr_login(ecr, registry_uri: str, env=None):
    # Use ECR authorization token
    auth = ecr.get_authorization_token()
    token = auth["authorizationData"][0]["authorizationToken"]
    proxy_endpoint = auth["authorizationData"][0]["proxyEndpoint"]
    user_pass = base64.b64decode(token).decode()  # "AWS:<password>"
    username, password = user_pass.split(":")
    p = _docker("login", "-u", username, "--password-stdin", proxy_endpoint, input_bytes=password.encode(), env=env)
    return p

# -------- API --------
@deployer_bp.route("/validate", methods=["POST"])
def validate_code():
    if "aws_access_key" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 403

    data = request.get_json()
    code = data.get("code", "")
    app_name = _sanitize_name(data.get("app_name", "flaskapp"))
    if not code.strip():
        return jsonify({"success": False, "error": "Code empty"}), 400

    ok, err = _compile_check(code)
    if not ok:
        return jsonify({"success": False, "valid": False, "reason": err})

    # Heuristic: ensure `app = Flask(__name__)` or application named "app"
    if "Flask(" not in code or "app =" not in code:
        return jsonify({"success": False, "valid": False, "reason": "Flask app object not detected as 'app'."})

    return jsonify({"success": True, "valid": True, "app_name": app_name})

@deployer_bp.route("/deploy", methods=["POST"])
def deploy():
    if "aws_access_key" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 403

    ecr, sts, _ = _aws_clients()
    if not ecr or not sts:
        return jsonify({"success": False, "error": "AWS client init failed"}), 400

    data = request.get_json()
    code = data.get("code", "")
    app_name = _sanitize_name(data.get("app_name", "flaskapp"))
    k8s_kind = data.get("k8s_kind", "Deployment")  # Deployment|ReplicaSet
    replicas = int(data.get("replicas", 2))
    service_type = data.get("service_type", "ClusterIP")  # ClusterIP|NodePort|LoadBalancer
    container_port = int(data.get("container_port", 8080))
    namespace = data.get("namespace", "default")

    ok, err = _compile_check(code)
    if not ok:
        return jsonify({"success": False, "error": f"Validation failed: {err}"}), 400

    tmpdir = _build_temp_project(code, app_module="app")
    logs = []

    try:
        # Build local image
        local_tag = f"{app_name}:latest"
        p = _docker("build", "-t", local_tag, tmpdir)
        logs.append(p.stdout.decode() + p.stderr.decode())
        if p.returncode != 0:
            return jsonify({"success": False, "error": "Docker build failed", "logs": logs}), 400

        # AWS account/region
        account_id = session.get("aws_account_id")
        region = session.get("aws_region")
        if not account_id:
            ident = sts.get_caller_identity()
            account_id = ident.get("Account")
            session["aws_account_id"] = account_id

        registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        repo_name = app_name
        _ensure_ecr_repo(ecr, repo_name)

        # ECR login
        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = session["aws_access_key"]
        env["AWS_SECRET_ACCESS_KEY"] = session["aws_secret_key"]
        env["AWS_DEFAULT_REGION"] = region

        p = _ecr_login(ecr, registry, env=env)
        logs.append(p.stdout.decode() + p.stderr.decode())
        if p.returncode != 0:
            return jsonify({"success": False, "error": "ECR login failed", "logs": logs}), 400

        # Tag + Push
        remote_tag = f"{registry}/{repo_name}:latest"
        p = _docker("tag", local_tag, remote_tag, env=env)
        logs.append(p.stdout.decode() + p.stderr.decode())
        if p.returncode != 0:
            return jsonify({"success": False, "error": "Docker tag failed", "logs": logs}), 400

        p = _docker("push", remote_tag, env=env)
        logs.append(p.stdout.decode() + p.stderr.decode())
        if p.returncode != 0:
            return jsonify({"success": False, "error": "Docker push failed", "logs": logs}), 400

        # Kubernetes manifests
        app_label = f"app: {app_name}"
        image = remote_tag

        if k8s_kind not in ["Deployment", "ReplicaSet"]:
            k8s_kind = "Deployment"

        workload = dedent(f"""
        apiVersion: apps/v1
        kind: {k8s_kind}
        metadata:
          name: {app_name}
          namespace: {namespace}
        spec:
          replicas: {replicas}
          selector:
            matchLabels:
              app: {app_name}
          template:
            metadata:
              labels:
                app: {app_name}
            spec:
              containers:
                - name: {app_name}
                  image: {image}
                  imagePullPolicy: IfNotPresent
                  ports:
                    - containerPort: {container_port}
        """).strip()

        if service_type not in ["ClusterIP", "NodePort", "LoadBalancer"]:
            service_type = "ClusterIP"

        service = dedent(f"""
        apiVersion: v1
        kind: Service
        metadata:
          name: {app_name}
          namespace: {namespace}
        spec:
          type: {service_type}
          selector:
            app: {app_name}
          ports:
            - port: 80
              targetPort: {container_port}
        """).strip()

        manifest_all = workload + "\n---\n" + service + "\n"

        # Apply to Kubernetes
        p = _kubectl_apply(manifest_all, env=env)
        logs.append(p.stdout.decode() + p.stderr.decode())
        if p.returncode != 0:
            return jsonify({"success": False, "error": "kubectl apply failed", "logs": logs, "manifest": manifest_all}), 400

        return jsonify({
            "success": True,
            "image": image,
            "manifest": manifest_all,
            "logs": logs,
            "service_url_hint": f"Service {app_name} ({service_type}). For LoadBalancer, wait for EXTERNAL-IP."
        })

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

