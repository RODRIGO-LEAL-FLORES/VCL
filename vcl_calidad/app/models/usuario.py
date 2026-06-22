from flask_login import UserMixin # 1. Importa el Mixin
from app import db 

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(25), nullable=False, unique=True)

# 2. Hereda de UserMixin
class Usuario(db.Model, UserMixin): 
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(40), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    activo = db.Column(db.Boolean, default=True)
    
    # Permisos booleanos
    puede_ver_reclamaciones = db.Column(db.Boolean, default=True)
    puede_ver_tickets = db.Column(db.Boolean, default=True)
    puede_ver_reportes = db.Column(db.Boolean, default=False)
    puede_ver_scrap = db.Column(db.Boolean, default=False)
    puede_gestionar_usuarios = db.Column(db.Boolean, default=False)

    rol = db.relationship('Rol', backref=db.backref('usuarios', lazy=True))

    # 3. Opcional: Si quieres que el usuario se bloquee si 'activo' es False
    def is_active(self):
        return self.activo