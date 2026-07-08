from datetime import datetime

from app import db


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id_folio_ticket = db.Column(db.Integer, primary_key=True)
    id_color_ticket = db.Column(db.Integer, db.ForeignKey('color_tickets.id_color'), nullable=True)
    id_usuario_creador = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    emisor = db.Column(db.String(100), nullable=True)
    id_area_responsable = db.Column(db.Integer, db.ForeignKey('areas.id_area'), nullable=True)
    fecha_emicion = db.Column(db.Date, nullable=False)
    fecha_compromiso = db.Column(db.Date, nullable=True)
    fecha_cierre = db.Column(db.Date, nullable=True)
    id_estatus_ticket = db.Column(db.Integer, db.ForeignKey('estatus_tickets.id_estatus_ticket'), nullable=False)
    dias_retrazo = db.Column(db.Integer, default=0)
    evidencia_resolucion = db.Column(db.Text, nullable=True)
    problematica = db.Column(db.Text, nullable=True)
    accion_correctiva = db.Column(db.Text, nullable=True)

    # Relationships
    color_ticket = db.relationship('Color_Ticket', backref='tickets')
    area_responsable = db.relationship('Area', backref='tickets')
    estatus_ticket = db.relationship('Estatus_Ticket', backref='tickets')
    usuario_creador = db.relationship('Usuario', backref='tickets_creados', foreign_keys=[id_usuario_creador])
    evidencias = db.relationship('TicketEvidence', back_populates='ticket', cascade='all, delete-orphan')

    @property
    def dias_retraso_calculado(self):
        if not self.fecha_compromiso:
            return 0
        retraso = (datetime.now().date() - self.fecha_compromiso).days
        return retraso if retraso > 0 else 0

    def __repr__(self):
        return f'<Ticket {self.id_folio_ticket}>'


class TicketEvidence(db.Model):
    __tablename__ = 'ticket_evidencias'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id_folio_ticket'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    ticket = db.relationship('Ticket', back_populates='evidencias')

    def __repr__(self):
        return f'<TicketEvidence {self.filename}>'



