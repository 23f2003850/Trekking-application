from flask import Flask
from models import db, User
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super_secret_key_for_flask' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all() 
    
    admin_exists = User.query.filter_by(role='admin').first()
    if not admin_exists:
        hashed_password = generate_password_hash('Founder123') 
        default_admin = User(
            name='Founder',
            email='Founder@trek.com',
            password=hashed_password,
            role='admin',
            is_active=True,
            is_approved=True 
        )
        db.session.add(default_admin)
        db.session.commit()
        print("Database initialized. Admin: Founder@trek.com / Founder123")

import controllers
controllers.setup_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
