from app import db

class Maquina(db.Model):
    __tablename__ = 'maquinas'
    id_maquina = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Maquina {self.nombre}>'


class Operador(db.Model):
    __tablename__ = 'operadores'
    id_operador = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False, unique=True)

    def __repr__(self):
        return f'<Operador {self.nombre}>'


class Turno(db.Model):
    __tablename__ = 'turnos'
    id_turno = db.Column(db.Integer, primary_key=True)
    nombre_turno = db.Column(db.String(25), nullable=False, unique=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<Turno {self.nombre_turno}>'


class DefectoScrap(db.Model):
    __tablename__ = 'defectos_scrap'
    id_defecto_scrap = db.Column(db.Integer, primary_key=True)
    defecto = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<DefectoScrap {self.defecto}>'


class ClasificacionScrap(db.Model):
    __tablename__ = 'clasificaciones_scrap'
    id_clasificacion = db.Column(db.Integer, primary_key=True)
    clasificacion = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<ClasificacionScrap {self.clasificacion}>'


class Supervisor(db.Model):
    __tablename__ = 'supervisores'
    id_supervisor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False, unique=True)

    def __repr__(self):
        return f'<Supervisor {self.nombre}>'


class TipoAcero(db.Model):
    __tablename__ = 'tipos_acero'
    id_tipo_acero = db.Column(db.Integer, primary_key=True)
    especificacion = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<TipoAcero {self.especificacion}>'


class TipoLaminacion(db.Model):
    __tablename__ = 'tipos_laminacion'
    id_tipo_laminacion = db.Column(db.Integer, primary_key=True)
    especificacion = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<TipoLaminacion {self.especificacion}>'


class EstatusScrap(db.Model):
    __tablename__ = 'estatus_scrap'
    id_estatus_scrap = db.Column(db.Integer, primary_key=True)
    descripcion_status = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<EstatusScrap {self.descripcion_status}>'