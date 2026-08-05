from app import db


class EstatusLiberacion(db.Model):
    __tablename__ = 'estatus_liberaciones'
    id_estatus = db.Column(db.Integer, primary_key=True)
    descripcion_status = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<EstatusLiberacion {self.descripcion_status}>'