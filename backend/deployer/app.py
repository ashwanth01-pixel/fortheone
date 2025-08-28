# app.py
from flask import Flask
from deployer import backend  # assuming backend.py is inside "deployer" folder

app = Flask(__name__)
app.register_blueprint(backend.deployer_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

