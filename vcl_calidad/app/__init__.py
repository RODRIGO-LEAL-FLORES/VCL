import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager  # 1. Importa LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager() # 2. Instancia global del LoginManager

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'clave_alternativa_por_si_falla_el_env'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # 3. Configura el LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'main.welcome' # Asegúrate que coincida con tu ruta de login
    
    # 4. Importa y vincula el cargador de usuario
    from app.models.usuario import Usuario 

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Importar y registrar rutas
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        db.create_all()
        
    return app