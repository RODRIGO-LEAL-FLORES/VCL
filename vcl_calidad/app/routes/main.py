from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app import db
from app.models.usuario import Usuario, Rol
from app.models.cliente import Cliente
import hashlib
from app.models.defectos import Defecto
from app.models.tipo import Tipo
from flask_login import login_required, login_user, current_user  # Importa funciones de Flask-Login

main_bp = Blueprint('main', __name__)

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


from flask_login import login_user, current_user

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
    
        
    # Si está logeado, ve sus tarjetas dinámicas en el home.html
    return render_template('home.html')





@main_bp.route('/reclamaciones')
@login_required
def reclamaciones():
    
    return render_template('reclamaciones.html')


@main_bp.route('/reclamaciones/<section>')
@login_required
def reclamaciones_section(section):
    

    allowed = {
        'nuevo': 'Nueva Reclamación',
        'categorias': 'Categorías',
        'defectos': 'Defectos',
        'ocurrencias': 'Ocurrencias',
        'tipos': 'Tipos de Reclamación',
        'estatus': 'Estatus de Reclamaciones',
        'clientes': 'Clientes',
        'contenedores': 'Contenedores'
    }

    if section not in allowed:
        abort(404)

    if section == 'clientes':
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        per_page = 10
        clients_query = Cliente.query
        if search_query:
            clients_query = clients_query.filter(Cliente.nombre.ilike(f'%{search_query}%'))

        total_results = clients_query.count()
        total_pages = (total_results + per_page - 1) // per_page if total_results else 1
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        clients = clients_query.order_by(Cliente.nombre).offset((page - 1) * per_page).limit(per_page).all()
        start = (page - 1) * per_page + 1 if total_results else 0
        end = min(page * per_page, total_results)

        if total_pages <= 7:
            page_numbers = list(range(1, total_pages + 1))
        else:
            if page <= 4:
                page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
            elif page >= total_pages - 3:
                page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]

        return render_template(
            'clientes.html',
            section_title=allowed[section],
            section_key=section,
            clients=clients,
            total_results=total_results,
            start=start,
            end=end,
            page=page,
            total_pages=total_pages,
            page_numbers=page_numbers,
            search_query=search_query
        )

    if section == 'defectos':
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        per_page = 10
        defectos_query = Defecto.query
        if search_query:
            defectos_query = defectos_query.filter(Defecto.descripcion.ilike(f'%{search_query}%'))

        total_results = defectos_query.count()
        total_pages = (total_results + per_page - 1) // per_page if total_results else 1
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        defectos = defectos_query.order_by(Defecto.descripcion).offset((page - 1) * per_page).limit(per_page).all()
        start = (page - 1) * per_page + 1 if total_results else 0
        end = min(page * per_page, total_results)

        if total_pages <= 7:
            page_numbers = list(range(1, total_pages + 1))
        else:
            if page <= 4:
                page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
            elif page >= total_pages - 3:
                page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]

        return render_template(
            'defectos.html',
            section_title=allowed[section],
            section_key=section,
            defectos=defectos,
            total_results=total_results,
            start=start,
            end=end,
            page=page,
            total_pages=total_pages,
            page_numbers=page_numbers,
            search_query=search_query
        )
    
    if section == 'tipos':
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        per_page = 10
        tipos_query = Tipo.query
        if search_query:
            tipos_query = tipos_query.filter(Tipo.nombre.ilike(f'%{search_query}%'))

        total_results = tipos_query.count()
        total_pages = (total_results + per_page - 1) // per_page if total_results else 1
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        tipos = tipos_query.order_by(Tipo.nombre).offset((page - 1) * per_page).limit(per_page).all()
        start = (page - 1) * per_page + 1 if total_results else 0
        end = min(page * per_page, total_results)

        if total_pages <= 7:
            page_numbers = list(range(1, total_pages + 1))
        else:
            if page <= 4:
                page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
            elif page >= total_pages - 3:
                page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
            else:
                page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]

        return render_template(
            'tipo.html',
            section_title=allowed[section],
            section_key=section,
            tipos=tipos,
            total_results=total_results,
            start=start,
            end=end,
            page=page,
            total_pages=total_pages,
            page_numbers=page_numbers,
            search_query=search_query
        )
    
    return render_template('reclamaciones_section.html', section_title=allowed[section], section_key=section)




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
    return render_template('usuarios.html', users=users, roles=roles)


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
        puede_ver_scrap=puede_ver_scrap  # Guardar en DB
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

        db.session.commit()
        return redirect(url_for('main.usuarios'))

    users = Usuario.query.order_by(Usuario.nombre).all()
    roles = Rol.query.order_by(Rol.nombre).all()
    return render_template('usuarios.html', users=users, roles=roles, edit_user=usuario)


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
#  CRUD clientes
# ==========================================


@main_bp.route('/reclamaciones/clientes/crear', methods=['POST'])
@login_required
def crear_cliente():
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash('El nombre del cliente es obligatorio.')
        return redirect(url_for('main.reclamaciones_section', section='clientes'))

    cliente = Cliente(nombre=nombre)
    db.session.add(cliente)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='clientes'))


@main_bp.route('/reclamaciones/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id_cliente):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    cliente = Cliente.query.get_or_404(id_cliente)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre del cliente es obligatorio.')
            return redirect(url_for('main.editar_cliente', id_cliente=id_cliente))

        cliente.nombre = nombre
        db.session.commit()
        return redirect(url_for('main.reclamaciones_section', section='clientes'))

    clients = Cliente.query.order_by(Cliente.nombre).all()
    total_results = len(clients)
    page = 1
    total_pages = 1
    page_numbers = [1]
    start = total_results and 1 or 0
    end = total_results
    return render_template(
        'clientes.html',
        section_title='Clientes',
        section_key='clientes',
        clients=clients,
        total_results=total_results,
        start=start,
        end=end,
        page=page,
        total_pages=total_pages,
        page_numbers=page_numbers,
        search_query='',
        edit_client=cliente
    )


@main_bp.route('/reclamaciones/clientes/eliminar/<int:id_cliente>', methods=['POST'])
@login_required
def eliminar_cliente(id_cliente):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    cliente = Cliente.query.get_or_404(id_cliente)
    db.session.delete(cliente)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='clientes'))

# ==========================================
#  CRUD DEFECTOS
# ==========================================

@main_bp.route('/reclamaciones/defectos/crear', methods=['POST'])
@login_required
def crear_defecto():
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    descripcion = request.form.get('descripcion', '').strip()
    if not descripcion:
        flash('La descripción del defecto es obligatoria.')
        return redirect(url_for('main.reclamaciones_section', section='defectos'))

    defecto = Defecto(descripcion=descripcion)
    db.session.add(defecto)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='defectos'))


@main_bp.route('/reclamaciones/defectos/editar/<int:id_defecto>', methods=['GET', 'POST'])
@login_required
def editar_defecto(id_defecto):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    defecto = Defecto.query.get_or_404(id_defecto)

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            flash('La descripción del defecto es obligatoria.')
            return redirect(url_for('main.editar_defecto', id_defecto=id_defecto))

        defecto.descripcion = descripcion
        db.session.commit()
        return redirect(url_for('main.reclamaciones_section', section='defectos'))

    search_query = ''
    page = 1
    per_page = 10
    defectos_query = Defecto.query
    total_results = defectos_query.count()
    total_pages = (total_results + per_page - 1) // per_page if total_results else 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    defectos = defectos_query.order_by(Defecto.descripcion).offset((page - 1) * per_page).limit(per_page).all()
    start = (page - 1) * per_page + 1 if total_results else 0
    end = min(page * per_page, total_results)

    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        if page <= 4:
            page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
        elif page >= total_pages - 3:
            page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        else:
            page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]

    return render_template(
        'defectos.html',
        section_title='Defectos',
        section_key='defectos',
        defectos=defectos,
        total_results=total_results,
        start=start,
        end=end,
        page=page,
        total_pages=total_pages,
        page_numbers=page_numbers,
        search_query=search_query,
        edit_defecto=defecto
    )


@main_bp.route('/reclamaciones/defectos/eliminar/<int:id_defecto>', methods=['POST'])
@login_required        
def eliminar_defecto(id_defecto):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    defecto = Defecto.query.get_or_404(id_defecto)
    db.session.delete(defecto)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='defectos'))



# ==========================================
#  CRUD TIPOS
# ==========================================

@main_bp.route('/reclamaciones/tipos/crear', methods=['POST'])
@login_required
def crear_tipo():
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash('El nombre del tipo es obligatorio.')
        return redirect(url_for('main.reclamaciones_section', section='tipos'))
    tipo_nuevo = Tipo(nombre=nombre)
    db.session.add(tipo_nuevo)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='tipos'))

@main_bp.route('/reclamaciones/tipos/editar/<int:id_tipo>', methods=['GET', 'POST'])
@login_required
def editar_tipo(id_tipo):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    tipo = Tipo.query.get_or_404(id_tipo)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre del tipo es obligatorio.')
            return redirect(url_for('main.editar_tipo', id_tipo=id_tipo))

        tipo.nombre = nombre
        db.session.commit()
        return redirect(url_for('main.reclamaciones_section', section='tipos'))

    search_query = ''
    page = 1
    per_page = 10
    tipos_query = Tipo.query
    total_results = tipos_query.count()
    total_pages = (total_results + per_page - 1) // per_page if total_results else 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    tipos = tipos_query.order_by(Tipo.nombre).offset((page - 1) * per_page).limit(per_page).all()
    start = (page - 1) * per_page + 1 if total_results else 0
    end = min(page * per_page, total_results)

    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        if page <= 4:
            page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
        elif page >= total_pages - 3:
            page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        else:
            page_numbers = [1, '...', page - 1, page, page + 1, '...', total_pages]

    return render_template(
        'tipo.html',
        section_title='Tipos de Reclamación',
        section_key='tipos',
        tipos=tipos,
        total_results=total_results,
        start=start,
        end=end,
        page=page,
        total_pages=total_pages,
        page_numbers=page_numbers,
        search_query=search_query,
        edit_tipo=tipo
    )
  
    
@main_bp.route('/reclamaciones/tipos/eliminar/<int:id_tipo>', methods=['POST'])
@login_required
def eliminar_tipo(id_tipo):
    if 'user_id' not in session:
        return redirect(url_for('main.welcome'))

    tipo_eliminar = Tipo.query.get_or_404(id_tipo)
    db.session.delete(tipo_eliminar)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='tipos'))



# ==========================================
#  CERRAR SESIÓN (LOGOUT)
# ==========================================
@main_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.')
    return redirect(url_for('main.welcome'))