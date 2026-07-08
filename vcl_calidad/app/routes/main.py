from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app import db
from app.models.usuario import Usuario, Rol
from app.models.tickect_models.T_models import Area  # Importa el modelo Area

import hashlib

from flask_login import login_required, login_user, current_user  # Importa funciones de Flask-Login

main_bp = Blueprint('main', __name__)



# ── Sesión permanente en todas las rutas ──────────────────────────────
@main_bp.before_request
def make_session_permanent():
    session.permanent = True

# ==========================================
# 1. TU INDEX PÚBLICO (LA RAÍZ)
# ==========================================
@main_bp.route('/')
def index():
    # Esta es tu página de inicio pública. Cualquiera la puede ver sin logearse.
    return render_template('index.html')


# ==========================================
# 2. TU LOGIN (WELCOME)
# ==========================================



@main_bp.route('/welcome', methods=['GET', 'POST'])
def welcome():
    # Si ya está autenticado, directo al home
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password_ingresado = request.form.get('password')
        
        hashed = hashlib.md5((password_ingresado + (email or '')).encode()).hexdigest()

        user = Usuario.query.filter(
            Usuario.email == email,
            Usuario.password == hashed,
            Usuario.activo == True
        ).first()
        
        if user:
            login_user(user) # Esto gestiona la sesión automáticamente
            return redirect(url_for('main.home'))
        else:
            flash('Credenciales incorrectas o usuario inactivo.')
            return redirect(url_for('main.welcome'))
            
    return render_template('welcome.html')



# ==========================================
# 3. TU HOME PRIVADO (PANEL DE CONTROL)
# ==========================================
@main_bp.route('/home')

@login_required
def home():
    session.permanent = True 
        
    # Si está logeado, ve sus tarjetas dinámicas en el home.html
    return render_template('home.html')







# ==========================================
#  CRUD USUARIOS
# ==========================================


@main_bp.route('/usuarios')
@login_required
def usuarios():
    if not current_user.puede_gestionar_usuarios:
        flash("No tienes autorización para gestionar usuarios.")
        return redirect(url_for('main.home'))

    users = Usuario.query.order_by(Usuario.nombre).all()
    roles = Rol.query.order_by(Rol.nombre).all()
    areas = Area.query.order_by(Area.area).all()
    return render_template('usuarios.html', users=users, roles=roles, areas=areas)


@main_bp.route('/usuarios/crear', methods=['POST'])
@login_required
def crear_usuario():
    if not current_user.puede_gestionar_usuarios:
        flash("No tienes autorización para gestionar usuarios.")
        return redirect(url_for('main.home'))

    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    rol_id = request.form.get('rol_id')
    activo = bool(request.form.get('activo'))
    id_area = request.form.get('id_area')  # Nuevo campo para el área
    puede_ver_reclamaciones = bool(request.form.get('puede_ver_reclamaciones'))
    puede_ver_tickets = bool(request.form.get('puede_ver_tickets'))
    puede_ver_reportes = bool(request.form.get('puede_ver_reportes'))
    puede_gestionar_usuarios = bool(request.form.get('puede_gestionar_usuarios'))
    # NUEVO MÓDULO: Control de Scrap
    puede_ver_scrap = bool(request.form.get('puede_ver_scrap'))

    if not nombre or not email or not password or not rol_id:
        flash('Nombre, email, contraseña y rol son obligatorios.')
        return redirect(url_for('main.usuarios'))

    hashed = hashlib.md5((password + email).encode()).hexdigest()

    # Evitar duplicados por email
    existing = Usuario.query.filter(Usuario.email == email).first()
    if existing:
        flash('Ya existe un usuario con ese correo.')
        return redirect(url_for('main.usuarios'))

    usuario = Usuario(
        nombre=nombre,
        email=email,
        password=hashed,
        rol_id=int(rol_id),
        activo=activo,
        puede_ver_reclamaciones=puede_ver_reclamaciones,
        puede_ver_tickets=puede_ver_tickets,
        puede_ver_reportes=puede_ver_reportes,
        puede_gestionar_usuarios=puede_gestionar_usuarios,
        puede_ver_scrap=puede_ver_scrap,  # Guardar en DB
        id_area=int(id_area) if id_area else None  # Guardar el ID del área
    )
    db.session.add(usuario)
    db.session.commit()
    return redirect(url_for('main.usuarios'))


@main_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id_usuario):
    if not current_user.puede_gestionar_usuarios:
        flash("No tienes autorización para gestionar usuarios.")
        return redirect(url_for('main.home'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rol_id = request.form.get('rol_id')
        activo = bool(request.form.get('activo'))
        puede_ver_reclamaciones = bool(request.form.get('puede_ver_reclamaciones'))
        puede_ver_tickets = bool(request.form.get('puede_ver_tickets'))
        puede_ver_reportes = bool(request.form.get('puede_ver_reportes'))
        puede_gestionar_usuarios = bool(request.form.get('puede_gestionar_usuarios'))
        id_area = request.form.get('id_area')
        # NUEVO MÓDULO: Control de Scrap
        puede_ver_scrap = bool(request.form.get('puede_ver_scrap'))

        if not nombre or not email or not rol_id:
            flash('Nombre, email y rol son obligatorios.')
            return redirect(url_for('main.editar_usuario', id_usuario=id_usuario))

        usuario.nombre = nombre
        usuario.email = email
        if password:
            usuario.password = hashlib.md5((password + email).encode()).hexdigest()
        usuario.rol_id = int(rol_id)
        usuario.activo = activo
        usuario.puede_ver_reclamaciones = puede_ver_reclamaciones
        usuario.puede_ver_tickets = puede_ver_tickets
        usuario.puede_ver_reportes = puede_ver_reportes
        usuario.puede_gestionar_usuarios = puede_gestionar_usuarios
        usuario.puede_ver_scrap = puede_ver_scrap  # Actualizar en DB
        usuario.id_area = int(id_area) if id_area else None  # Actualizar el ID del área

        db.session.commit()
        return redirect(url_for('main.usuarios'))

    users = Usuario.query.order_by(Usuario.nombre).all()
    roles = Rol.query.order_by(Rol.nombre).all()
    areas = Area.query.order_by(Area.area).all()
    return render_template('usuarios.html', users=users, roles=roles, areas=areas, edit_user=usuario)


@main_bp.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
@login_required        
def eliminar_usuario(id_usuario):
    if not current_user.puede_gestionar_usuarios:
        flash("No tienes autorización para gestionar usuarios.")
        return redirect(url_for('main.home'))

    usuario = Usuario.query.get_or_404(id_usuario)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('main.usuarios'))



# ==========================================
#  CERRAR SESIÓN (LOGOUT)
# ==========================================
@main_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.')
    return redirect(url_for('main.welcome'))