import os
from app import create_app
from app.init_fixed_estatus import init_fixed_estatus

# Llamamos a la función factory para que configure todo y nos devuelva la app
app = create_app()

# Inicializar estatus fijos al arrancar la aplicación
with app.app_context():
    print("\n Inicializando estatus fijos...")
    init_fixed_estatus()
    print(" Estatus fijos inicializados correctamente.\n")

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5000, debug=True)
    
    
