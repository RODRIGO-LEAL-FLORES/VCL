import os
from datetime import timedelta  # ← Agrega este import
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Sesión por inactividad ─────────────────────────────────────────
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=0.5)
    app.config['SESSION_PERMANENT'] = True
    # ──────────────────────────────────────────────────────────────────
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.welcome'
    
    from app.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        db.create_all()
        
    return app