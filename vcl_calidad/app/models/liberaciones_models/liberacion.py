from app import db


class Liberacion(db.Model):
    __tablename__ = 'liberaciones'
    id = db.Column(db.Integer, primary_key=True)
    motivo = db.Column(db.String(300), nullable=False)
    fecha_liberacion = db.Column(db.Date, nullable=False)
    hora_liberacion = db.Column(db.Time, nullable=False)
    
    id_status = db.Column(db.Integer, db.ForeignKey('estatus_liberaciones.id_estatus'), nullable=False)
    
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_tipo_laminacion = db.Column(db.Integer, db.ForeignKey('tipos_laminacion.id_tipo_laminacion'), nullable=False)
    id_maquina = db.Column(db.Integer, db.ForeignKey('maquinas.id_maquina'), nullable=False)

    
    # Relationships
    estatus = db.relationship('EstatusLiberacion', backref='liberaciones')
    usuario = db.relationship('Usuario', backref='liberaciones')
    cliente = db.relationship('Cliente', backref='liberaciones')
    tipo_laminacion = db.relationship('TipoLaminacion', backref='liberaciones')
    maquina = db.relationship('Maquina', backref='liberaciones')
    

    def __repr__(self):
        return f'<Liberacion {self.id}>'