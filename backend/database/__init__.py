from flask import Flask
from .models import db

def init_db(app: Flask, mysql_uri=None):
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_uri or "mysql+pymysql://root:password@localhost:3306/clouddeployer"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

