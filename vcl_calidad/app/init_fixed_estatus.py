"""
Script de inicialización de estatus fijos.
Ejecutar una sola vez o antes de iniciar la app para asegurar que existan los estatus predefinidos.

IMPORTANTE: Solo Tickets tiene estatus fijos. Scrap gestiona sus propios estatus dinámicamente.
"""

from app.init_tickets_estatus import init_tickets_estatus


def init_fixed_estatus():
    """
    Inicializa los estatus fijos de la aplicación.
    - Tickets: Estatus predefinidos y fijos
    - Scrap: Gestiona sus estatus de forma dinámica (sin inicialización fija)
    """
    print("\n" + "="*60)
    print("INICIALIZANDO ESTATUS FIJOS")
    print("="*60 + "\n")
    
    # Inicializar estatus de Tickets (fijos)
    print(" ESTATUS DE TICKETS:")
    print("-" * 60)
    init_tickets_estatus()
    
    print("="*60)
    print("✓ Estatus fijos inicializados correctamente")
    print("="*60 + "\n")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        init_fixed_estatus()
