"""
Script de inicialización de estatus fijos para TICKETS.
Estos estatus son independientes de los de Scrap.
"""

from app import db
from app.models.tickect_models import Estatus_Ticket


def init_tickets_estatus():
    """Crea los estatus fijos de tickets si no existen."""
    
    estatus_fijos = [
        'Sin atender',
        'En proceso',
        'Pendiente de validación',
        'Cerrado'
    ]
    
    for descripcion in estatus_fijos:
        existe = Estatus_Ticket.query.filter_by(status_descripcion=descripcion).first()
        if not existe:
            nuevo = Estatus_Ticket(status_descripcion=descripcion)
            db.session.add(nuevo)
            print(f"✓ Estatus Ticket creado: {descripcion}")
        else:
            print(f"✓ Estatus Ticket ya existe: {descripcion}")
    
    # Guardar todos los cambios
    try:
        db.session.commit()
        print("✓ Estatus de Tickets inicializados correctamente.\n")
    except Exception as e:
        db.session.rollback()
        print(f"Error al inicializar estatus de tickets: {e}")
        raise


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        init_tickets_estatus()
