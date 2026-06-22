from app  import db

class Tipo(db.Model):
    __tablename__ = 'tipos'

    id_tipo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Tipo {self.nombre!r}>"