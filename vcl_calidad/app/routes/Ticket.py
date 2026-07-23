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
    raise ValueError("  NO HAY ESTATUS DISPONIBLES. Ejecute init_fixed_estatus() primero.")


def get_cerrados_ids():
    """
    Devuelve el conjunto de IDs de estatus que se consideran 'Cerrado'.
    Se usa para saber si un ticket ya cerró o sigue abierto al calcular el retraso.
    """
    return {e.id_estatus_ticket for e in Estatus_Ticket.query.filter_by(status_descripcion='Cerrado').all()}


def calcular_dias_retrazo(ticket, cerrados_ids=None):
    """
    Calcula los días de retraso de un ticket EN TIEMPO REAL, sin depender del
    valor guardado en la columna `dias_retrazo` (que solo se actualizaba al
    crear/editar el ticket y por eso se desincronizaba con el paso de los días).

    - Si el ticket no tiene fecha_compromiso -> 0.
    - Si el ticket ya está Cerrado -> retraso fijo = fecha_cierre - fecha_compromiso
      (si no tiene fecha_cierre, se asume 0).
    - Si el ticket sigue abierto -> retraso = hoy - fecha_compromiso.
    - Nunca retorna valores negativos (se limita a 0 como mínimo).
    """
    if not ticket.fecha_compromiso:
        return 0

    if cerrados_ids is None:
        cerrados_ids = get_cerrados_ids()

    if ticket.id_estatus_ticket in cerrados_ids:
        if ticket.fecha_cierre:
            dias = (ticket.fecha_cierre - ticket.fecha_compromiso).days
        else:
            dias = 0
    else:
        dias = (datetime.now().date() - ticket.fecha_compromiso).days

    return dias if dias > 0 else 0


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
    
    # Calculamos el retraso EN TIEMPO REAL para cada ticket mostrado en esta
    # página (se usa en el modal "Ver" de generar_registro.html).
    cerrados_ids = get_cerrados_ids()
    retraso_map = {t.id_folio_ticket: calcular_dias_retrazo(t, cerrados_ids) for t in items}

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
        retraso_map=retraso_map,
    )

@main_bp.route('/tickets/mis-pendientes')
@login_required
def mis_tickets():
    closed_id = get_status_id('Cerrado') or 3
    tickets = Ticket.query.filter(
        Ticket.id_area_responsable == current_user.id_area,
        Ticket.id_estatus_ticket != closed_id
    ).order_by(Ticket.fecha_compromiso.asc()).all()

    cerrados_ids = {closed_id}
    retraso_map = {t.id_folio_ticket: calcular_dias_retrazo(t, cerrados_ids) for t in tickets}

    return render_template('tickets/mis_tickets.html', tickets=tickets, today=datetime.now().date(), closed_id=closed_id, retraso_map=retraso_map)


@main_bp.route('/tickets/seguimiento')
@login_required
def seguimiento_tickets():
    closed_id = get_status_id('Cerrado') or 3
    tickets = Ticket.query.filter(
        Ticket.id_area_responsable == current_user.id_area,
        Ticket.id_estatus_ticket != closed_id
    ).order_by(Ticket.fecha_compromiso.asc()).all()

    cerrados_ids = {closed_id}
    retraso_map = {t.id_folio_ticket: calcular_dias_retrazo(t, cerrados_ids) for t in tickets}

    return render_template('tickets/seguimiento_tickets.html', tickets=tickets, today=datetime.now().date(), closed_id=closed_id, retraso_map=retraso_map)


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
                ticket.dias_retrazo = calcular_dias_retrazo(ticket, {cerrado_id})
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

            ticket.dias_retrazo = calcular_dias_retrazo(ticket, {cerrado_id})

            db.session.commit()
            flash('Ticket actualizado correctamente.')
            return redirect(url_for('main.ticket_detail', item_id=item_id))

    dias_retrazo = calcular_dias_retrazo(ticket, {cerrado_id})

    return render_template('tickets/ticket_detail.html', ticket=ticket, today=datetime.now().date(), closed_id=cerrado_id, pendiente_validacion_id=pendiente_validacion_id, dias_retrazo=dias_retrazo)


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

        registro.dias_retrazo = calcular_dias_retrazo(registro)

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



    

# =========================================================================
# REPORTES DE TICKETS (TODOS LOS USUARIOS CON ACCESO AL MÓDULO)
# =========================================================================
def _reportes_filtered_query():
    search_query = request.args.get('search', '', type=str).strip()
    area_id = request.args.get('area', type=int)
    color_id = request.args.get('color', type=int)
    estatus_id = request.args.get('estatus', type=int)
    fecha_desde = request.args.get('fecha_desde', type=str)
    fecha_hasta = request.args.get('fecha_hasta', type=str)

    query = Ticket.query

    if search_query:
        query = query.filter(cast(Ticket.id_folio_ticket, String).ilike(f'%{search_query}%'))
    if area_id:
        query = query.filter(Ticket.id_area_responsable == area_id)
    if color_id:
        query = query.filter(Ticket.id_color_ticket == color_id)
    if estatus_id:
        query = query.filter(Ticket.id_estatus_ticket == estatus_id)
    if fecha_desde:
        try:
            query = query.filter(Ticket.fecha_emicion >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            pass
    if fecha_hasta:
        try:
            query = query.filter(Ticket.fecha_emicion <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    return query.order_by(Ticket.id_folio_ticket.desc())


@main_bp.route('/tickets/reportes')
@login_required
def reportes_tickets():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    page = request.args.get('page', 1, type=int)
    items_per_page = 20

    query = _reportes_filtered_query()
    total_results = query.count()
    paginated = query.paginate(page=page, per_page=items_per_page, error_out=False)
    items = paginated.items
    total_pages = paginated.pages
    start = (page - 1) * items_per_page + 1 if items else 0
    end = min(start + len(items) - 1, total_results)

    page_numbers = []
    for i in range(1, total_pages + 1):
        if i == 1 or i == total_pages or abs(i - page) <= 1:
            page_numbers.append(i)
        elif page_numbers[-1] != '...':
            page_numbers.append('...')

    area_map = {a.id_area: a.area for a in Area.query.all()}
    color_map = {c.id_color: c.color_ticket for c in Color_Ticket.query.all()}
    estatus_map = {e.id_estatus_ticket: e.status_descripcion for e in Estatus_Ticket.query.all()}

    # Calculamos el retraso EN TIEMPO REAL para cada ticket mostrado en esta
    # página, en lugar de usar la columna dias_retrazo (que puede estar
    # desactualizada si nadie ha vuelto a editar el ticket).
    cerrados_ids = get_cerrados_ids()
    retraso_map = {t.id_folio_ticket: calcular_dias_retrazo(t, cerrados_ids) for t in items}

    return render_template(
        'tickets/reportes.html',
        items=items,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        start=start,
        end=end,
        search_query=request.args.get('search', ''),
        page_numbers=page_numbers,
        colores=Color_Ticket.query.order_by(Color_Ticket.color_ticket).all(),
        areas=Area.query.order_by(Area.area).all(),
        estatus_list=Estatus_Ticket.query.order_by(Estatus_Ticket.status_descripcion).all(),
        selected_area=request.args.get('area', type=int),
        selected_color=request.args.get('color', type=int),
        selected_estatus=request.args.get('estatus', type=int),
        fecha_desde=request.args.get('fecha_desde', ''),
        fecha_hasta=request.args.get('fecha_hasta', ''),
        area_map=area_map,
        color_map=color_map,
        estatus_map=estatus_map,
        retraso_map=retraso_map,
        today=datetime.now().date(),
    )


@main_bp.route('/tickets/reportes/exportar')
@login_required
def reportes_exportar():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    import csv
    import io
    from flask import Response

    tickets_list = _reportes_filtered_query().all()

    area_map = {a.id_area: a.area for a in Area.query.all()}
    color_map = {c.id_color: c.color_ticket for c in Color_Ticket.query.all()}
    estatus_map = {e.id_estatus_ticket: e.status_descripcion for e in Estatus_Ticket.query.all()}
    cerrados_ids = get_cerrados_ids()

    output = io.StringIO()
    output.write('\ufeff')  # BOM para que Excel abra bien los acentos
    writer = csv.writer(output)
    writer.writerow([
        'Folio', 'Emisor', 'Área', 'Color', 'Estatus',
        'Fecha Emisión', 'Fecha Compromiso', 'Fecha Cierre',
        'Días Retraso', 'Problemática', 'Acción Correctiva', 'Evidencia Resolución'
    ])

    for t in tickets_list:
        writer.writerow([
            t.id_folio_ticket,
            t.emisor or '',
            area_map.get(t.id_area_responsable, ''),
            color_map.get(t.id_color_ticket, ''),
            estatus_map.get(t.id_estatus_ticket, ''),
            t.fecha_emicion.strftime('%Y-%m-%d') if t.fecha_emicion else '',
            t.fecha_compromiso.strftime('%Y-%m-%d') if t.fecha_compromiso else '',
            t.fecha_cierre.strftime('%Y-%m-%d') if t.fecha_cierre else '',
            calcular_dias_retrazo(t, cerrados_ids),
            (t.problematica or '').replace('\n', ' '),
            (t.accion_correctiva or '').replace('\n', ' '),
            (t.evidencia_resolucion or '').replace('\n', ' '),
        ])

    filename = f"reporte_tickets_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
    
    
@main_bp.route('/tickets/reportes/pdf')
@login_required
def reportes_pdf():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    import io
    import os
    from collections import Counter

    import matplotlib
    matplotlib.use('Agg')  # backend sin interfaz gráfica, necesario en servidor
    import matplotlib.pyplot as plt

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, HRFlowable
    )

    # ---------------------------------------------------------------
    # 0. Mapeo de nombres de color -> color real (hex) para las gráficas
    # ---------------------------------------------------------------
    COLOR_HEX_MAP = {
        'rojo':     '#ef4444',
        'naranja':  '#f97316',
        'amarillo': '#eab308',
        'verde':    '#22c55e',
        'azul':     '#3b82f6',
        'morado':   '#a855f7',
        'violeta':  '#a855f7',
        'rosa':     '#ec4899',
        'gris':     '#6b7280',
        'negro':    '#111827',
        'blanco':   '#e5e7eb',
        'cafe':     '#92400e',
        'café':     '#92400e',
    }

    def color_for(name):
        return COLOR_HEX_MAP.get((name or '').strip().lower(), '#94a3b8')  # gris por defecto

    # ---------------------------------------------------------------
    # 1. Obtener los tickets ya filtrados (misma lógica que reportes_tickets)
    # ---------------------------------------------------------------
    tickets_list = _reportes_filtered_query().all()

    area_map = {a.id_area: a.area for a in Area.query.all()}
    color_map = {c.id_color: c.color_ticket for c in Color_Ticket.query.all()}
    estatus_map = {e.id_estatus_ticket: e.status_descripcion for e in Estatus_Ticket.query.all()}

    cerrados_ids = get_cerrados_ids()
    # Calculamos el retraso real de cada ticket una sola vez y lo reutilizamos
    # tanto en los totales/gráficas como en la tabla de detalle del PDF.
    retraso_por_ticket = {t.id_folio_ticket: calcular_dias_retrazo(t, cerrados_ids) for t in tickets_list}

    total = len(tickets_list)
    abiertos = sum(1 for t in tickets_list if t.id_estatus_ticket not in cerrados_ids)
    cerrados = total - abiertos
    con_retraso = sum(1 for t in tickets_list if retraso_por_ticket[t.id_folio_ticket] > 0)

    por_area = Counter(area_map.get(t.id_area_responsable, 'Sin área') for t in tickets_list)
    por_color = Counter(color_map.get(t.id_color_ticket, 'Sin color') for t in tickets_list)
    por_estatus = Counter(estatus_map.get(t.id_estatus_ticket, 'Sin estatus') for t in tickets_list)

    # Descripción de filtros aplicados (para el texto de portada)
    filtros_aplicados = []
    if request.args.get('search'):
        filtros_aplicados.append(f"folio contiene '{request.args.get('search')}'")
    if request.args.get('area', type=int):
        a_obj = Area.query.get(request.args.get('area', type=int))
        if a_obj:
            filtros_aplicados.append(f"área = {a_obj.area}")
    if request.args.get('color', type=int):
        c_obj = Color_Ticket.query.get(request.args.get('color', type=int))
        if c_obj:
            filtros_aplicados.append(f"color = {c_obj.color_ticket}")
    if request.args.get('estatus', type=int):
        e_obj = Estatus_Ticket.query.get(request.args.get('estatus', type=int))
        if e_obj:
            filtros_aplicados.append(f"estatus = {e_obj.status_descripcion}")
    if request.args.get('fecha_desde'):
        filtros_aplicados.append(f"desde {request.args.get('fecha_desde')}")
    if request.args.get('fecha_hasta'):
        filtros_aplicados.append(f"hasta {request.args.get('fecha_hasta')}")

    filtros_texto = "; ".join(filtros_aplicados) if filtros_aplicados else "sin filtros (todos los tickets registrados)"

    # ---------------------------------------------------------------
    # 2. Generar las gráficas con matplotlib y guardarlas en memoria (PNG)
    # ---------------------------------------------------------------
    plt.rcParams['font.family'] = 'DejaVu Sans'

    def make_bar_chart(counter, title, bar_colors=None, default_color='#0f172a'):
        buf = io.BytesIO()
        labels = list(counter.keys())
        values = list(counter.values())
        colors_list = bar_colors if bar_colors else [default_color] * len(labels)
        fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=160)
        bars = ax.bar(labels, values, color=colors_list, edgecolor='white', linewidth=0.6)
        ax.set_title(title, fontsize=13, fontweight='bold', color='#0f172a', pad=12)
        ax.tick_params(axis='x', rotation=20, labelsize=9)
        ax.tick_params(axis='y', labelsize=8)
        ax.set_facecolor('#ffffff')
        fig.patch.set_facecolor('#ffffff')
        for spine in ['top', 'right', 'left']:
            ax.spines[spine].set_visible(False)
        ax.yaxis.grid(True, color='#e5e7eb', linewidth=0.7)
        ax.set_axisbelow(True)
        for b in bars:
            height = b.get_height()
            ax.annotate(f'{int(height)}', xy=(b.get_x() + b.get_width() / 2, height),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', fontsize=8, fontweight='bold', color='#0f172a')
        fig.tight_layout()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf

    chart_area = make_bar_chart(por_area, 'Tickets por Área', default_color='#0ea5a4') if por_area else None
    chart_estatus = make_bar_chart(por_estatus, 'Tickets por Estatus', default_color='#38bdf8') if por_estatus else None

    color_labels = list(por_color.keys())
    color_bar_colors = [color_for(lbl) for lbl in color_labels]
    chart_color = make_bar_chart(por_color, 'Tickets por Color', bar_colors=color_bar_colors) if por_color else None

    # ---------------------------------------------------------------
    # 3. Rutas de los logos (carpeta static)
    # ---------------------------------------------------------------
    static_folder = current_app.static_folder
    logo_path = os.path.join(static_folder, 'logo2.jpg')
   

    # ---------------------------------------------------------------
    # 4. Armar el PDF con reportlab
    # ---------------------------------------------------------------
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, pagesize=letter,
        topMargin=2.2 * cm, bottomMargin=2 * cm,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleCustom', parent=styles['Title'], fontSize=22,
                                  textColor=colors.HexColor('#0f172a'), spaceAfter=2)
    subtitle_style = ParagraphStyle('SubtitleCustom', parent=styles['Normal'], fontSize=10.5,
                                     textColor=colors.HexColor('#475569'), spaceAfter=2)
    desc_style = ParagraphStyle('DescCustom', parent=styles['Normal'], fontSize=9.5,
                                 textColor=colors.HexColor('#64748b'), leading=14)
    heading_style = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=14,
                                    textColor=colors.HexColor('#0f172a'), spaceBefore=18, spaceAfter=10)
    chip_style = ParagraphStyle('ChipStyle', parent=styles['Normal'], fontSize=9,
                                 textColor=colors.HexColor('#0f172a'), alignment=TA_CENTER)

    story = []

    # ---- Encabezado con logos ----
    if os.path.exists(logo_path):
        logo_cell = Image(logo_path, width=1.6 * cm, height=1.6 * cm)
    else:
        logo_cell = Paragraph("", styles['Normal'])

    header_text = [
        Paragraph("VC LAMINATIONS", ParagraphStyle('Brand', parent=styles['Normal'], fontSize=13,
                                                      textColor=colors.HexColor('#0f172a'), leading=15,
                                                      fontName='Helvetica-Bold')),
        Paragraph("Lapham-Hickey Steel", ParagraphStyle('BrandSub', parent=styles['Normal'], fontSize=9,
                                                          textColor=colors.HexColor('#64748b'))),
    ]

   

    header_table = Table(
        [[logo_cell, header_text]],
        colWidths=[2.2 * cm, 10.6 * cm, 3.8 * cm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 16))

    # ---- Portada / texto de reporte ----
    story.append(Paragraph("Reporte de Tickets", title_style))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d de %B de %Y, %H:%M')} hrs por {current_user.nombre}",
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Este documento presenta un resumen estadístico y el detalle de los tickets del sistema de "
        "gestión de reclamaciones de VC Laminations. Incluye totales generales, distribución de tickets "
        "por área responsable, por color de prioridad y por estatus de seguimiento, así como la tabla "
        f"completa de tickets incluidos en este corte. Filtros aplicados: {filtros_texto}.",
        desc_style
    ))
    story.append(Spacer(1, 18))

    # --- Resumen en tabla (tarjetas) ---
    resumen_data = [
        ['TOTAL DE TICKETS', 'ABIERTOS', 'CERRADOS', 'CON RETRASO'],
        [str(total), str(abiertos), str(cerrados), str(con_retraso)],
    ]
    resumen_table = Table(resumen_data, colWidths=[4.1 * cm] * 4)
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f1f5f9')),
        ('LINEBELOW', (0, 0), (-1, 0), 0, colors.white),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
    ]))
    story.append(resumen_table)

    # --- Gráficas dentro de "tarjetas" con margen y borde ---
    def chart_card(img_buf, width_cm=16, height_cm=8.6):
        img = Image(img_buf, width=width_cm * cm, height=height_cm * cm)
        card = Table([[img]], colWidths=[width_cm * cm + 0.8 * cm])
        card.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        return card

    story.append(Paragraph("Gráficas", heading_style))
    if chart_area:
        story.append(chart_card(chart_area))
        story.append(Spacer(1, 14))
    if chart_estatus:
        story.append(chart_card(chart_estatus))
        story.append(Spacer(1, 14))
    if chart_color:
        story.append(chart_card(chart_color))

    story.append(PageBreak())

    # --- Tabla detallada ---
    story.append(Paragraph("Detalle de Tickets", heading_style))
    table_data = [['Folio', 'Emisor', 'Área', 'Color', 'Estatus', 'Emisión', 'Cierre', 'Retraso']]
    for t in tickets_list:
        table_data.append([
            str(t.id_folio_ticket),
            t.emisor or '-',
            area_map.get(t.id_area_responsable, '-'),
            color_map.get(t.id_color_ticket, '-'),
            estatus_map.get(t.id_estatus_ticket, '-'),
            t.fecha_emicion.strftime('%Y-%m-%d') if t.fecha_emicion else '-',
            t.fecha_cierre.strftime('%Y-%m-%d') if t.fecha_cierre else '-',
            str(retraso_por_ticket[t.id_folio_ticket]),
        ])

    detail_table = Table(table_data, repeatRows=1,
                          colWidths=[1.6*cm, 2.6*cm, 2.4*cm, 2*cm, 2.6*cm, 2.2*cm, 2.2*cm, 1.6*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(detail_table)

    # ---- Pie de página con número de página ----
    def add_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#94a3b8'))
        canvas_obj.drawString(2.2 * cm, 1.2 * cm, "VC Laminations · Sistema de Gestión de Tickets")
        canvas_obj.drawRightString(letter[0] - 2.2 * cm, 1.2 * cm, f"Página {doc_obj.page}")
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_buffer.seek(0)

    from flask import Response
    filename = f"reporte_tickets_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )