from app import db
from datetime import datetime

class Scrap(db.Model):
    __tablename__ = 'scrap'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Llaves Foráneas
    id_maquina = db.Column(db.Integer, db.ForeignKey('maquinas.id_maquina'), nullable=False)
    id_operador = db.Column(db.Integer, db.ForeignKey('operadores.id_operador'), nullable=False)
    id_turno = db.Column(db.Integer, db.ForeignKey('turnos.id_turno'), nullable=False)
    id_defecto_scrap = db.Column(db.Integer, db.ForeignKey('defectos_scrap.id_defecto_scrap'), nullable=False)
    id_clasificacion = db.Column(db.Integer, db.ForeignKey('clasificaciones_scrap.id_clasificacion'), nullable=False)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('supervisores.id_supervisor'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_tipo_acero = db.Column(db.Integer, db.ForeignKey('tipos_acero.id_tipo_acero'), nullable=False)
    id_estatus_scrap = db.Column(db.Integer, db.ForeignKey('estatus_scrap.id_estatus_scrap'), nullable=False)
    usuario_registro_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Campos manuales
    numero_parte = db.Column(db.String(50), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    peso = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad_retrabajado = db.Column(db.Integer, default=0)
    cantidad_ng = db.Column(db.Integer, default=0)

    # Relaciones para usar fácilmente en Jinja2 (ej: registro.maquina.nombre)
    maquina = db.relationship('Maquina', backref='registros_scrap')
    operador = db.relationship('Operador', backref='registros_scrap')
    turno = db.relationship('Turno', backref='registros_scrap')
    defecto = db.relationship('DefectoScrap', backref='registros_scrap')
    clasificacion = db.relationship('ClasificacionScrap', backref='registros_scrap')
    supervisor = db.relationship('Supervisor', backref='registros_scrap')
    tipo_acero = db.relationship('TipoAcero', backref='registros_scrap')
    estatus = db.relationship('EstatusScrap', backref='registros_scrap')
   
    cliente = db.relationship('Cliente', backref='registros_scrap')

    def __repr__(self):
        return f'<Scrap ID {self.id} - Lote {self.lote}>'