from app  import db

class Defecto(db.Model):
    __tablename__ = 'defectos'

    id_defecto = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Defecto {self.descripcion!r}>"