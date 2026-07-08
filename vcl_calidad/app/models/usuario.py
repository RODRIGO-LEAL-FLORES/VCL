from flask_login import UserMixin # 1. Importa el Mixin
from app import db 
from app.models.tickect_models.T_models import Area

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
    id_area = db.Column(db.Integer, db.ForeignKey('areas.id_area'), nullable=True)
    
    # Permisos booleanos
    puede_ver_reclamaciones = db.Column(db.Boolean, default=True)
    puede_ver_tickets = db.Column(db.Boolean, default=True)
    puede_ver_reportes = db.Column(db.Boolean, default=False)
    puede_ver_scrap = db.Column(db.Boolean, default=False)
    puede_gestionar_usuarios = db.Column(db.Boolean, default=False)

    rol = db.relationship('Rol', backref=db.backref('usuarios', lazy=True))
    area = db.relationship('Area', backref=db.backref('usuarios', lazy=True), foreign_keys=[id_area])

    # 3. Opcional: Si quieres que el usuario se bloquee si 'activo' es False
    def is_active(self):
        return self.activo