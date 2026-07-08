from app import db

class Color_Ticket(db.Model):
    __tablename__ = 'color_tickets'
    id_color = db.Column(db.Integer, primary_key=True)
    color_ticket = db.Column(db.String(20), nullable=False, unique=True)
    descripcion_color_ticket = db.Column(db.String(1000))
    dias_resolucion = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Color_Ticket {self.color_ticket}>'

class Area(db.Model):
    __tablename__ = 'areas'
    id_area = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Area {self.area}>'
    

class Estatus_Ticket(db.Model):
    __tablename__ = 'estatus_tickets'
    id_estatus_ticket = db.Column(db.Integer, primary_key=True)
    status_descripcion = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Estatus_Ticket {self.status_descripcion}>'


