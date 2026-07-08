from app import db


class Reclamacion(db.Model):
    __tablename__ = 'reclamaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_reporte_cliente = db.Column(db.String(50), nullable=False, unique=True)
    issue = db.Column(db.String(255), nullable=False)

    id_defecto = db.Column(db.Integer, db.ForeignKey('defectos.id_defecto'), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categorias'), nullable=False)
    id_ocurrencia = db.Column(db.Integer, db.ForeignKey('ocurrencias.id_ocurrencia'), nullable=False)
    id_numero_contenedor = db.Column(db.Integer, db.ForeignKey('contenedores.id_numero_contenedor'), nullable=True)
    id_tipo_de_reclamacion = db.Column(db.Integer, db.ForeignKey('tipo_de_reclamacion.id_tipo_de_reclamacion'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=True)
    id_estatus = db.Column(db.Integer, db.ForeignKey('estatus_reclamaciones.id_estatus'), nullable=False)

    numero_parte = db.Column(db.String(50), nullable=True)
    lote = db.Column(db.String(50), nullable=True)
    cantidad_piezas = db.Column(db.Integer, nullable=True)
    cantidad_kg = db.Column(db.Numeric(10, 2), nullable=True)

    fecha_reporte = db.Column(db.Date, nullable=False)
    fecha_confirmacion = db.Column(db.Date, nullable=True)
    fecha_contencion = db.Column(db.Date, nullable=True)
    fecha_CR_AC = db.Column(db.Date, nullable=True)
    fecha_cierre = db.Column(db.Date, nullable=True)

    dias_retrazo_al_reclamo = db.Column(db.Integer, default=0)
    periodo = db.Column(db.String(50), nullable=True)

    # Relationships
    defecto = db.relationship('Defecto', backref='reclamaciones')
    categoria = db.relationship('Categoria', backref='reclamaciones')
    ocurrencia = db.relationship('Ocurrencia', backref='reclamaciones')
    contenedor = db.relationship('Contenedor', backref='reclamaciones')
    tipo_de_reclamacion = db.relationship('TipoDeReclamacion', backref='reclamaciones')
    cliente = db.relationship('Cliente', backref='reclamaciones')
    estatus = db.relationship('EstatusReclamacion', backref='reclamaciones')

    def __repr__(self):
        return f'<Reclamacion {self.id_reporte_cliente}>'