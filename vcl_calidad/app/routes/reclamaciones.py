from flask_login import current_user, login_required

from . import main_bp

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app import db
from app.models.defectos import Defecto
from app.models.tipo import Tipo
from app.models.cliente import Cliente
 # Importamos el Blueprint creado en __init__.py


@main_bp.route('/reclamaciones')
@login_required
def reclamaciones():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))
    return render_template('reclamaciones.html')


@main_bp.route('/reclamaciones/<section>')
@login_required
def reclamaciones_section(section):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
#  CRUD clientes
# ==========================================


@main_bp.route('/reclamaciones/clientes/crear', methods=['POST'])
@login_required
def crear_cliente():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))
    

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

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
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    tipo_editar = Tipo.query.get_or_404(id_tipo)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre del tipo es obligatorio.')
            return redirect(url_for('main.editar_tipo', id_tipo=id_tipo))

        tipo_editar.nombre = nombre
        db.session.commit()
        return redirect(url_for('main.reclamaciones_section', section='tipos'))

    return render_template(
        'editar_tipo.html',
        section_title='Editar Tipo',
        section_key='tipos',
        tipo=tipo_editar
    )
    
@main_bp.route('/reclamaciones/tipos/eliminar/<int:id_tipo>', methods=['POST'])
@login_required
def eliminar_tipo(id_tipo):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    tipo_eliminar = Tipo.query.get_or_404(id_tipo)
    db.session.delete(tipo_eliminar)
    db.session.commit()

    return redirect(url_for('main.reclamaciones_section', section='tipos'))
