import os
import uuid
import smtplib
from email.message import EmailMessage
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import cast, String
from app import db

from app.models.tickect_models import Color_Ticket, Area, Estatus_Ticket
from app.models.tickect_models.ticket import Ticket, TicketEvidence
from app.models.usuario import Usuario
from app.routes.main import main_bp

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_status_id(status_name):
    """
    Obtiene el ID de un estatus por su nombre descriptivo.
    Si no existe, retorna el primer estatus disponible como fallback.
    IMPORTANTE: Los estatus deben estar predefinidos en la BD por init_fixed_estatus.py
    """
    status = Estatus_Ticket.query.filter_by(status_descripcion=status_name).first()
    if status:
        return status.id_estatus_ticket
    
    # Fallback: usar el primer estatus disponible
    fallback = Estatus_Ticket.query.order_by(Estatus_Ticket.id_estatus_ticket).first()
    if fallback:
        print(f"⚠️  Estatus '{status_name}' no encontrado. Usando fallback: '{fallback.status_descripcion}'")
        return fallback.id_estatus_ticket
    
    # Error: no hay ningún estatus disponible (no debería ocurrir si init se ejecutó)
    raise ValueError("⚠️  NO HAY ESTATUS DISPONIBLES. Ejecute init_fixed_estatus() primero.")


def create_ticket_from_form():
    fecha_cierre_str = request.form.get('fecha_cierre')
    problematica_str = request.form.get('problematica', '').strip() or None

    fecha_emicion = datetime.now().date()
    fecha_cierre = datetime.strptime(fecha_cierre_str, '%Y-%m-%d').date() if fecha_cierre_str else None
    color_id = request.form.get('id_color_ticket') or None
    color_obj = Color_Ticket.query.get(int(color_id)) if color_id else None

    fecha_compromiso = None
    if fecha_emicion and color_obj and color_obj.dias_resolucion is not None:
        fecha_compromiso = fecha_emicion + timedelta(days=color_obj.dias_resolucion)

    nuevo_ticket = Ticket(
        id_color_ticket      = color_id,
        id_usuario_creador   = current_user.id,
        emisor               = current_user.nombre,
        id_area_responsable  = request.form.get('id_area_responsable') or None,
        fecha_emicion        = fecha_emicion,
        fecha_compromiso     = fecha_compromiso,
        fecha_cierre         = fecha_cierre,
        id_estatus_ticket    = get_status_id('Sin atender') or get_status_id('En proceso') or 1,
        dias_retrazo         = 0,
        problematica         = problematica_str,
    )
    db.session.add(nuevo_ticket)
    db.session.commit()
    # send_ticket_notification(nuevo_ticket)  # Desactivado temporalmente


# =========================================================================
# VISTA PRINCIPAL: MENÚ DE TICKETS
# =========================================================================
@main_bp.route('/tickets')
@login_required
def tickets():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    return render_template(
        'tickets/tickets.html',
        today=datetime.now().date(),
        colores=Color_Ticket.query.order_by(Color_Ticket.color_ticket).all(),
        areas=Area.query.order_by(Area.area).all(),
        registros=Ticket.query.filter(Ticket.id_usuario_creador == current_user.id).order_by(Ticket.id_folio_ticket.desc()).limit(20).all(),
    )

@main_bp.route('/tickets/generar-registro', methods=['GET', 'POST'])
@login_required
def tickets_create():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        create_ticket_from_form()
        flash('Ticket registrado correctamente.')
        return redirect(url_for('main.tickets_create'))
    
    # Búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    items_per_page = 10
    
    # Query base: tickets del usuario actual
    query = Ticket.query.filter(Ticket.id_usuario_creador == current_user.id)
    
    # Filtro por folio si hay búsqueda
    if search_query:
        query = query.filter(cast(Ticket.id_folio_ticket, String).ilike(f'%{search_query}%'))
    
    # Total de resultados
    total_results = query.count()
    
    # Paginación
    paginated = query.order_by(Ticket.id_folio_ticket.desc()).paginate(
        page=page, per_page=items_per_page, error_out=False
    )
    items = paginated.items
    total_pages = paginated.pages
    
    # Calcular rango mostrado
    start = (page - 1) * items_per_page + 1 if items else 0
    end = min(start + len(items) - 1, total_results)
    
    # Números de página para paginación
    page_numbers = []
    for i in range(1, total_pages + 1):
        if i == 1 or i == total_pages or abs(i - page) <= 1:
            page_numbers.append(i)
        elif page_numbers[-1] != '...':
            page_numbers.append('...')
    
    return render_template(
        'tickets/generar_registro.html',
        today=datetime.now().date(),
        colores=Color_Ticket.query.order_by(Color_Ticket.color_ticket).all(),
        areas=Area.query.order_by(Area.area).all(),
        items=items,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        start=start,
        end=end,
        search_query=search_query,
        page_numbers=page_numbers,
    )

@main_bp.route('/tickets/mis-pendientes')
@login_required
def mis_tickets():
    closed_id = get_status_id('Cerrado') or 3
    tickets = Ticket.query.filter(
        Ticket.id_area_responsable == current_user.id_area,
        Ticket.id_estatus_ticket != closed_id
    ).order_by(Ticket.fecha_compromiso.asc()).all()

    return render_template('tickets/mis_tickets.html', tickets=tickets, today=datetime.now().date(), closed_id=closed_id)


@main_bp.route('/tickets/seguimiento')
@login_required
def seguimiento_tickets():
    closed_id = get_status_id('Cerrado') or 3
    tickets = Ticket.query.filter(
        Ticket.id_area_responsable == current_user.id_area,
        Ticket.id_estatus_ticket != closed_id
    ).order_by(Ticket.fecha_compromiso.asc()).all()

    return render_template('tickets/seguimiento_tickets.html', tickets=tickets, today=datetime.now().date(), closed_id=closed_id)


@main_bp.route('/tickets/por-cerrar')
@login_required
def cerrar_tickets():
    pendiente_validacion_id = get_status_id('Pendiente de validación')
    if pendiente_validacion_id is None:
        tickets = []
    else:
        tickets = Ticket.query.filter(
            Ticket.id_usuario_creador == current_user.id,
            Ticket.id_estatus_ticket == pendiente_validacion_id
        ).order_by(Ticket.fecha_compromiso.asc()).all()

    return render_template('tickets/cerrar_tickets.html', tickets=tickets, today=datetime.now().date())


@main_bp.route('/tickets/detalle/<int:item_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(item_id):
    ticket = Ticket.query.get_or_404(item_id)
    sin_atender_id = get_status_id('Sin atender')
    en_proceso_id = get_status_id('En proceso')
    pendiente_validacion_id = get_status_id('Pendiente de validación')
    cerrado_id = get_status_id('Cerrado') or 3

    if request.method == 'POST':
        if current_user.id == ticket.id_usuario_creador and ticket.id_estatus_ticket == pendiente_validacion_id:
            if request.form.get('cerrar_ticket'):
                ticket.id_estatus_ticket = cerrado_id
                ticket.fecha_cierre = datetime.now().date()
                db.session.commit()
                flash('Ticket cerrado correctamente.')
                return redirect(url_for('main.ticket_detail', item_id=item_id))

        if current_user.id_area == ticket.id_area_responsable:
            acciones_correctivas_str = request.form.get('acciones_correctivas', '').strip() or None
            evidencia_resolucion_str = request.form.get('evidencia_resolucion', '').strip() or None
            uploaded_files = request.files.getlist('evidence_images')
            saved_files = []

            if acciones_correctivas_str:
                ticket.accion_correctiva = acciones_correctivas_str
                if en_proceso_id:
                    ticket.id_estatus_ticket = en_proceso_id

            if evidencia_resolucion_str:
                ticket.evidencia_resolucion = evidencia_resolucion_str
                if pendiente_validacion_id:
                    ticket.id_estatus_ticket = pendiente_validacion_id

            for upload in uploaded_files:
                if upload and upload.filename and allowed_image(upload.filename):
                    filename = secure_filename(upload.filename)
                    unique_name = f"{uuid.uuid4().hex}_{filename}"
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                    upload.save(save_path)
                    evidence = TicketEvidence(ticket_id=ticket.id_folio_ticket, filename=unique_name)
                    db.session.add(evidence)
                    saved_files.append(unique_name)

            if saved_files and pendiente_validacion_id:
                ticket.id_estatus_ticket = pendiente_validacion_id

            ticket.dias_retrazo = 0
            if ticket.fecha_compromiso:
                overdue_days = (datetime.now().date() - ticket.fecha_compromiso).days
                ticket.dias_retrazo = overdue_days if overdue_days > 0 else 0

            db.session.commit()
            flash('Ticket actualizado correctamente.')
            return redirect(url_for('main.ticket_detail', item_id=item_id))

    return render_template('tickets/ticket_detail.html', ticket=ticket, today=datetime.now().date(), closed_id=cerrado_id, pendiente_validacion_id=pendiente_validacion_id)


# =========================================================================
# CONTROLADOR DINÁMICO POR SECCIONES (VISTAS GET / POST)
# =========================================================================
@main_bp.route('/tickets/<section>', methods=['GET', 'POST'])
@login_required
def tickets_section(section):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    edit_id = request.args.get('edit_id', type=int)

    # --- LÓGICA PARA REGISTROS DE TICKETS ---
    if section == 'nuevo':
        if request.method == 'POST':
            try:
                create_ticket_from_form()
            except Exception as e:
                db.session.rollback()
                flash(f'Error al guardar: {e}')
            return redirect(url_for('main.tickets'))

        return redirect(url_for('main.tickets'))

    # --- LÓGICA PARA CATÁLOGOS ---
    mapping = {
        'colores':  (Color_Ticket,   'tickets/colores.html',  'color_ticket'),
        'areas':    (Area,           'tickets/areas.html',    'area'),
        'estatus':  (Estatus_Ticket, 'tickets/estatus.html',  'status_descripcion'),
    }

    if section in mapping:
        model, template, field = mapping[section]

        page         = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '', type=str).strip()
        per_page     = 20

        query = model.query
        if search_query:
            query = query.filter(getattr(model, field).ilike(f'%{search_query}%'))

        pagination = query.order_by(field).paginate(page=page, per_page=per_page, error_out=False)
        total      = pagination.total
        start      = (page - 1) * per_page + 1 if total > 0 else 0
        end        = min(page * per_page, total)

        def build_page_numbers(current, total_pages):
            pages = []
            for n in range(1, total_pages + 1):
                if n == 1 or n == total_pages or abs(n - current) <= 1:
                    pages.append(n)
                elif pages and pages[-1] != '...':
                    pages.append('...')
            return pages

        return render_template(template,
            items         = pagination.items,
            edit_item     = model.query.get(edit_id) if edit_id else None,
            page          = page,
            total_pages   = pagination.pages,
            page_numbers  = build_page_numbers(page, pagination.pages),
            search_query  = search_query,
            total_results = total,
            start         = start,
            end           = end,
            section       = section,
        )

    return redirect(url_for('main.tickets_section', section='nuevo'))


# =========================================================================
# RUTAS POST: CRUD CENTRALIZADO DE CATÁLOGOS
# =========================================================================
@main_bp.route('/tickets/action/<section>/<action_type>', methods=['POST'])
@main_bp.route('/tickets/action/<section>/<action_type>/<int:item_id>', methods=['POST'])
@login_required
def tickets_actions(section, action_type, item_id=None):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    # ===== PROTECCIÓN: ESTATUS NO SE PUEDE CREAR NI EDITAR =====
    if section == 'estatus':
        if action_type in ['crear', 'editar', 'eliminar']:
            flash('Los estatus están predefinidos y no pueden ser modificados.')
            return redirect(url_for('main.tickets_section', section=section))

    model_mapping = {
        'colores': (Color_Ticket,   'color_ticket',       'id_color'),
        'areas':   (Area,           'area',               'id_area'),
        'estatus': (Estatus_Ticket, 'status_descripcion', 'id_estatus_ticket'),
    }

    if section in model_mapping:
        model, field_name, pk_name = model_mapping[section]

        if action_type == 'crear':
            value = request.form.get(field_name, '').strip()
            if not value:
                flash('El campo requerido no puede estar vacío.')
                return redirect(url_for('main.tickets_section', section=section))

            if model.query.filter(getattr(model, field_name) == value).first():
                flash('Este registro ya existe en el sistema.')
            else:
                new_obj = model(**{field_name: value})
                if section == 'colores':
                    new_obj.descripcion_color_ticket = request.form.get('descripcion_color_ticket', '').strip() or None
                    dias_resolucion = request.form.get('dias_resolucion', '').strip()
                    new_obj.dias_resolucion = int(dias_resolucion) if dias_resolucion.isdigit() else 0
                db.session.add(new_obj)
                db.session.commit()
                flash('Registro creado con éxito.')

        elif action_type == 'editar' and item_id:
            value = request.form.get(field_name, '').strip()
            if not value:
                flash('El campo requerido no puede estar vacío.')
                return redirect(url_for('main.tickets_section', section=section))

            obj       = model.query.get_or_404(item_id)
            pk_column = getattr(model, pk_name)
            existing  = model.query.filter(getattr(model, field_name) == value, pk_column != item_id).first()

            if existing:
                flash('Ya existe otro registro con ese mismo valor.')
            else:
                setattr(obj, field_name, value)
                if section == 'colores':
                    obj.descripcion_color_ticket = request.form.get('descripcion_color_ticket', '').strip() or None
                    dias_resolucion = request.form.get('dias_resolucion', '').strip()
                    obj.dias_resolucion = int(dias_resolucion) if dias_resolucion.isdigit() else 0
                db.session.commit()
                flash('Registro actualizado con éxito.')

        elif action_type == 'eliminar' and item_id:
            obj = model.query.get_or_404(item_id)
            try:
                db.session.delete(obj)
                db.session.commit()
                flash('Registro eliminado correctamente.')
            except Exception as e:
                db.session.rollback()
                flash(f'No se pudo eliminar: puede tener registros relacionados. ({e})')

    return redirect(url_for('main.tickets_section', section=section))


# =========================================================================
# EDITAR TICKET INDIVIDUAL
# =========================================================================
@main_bp.route('/tickets/action/nuevo/crear', methods=['POST'])
@login_required
def tickets_create_modal():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    try:
        create_ticket_from_form()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}')

    return redirect(url_for('main.tickets'))


@main_bp.route('/tickets/action/nuevo/editar/<int:item_id>', methods=['POST'])
@login_required
def tickets_editar(item_id):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Ticket.query.get_or_404(item_id)

    try:
        fecha_emicion_str    = request.form.get('fecha_emicion')
        fecha_compromiso_str = request.form.get('fecha_compromiso')
        fecha_cierre_str     = request.form.get('fecha_cierre')
        acciones_correctivas_str   = request.form.get('acciones_correctivas', '').strip() or None
        problematica_str      = request.form.get('problematica', '').strip() or None

        registro.id_color_ticket     = request.form.get('id_color_ticket') or None
        registro.emisor              = request.form.get('emisor', '').strip() or None
        registro.id_area_responsable = request.form.get('id_area_responsable') or None
        registro.id_estatus_ticket   = request.form.get('id_estatus_ticket')
        registro.fecha_emicion       = datetime.strptime(fecha_emicion_str, '%Y-%m-%d').date() if fecha_emicion_str else None
        registro.fecha_cierre        = datetime.strptime(fecha_cierre_str, '%Y-%m-%d').date() if fecha_cierre_str else None

        color_obj = Color_Ticket.query.get(int(registro.id_color_ticket)) if registro.id_color_ticket else None
        registro.fecha_compromiso = None
        if registro.fecha_emicion and color_obj and color_obj.dias_resolucion is not None:
            registro.fecha_compromiso = registro.fecha_emicion + timedelta(days=color_obj.dias_resolucion)

        registro.dias_retrazo = 0
        if registro.fecha_compromiso:
            overdue_days = (datetime.now().date() - registro.fecha_compromiso).days
            registro.dias_retrazo = overdue_days if overdue_days > 0 else 0

        db.session.commit()
        flash('Ticket actualizado correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {e}')

    return redirect(url_for('main.tickets_section', section='nuevo'))


# =========================================================================
# ELIMINAR TICKET INDIVIDUAL
# =========================================================================
@main_bp.route('/tickets/action/nuevo/eliminar/<int:item_id>', methods=['POST'])
@login_required
def tickets_eliminar(item_id):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Ticket.query.get_or_404(item_id)

    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Ticket eliminado correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {e}')

    return redirect(url_for('main.tickets_section', section='nuevo'))