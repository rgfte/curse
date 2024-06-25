from flask import Flask
from back.ext import db, manager
import os
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://21061:mjpppv@web.edu:3306/21061_shop'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'frueywtuiy4897848734gfgryg34g'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'media', 'img2')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


from back import models, routes

db.init_app(app)
manager.init_app(app)

with app.app_context():
    inspector = inspect(db.engine)
    if 'user' not in inspector.get_table_names():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)