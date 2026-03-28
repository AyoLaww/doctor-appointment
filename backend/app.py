from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from models import db
from routes.auth import auth
from routes.patient import patient
from routes.doctor import doctor
import os

load_dotenv()

app = Flask(
    __name__,
    template_folder='../frontend',
    static_folder='../frontend/static'
)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(patient)
app.register_blueprint(doctor)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)