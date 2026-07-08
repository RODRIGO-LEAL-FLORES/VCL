from flask import render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db

from app.models.reclamaciones_models import (
    Categoria, Defecto, Ocurrencia, TipoDeReclamacion,
    EstatusReclamacion, Contenedor
)
from app.models.reclamaciones_models.reclamaciones import Reclamacion
from app.routes.main import main_bp
from app.models.cliente import Cliente


# =========================================================================
# VISTA PRINCIPAL: MENÚ DE OPCIONES DE RECLAMACIONES
# =========================================================================
@main_bp.route('/reclamaciones')
@login_required
def reclamaciones():
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    return render_template('reclamaciones/reclamaciones.html')


# =========================================================================
# CONTROLADOR DINÁMICO POR SECCIONES (VISTAS GET / POST)
# =========================================================================
@main_bp.route('/reclamaciones/<section>', methods=['GET', 'POST'])
@login_required
def reclamaciones_section(section):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    edit_id = request.args.get('edit_id', type=int)

    # --- LÓGICA PARA REGISTROS DE RECLAMACIONES ---
    if section == 'nuevo':
        if request.method == 'POST':
            try:
                fecha_reporte_str      = request.form.get('fecha_reporte')
                fecha_confirmacion_str = request.form.get('fecha_confirmacion')

                fecha_reporte      = datetime.strptime(fecha_reporte_str, '%Y-%m-%d').date() if fecha_reporte_str else None
                fecha_confirmacion = datetime.strptime(fecha_confirmacion_str, '%Y-%m-%d').date() if fecha_confirmacion_str else None
                fecha_contencion   = datetime.strptime(request.form.get('fecha_contencion'), '%Y-%m-%d').date() if request.form.get('fecha_contencion') else None
                fecha_CR_AC        = datetime.strptime(request.form.get('fecha_CR_AC'), '%Y-%m-%d').date() if request.form.get('fecha_CR_AC') else None
                fecha_cierre       = datetime.strptime(request.form.get('fecha_cierre'), '%Y-%m-%d').date() if request.form.get('fecha_cierre') else None

                dias_retrazo = 0
                if fecha_reporte and fecha_confirmacion:
                    dias_retrazo = (fecha_confirmacion - fecha_reporte).days

                nueva_reclamacion = Reclamacion(
                    id_reporte_cliente     = request.form.get('id_reporte_cliente', '').strip(),
                    issue                  = request.form.get('issue', '').strip(),
                    id_defecto             = request.form.get('id_defecto'),
                    id_categoria           = request.form.get('id_categoria'),
                    id_ocurrencia          = request.form.get('id_ocurrencia'),
                    id_numero_contenedor   = request.form.get('id_numero_contenedor') or None,
                    id_tipo_de_reclamacion = request.form.get('id_tipo_de_reclamacion'),
                    id_cliente             = request.form.get('id_cliente') or None,
                    id_estatus             = request.form.get('id_estatus'),
                    numero_parte           = request.form.get('numero_parte', '').strip() or None,
                    lote                   = request.form.get('lote', '').strip() or None,
                    cantidad_piezas        = int(request.form.get('cantidad_piezas', 0)) or None,
                    cantidad_kg            = float(request.form.get('cantidad_kg', 0)) or None,
                    fecha_reporte          = fecha_reporte,
                    fecha_confirmacion     = fecha_confirmacion,
                    fecha_contencion       = fecha_contencion,
                    fecha_CR_AC            = fecha_CR_AC,
                    fecha_cierre           = fecha_cierre,
                    dias_retrazo_al_reclamo = dias_retrazo,
                    periodo                = request.form.get('periodo', '').strip() or None,
                )
                db.session.add(nueva_reclamacion)
                db.session.commit()
                flash('Reclamación registrada exitosamente.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al guardar: {e}')

            return redirect(url_for('main.reclamaciones_section', section='nuevo'))

        # GET
        return render_template('reclamaciones/generar_registro.html',
            registros         = Reclamacion.query.order_by(Reclamacion.id.desc()).limit(20).all(),
            categorias        = Categoria.query.order_by(Categoria.categoria).all(),
            defectos          = Defecto.query.order_by(Defecto.defecto).all(),
            ocurrencias       = Ocurrencia.query.order_by(Ocurrencia.ocurrencia).all(),
            tipos_reclamacion = TipoDeReclamacion.query.order_by(TipoDeReclamacion.tipo_reclamacion).all(),
            estatus_list      = EstatusReclamacion.query.order_by(EstatusReclamacion.descripcion_status).all(),
            clientes          = Cliente.query.order_by(Cliente.nombre).all(),
            contenedores      = Contenedor.query.order_by(Contenedor.numero_contenedor).all(),
        )

    # --- LÓGICA PARA CATÁLOGOS ---
    mapping = {
        'categorias':        (Categoria,         'reclamaciones/categorias.html',       'categoria'),
        'defectos':          (Defecto,            'reclamaciones/defectos.html',          'descripcion'),
        'ocurrencias':       (Ocurrencia,         'reclamaciones/ocurrencias.html',       'ocurrencia'),
        'tipos_reclamacion': (TipoDeReclamacion,  'reclamaciones/tipos_reclamacion.html', 'tipo_reclamacion'),
        'estatus':           (EstatusReclamacion, 'reclamaciones/estatus.html',           'descripcion_status'),
        'clientes':          (Cliente,            'reclamaciones/clientes.html',          'nombre'),
        'contenedores':      (Contenedor,         'reclamaciones/contenedores.html',      'numero_contenedor'),
    }



    if section in mapping:
        model, template, field = mapping[section]

        # Paginación y búsqueda
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

    return redirect(url_for('main.reclamaciones_section', section='nuevo'))


# =========================================================================
# RUTAS POST: PROCESAMIENTO CRUD CENTRALIZADO Y SEGURO
# =========================================================================
@main_bp.route('/reclamaciones/action/<section>/<action_type>', methods=['POST'])
@main_bp.route('/reclamaciones/action/<section>/<action_type>/<int:item_id>', methods=['POST'])
@login_required
def reclamaciones_actions(section, action_type, item_id=None):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    model_mapping = {
        'categorias':        (Categoria,         'categoria',          'id_categorias'),
        'defectos':          (Defecto,            'defecto',            'id_defecto'),
        'ocurrencias':       (Ocurrencia,         'ocurrencia',         'id_ocurrencia'),
        'tipos_reclamacion': (TipoDeReclamacion,  'tipo_reclamacion',   'id_tipo_de_reclamacion'),
        'estatus':           (EstatusReclamacion, 'descripcion_status', 'id_estatus'),
        'clientes':          (Cliente,            'nombre',             'id_cliente'),
        'contenedores':      (Contenedor,         'numero_contenedor',  'id_numero_contenedor'),
    }

    if section in model_mapping:
        model, field_name, pk_name = model_mapping[section]

        if action_type == 'crear':
            value = request.form.get(field_name, '').strip()
            if not value:
                flash('El campo requerido no puede estar vacío.')
                return redirect(url_for('main.reclamaciones_section', section=section))

            if model.query.filter(getattr(model, field_name) == value).first():
                flash('Este registro ya existe en el sistema.')
            else:
                db.session.add(model(**{field_name: value}))
                db.session.commit()
                flash('Registro creado con éxito.')

        elif action_type == 'editar' and item_id:
            value = request.form.get(field_name, '').strip()
            if not value:
                flash('El campo requerido no puede estar vacío.')
                return redirect(url_for('main.reclamaciones_section', section=section))

            obj       = model.query.get_or_404(item_id)
            pk_column = getattr(model, pk_name)
            existing  = model.query.filter(getattr(model, field_name) == value, pk_column != item_id).first()

            if existing:
                flash('Ya existe otro registro con ese mismo valor.')
            else:
                setattr(obj, field_name, value)
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

    return redirect(url_for('main.reclamaciones_section', section=section))


# =========================================================================
# EDITAR RECLAMACIÓN INDIVIDUAL
# =========================================================================
@main_bp.route('/reclamaciones/action/nuevo/editar/<int:item_id>', methods=['POST'])
@login_required
def reclamaciones_editar(item_id):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Reclamacion.query.get_or_404(item_id)

    try:
        fecha_reporte_str      = request.form.get('fecha_reporte')
        fecha_confirmacion_str = request.form.get('fecha_confirmacion')

        registro.id_reporte_cliente     = request.form.get('id_reporte_cliente', '').strip()
        registro.issue                  = request.form.get('issue', '').strip()
        registro.id_defecto             = request.form.get('id_defecto')
        registro.id_categoria           = request.form.get('id_categoria')
        registro.id_ocurrencia          = request.form.get('id_ocurrencia')
        registro.id_numero_contenedor   = request.form.get('id_numero_contenedor') or None
        registro.id_tipo_de_reclamacion = request.form.get('id_tipo_de_reclamacion')
        registro.id_cliente             = request.form.get('id_cliente') or None
        registro.id_estatus             = request.form.get('id_estatus')
        registro.numero_parte           = request.form.get('numero_parte', '').strip() or None
        registro.lote                   = request.form.get('lote', '').strip() or None
        registro.cantidad_piezas        = int(request.form.get('cantidad_piezas', 0)) or None
        registro.cantidad_kg            = float(request.form.get('cantidad_kg', 0)) or None
        registro.periodo                = request.form.get('periodo', '').strip() or None

        registro.fecha_reporte      = datetime.strptime(fecha_reporte_str, '%Y-%m-%d').date() if fecha_reporte_str else None
        registro.fecha_confirmacion = datetime.strptime(fecha_confirmacion_str, '%Y-%m-%d').date() if fecha_confirmacion_str else None
        registro.fecha_contencion   = datetime.strptime(request.form.get('fecha_contencion'), '%Y-%m-%d').date() if request.form.get('fecha_contencion') else None
        registro.fecha_CR_AC        = datetime.strptime(request.form.get('fecha_CR_AC'), '%Y-%m-%d').date() if request.form.get('fecha_CR_AC') else None
        registro.fecha_cierre       = datetime.strptime(request.form.get('fecha_cierre'), '%Y-%m-%d').date() if request.form.get('fecha_cierre') else None

        if registro.fecha_reporte and registro.fecha_confirmacion:
            registro.dias_retrazo_al_reclamo = (registro.fecha_confirmacion - registro.fecha_reporte).days

        db.session.commit()
        flash('Reclamación actualizada correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {e}')

    return redirect(url_for('main.reclamaciones_section', section='nuevo'))


# =========================================================================
# ELIMINAR RECLAMACIÓN INDIVIDUAL
# =========================================================================
@main_bp.route('/reclamaciones/action/nuevo/eliminar/<int:item_id>', methods=['POST'])
@login_required
def reclamaciones_eliminar(item_id):
    if not current_user.puede_ver_reclamaciones:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Reclamacion.query.get_or_404(item_id)

    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Reclamación eliminada correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {e}')

    return redirect(url_for('main.reclamaciones_section', section='nuevo'))