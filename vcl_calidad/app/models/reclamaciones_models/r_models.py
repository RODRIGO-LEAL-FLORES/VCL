from app import db


class Categoria(db.Model):
    __tablename__ = 'categorias'
    id_categorias = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Categoria {self.categoria}>'


class Defecto(db.Model):
    __tablename__ = 'defectos'

    id_defecto = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Defecto {self.descripcion!r}>"

class Ocurrencia(db.Model):
    __tablename__ = 'ocurrencias'
    id_ocurrencia = db.Column(db.Integer, primary_key=True)
    ocurrencia = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Ocurrencia {self.ocurrencia}>'


class TipoDeReclamacion(db.Model):
    __tablename__ = 'tipo_de_reclamacion'
    id_tipo_de_reclamacion = db.Column(db.Integer, primary_key=True)
    tipo_reclamacion = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<TipoDeReclamacion {self.tipo_reclamacion}>'


class EstatusReclamacion(db.Model):
    __tablename__ = 'estatus_reclamaciones'
    id_estatus = db.Column(db.Integer, primary_key=True)
    descripcion_status = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<EstatusReclamacion {self.descripcion_status}>'



    


class Contenedor(db.Model):
    __tablename__ = 'contenedores'
    id_numero_contenedor = db.Column(db.Integer, primary_key=True)
    numero_contenedor = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Contenedor {self.numero_contenedor}>'