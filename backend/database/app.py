# database/app.py
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# MySQL URI (replace user/password/db as needed)
MYSQL_URI = os.environ.get("MYSQL_URI", "mysql+pymysql://root:password@localhost:3306/clouddeployer")
app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class UserAction(db.Model):
    __tablename__ = "user_actions"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(128))
    service = db.Column(db.String(50))
    endpoint = db.Column(db.String(128))
    action_type = db.Column(db.String(128))
    request_data = db.Column(db.Text)
    response_summary = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))

with app.app_context():
    db.create_all()

# --------------------------
# Log user action
# --------------------------
@app.route("/monitor/log", methods=["POST"])
def log_action():
    data = request.get_json() or {}

    # Mask sensitive info
    req_data = data.get("request_data", {})
    if isinstance(req_data, dict):
        for key in ["access_key", "secret_key", "token", "password"]:
            if key in req_data:
                req_data[key] = "****"

    entry = UserAction(
        user_id=data.get("user_id", "anonymous"),
        service=data.get("service", "unknown"),
        endpoint=data.get("endpoint", ""),
        action_type=data.get("action_type", ""),
        request_data=str(req_data),
        response_summary=str(data.get("response_summary", "")),
        ip_address=data.get("ip_address", ""),
        user_agent=data.get("user_agent", "")
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"success": True})

# --------------------------
# Display logs
# --------------------------
@app.route("/monitor")
def show_logs():
    logs = UserAction.query.order_by(UserAction.timestamp.desc()).limit(200).all()
    html = """
    <html>
    <head><title>User Activity Logs</title></head>
    <body>
    <h2>User Activity Logs</h2>
    <table border="1" cellpadding="5" cellspacing="0">
    <tr>
        <th>ID</th>
        <th>Timestamp</th>
        <th>User</th>
        <th>Service</th>
        <th>Endpoint</th>
        <th>Action</th>
        <th>Request Data</th>
        <th>Response Summary</th>
        <th>IP</th>
        <th>User Agent</th>
    </tr>
    {% for log in logs %}
    <tr>
        <td>{{ log.id }}</td>
        <td>{{ log.timestamp }}</td>
        <td>{{ log.user_id }}</td>
        <td>{{ log.service }}</td>
        <td>{{ log.endpoint }}</td>
        <td>{{ log.action_type }}</td>
        <td>{{ log.request_data }}</td>
        <td>{{ log.response_summary }}</td>
        <td>{{ log.ip_address }}</td>
        <td>{{ log.user_agent }}</td>
    </tr>
    {% endfor %}
    </table>
    </body>
    </html>
    """
    return render_template_string(html, logs=logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)

