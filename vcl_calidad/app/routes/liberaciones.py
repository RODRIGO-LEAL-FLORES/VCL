from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from app import db
from app.models.cliente import Cliente
from app.models.scrap_models.catalogos import Maquina, TipoLaminacion
from app.models.liberaciones_models import Liberacion, EstatusLiberacion
from app.routes.main import main_bp
from flask_login import login_required, current_user



def build_page_numbers(current, total_pages):
    pages = []
    for n in range(1, total_pages + 1):
        if n == 1 or n == total_pages or abs(n - current) <= 1:
            pages.append(n)
        elif pages and pages[-1] != '...':
            pages.append('...')
    return pages


@main_bp.route('/liberaciones')
@login_required
def liberaciones():
    if not current_user.puede_gestionar_liberaciones:
        flash("No tienes autorización para acceder al módulo de liberaciones.")
        return redirect(url_for('main.home'))

    return render_template('liberaciones/liberaciones.html')


@main_bp.route('/liberaciones/<section>', methods=['GET', 'POST'])
@login_required
def liberaciones_section(section):
    if not current_user.puede_gestionar_liberaciones:
        flash("No tienes autorización para acceder al módulo de liberaciones.")
        return redirect(url_for('main.home'))

    if current_user.rol.id != 4 and section not in ['maquinas_status']:
        flash("No tienes autorización para acceder a esta sección de liberaciones.")
        return redirect(url_for('main.liberaciones_section', section='estatus'))

    edit_id = request.args.get('edit_id', type=int)

    if section == 'nuevo':
        edit_registro = Liberacion.query.get(edit_id) if edit_id else None

        if request.method == 'POST':
            try:
                motivo = request.form.get('motivo', '').strip()
                fecha_liberacion = request.form.get('fecha_liberacion')
                hora_liberacion = request.form.get('hora_liberacion')
                id_cliente = request.form.get('id_cliente')
                id_tipo_laminacion = request.form.get('id_tipo_laminacion')
                id_maquina = request.form.get('id_maquina')
                id_status = request.form.get('id_status')

                if not motivo or not fecha_liberacion or not hora_liberacion or not id_cliente or not id_tipo_laminacion or not id_maquina or not id_status:
                    flash('Todos los campos son obligatorios.')
                    return redirect(url_for('main.liberaciones_section', section='nuevo'))

                nueva_liberacion = Liberacion(
                    motivo=motivo,
                    fecha_liberacion=datetime.strptime(fecha_liberacion, '%Y-%m-%d').date(),
                    hora_liberacion=datetime.strptime(hora_liberacion, '%H:%M').time(),
                    id_cliente=int(id_cliente),
                    id_tipo_laminacion=int(id_tipo_laminacion),
                    id_maquina=int(id_maquina),
                    id_status=int(id_status),
                    id_usuario=current_user.id,
                )
                db.session.add(nueva_liberacion)
                db.session.commit()
                flash('Liberación registrada correctamente.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al guardar la liberación: {e}')
            return redirect(url_for('main.liberaciones_section', section='nuevo'))

        # --- Búsqueda + paginación (10 registros por página) ---
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '', type=str).strip()
        per_page = 10

        query = Liberacion.query \
            .outerjoin(Cliente, Liberacion.id_cliente == Cliente.id_cliente) \
            .outerjoin(Maquina, Liberacion.id_maquina == Maquina.id_maquina) \
            .outerjoin(TipoLaminacion, Liberacion.id_tipo_laminacion == TipoLaminacion.id_tipo_laminacion) \
            .outerjoin(EstatusLiberacion, Liberacion.id_status == EstatusLiberacion.id_estatus)

        if search_query:
            like = f'%{search_query}%'
            query = query.filter(db.or_(
                Cliente.nombre.ilike(like),
                Maquina.nombre.ilike(like),
                TipoLaminacion.especificacion.ilike(like),
                EstatusLiberacion.descripcion_status.ilike(like),
                Liberacion.motivo.ilike(like),
            ))

        pagination = query.order_by(Liberacion.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        registros = pagination.items
        total = pagination.total
        start = (page - 1) * per_page + 1 if total > 0 else 0
        end = min(page * per_page, total)

        return render_template('liberaciones/generar_liberacion.html',
            registros=registros,
            edit_registro=edit_registro,
            clientes=Cliente.query.order_by(Cliente.nombre).all(),
            maquinas=Maquina.query.order_by(Maquina.nombre).all(),
            tipos_laminacion=TipoLaminacion.query.order_by(TipoLaminacion.especificacion).all(),
            estatus_list=EstatusLiberacion.query.order_by(EstatusLiberacion.descripcion_status).all(),
            page=page,
            total_pages=pagination.pages,
            page_numbers=build_page_numbers(page, pagination.pages) if pagination.pages else [],
            search_query=search_query,
            total_results=total,
            start=start,
            end=end,
        )

    if section == 'maquinas_status':
        search_query = request.args.get('search', '', type=str).strip()

        maquinas = Maquina.query.order_by(Maquina.nombre).all()
        maquinas_estado = []
        for maquina in maquinas:
            ultima_liberacion = Liberacion.query.filter_by(id_maquina=maquina.id_maquina).order_by(
                Liberacion.fecha_liberacion.desc(),
                Liberacion.hora_liberacion.desc(),
                Liberacion.id.desc()
            ).first()
            maquinas_estado.append({
                'maquina': maquina,
                'liberacion': ultima_liberacion,
            })

        if search_query:
            search_lower = search_query.lower()
            maquinas_estado = [row for row in maquinas_estado if search_lower in row['maquina'].nombre.lower() or (
                row['liberacion'] and row['liberacion'].estatus and search_lower in row['liberacion'].estatus.descripcion_status.lower()
            )]

        return render_template('liberaciones/maquinas_status.html', maquinas_estado=maquinas_estado, search_query=search_query)

    mapping = {
        'clientes':          (Cliente, 'liberaciones/clientes.html', 'nombre', 'id_cliente'),
        'maquinas':          (Maquina, 'liberaciones/maquinas_l.html', 'nombre', 'id_maquina'),
        'tipos_laminacion':  (TipoLaminacion, 'liberaciones/tipos_laminacion.html', 'especificacion', 'id_tipo_laminacion'),
        'estatus':           (EstatusLiberacion, 'liberaciones/status_liberaciones.html', 'descripcion_status', 'id_estatus'),
    }

    if section in mapping:
        model, template, field, pk_name = mapping[section]
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '', type=str).strip()
        per_page = 20

        query = model.query
        if search_query:
            query = query.filter(getattr(model, field).ilike(f'%{search_query}%'))

        pagination = query.order_by(getattr(model, field)).paginate(page=page, per_page=per_page, error_out=False)
        total = pagination.total
        start = (page - 1) * per_page + 1 if total > 0 else 0
        end = min(page * per_page, total)

        return render_template(template,
            items=pagination.items,
            edit_item=model.query.get(edit_id) if edit_id else None,
            page=page,
            total_pages=pagination.pages,
            page_numbers=build_page_numbers(page, pagination.pages),
            search_query=search_query,
            total_results=total,
            start=start,
            end=end,
            section=section,
        )

    return redirect(url_for('main.liberaciones'))


@main_bp.route('/liberaciones/action/<section>/<action_type>', methods=['POST'])
@main_bp.route('/liberaciones/action/<section>/<action_type>/<int:item_id>', methods=['POST'])
@login_required
def liberaciones_actions(section, action_type, item_id=None):
    if not current_user.puede_gestionar_liberaciones:
        flash("No tienes autorización para gestionar liberaciones.")
        return redirect(url_for('main.home'))

    if section == 'clientes':
        model = Cliente
        field_name = 'nombre'
        pk_name = 'id_cliente'
    elif section == 'maquinas':
        model = Maquina
        field_name = 'nombre'
        pk_name = 'id_maquina'
    elif section == 'tipos_laminacion':
        model = TipoLaminacion
        field_name = 'especificacion'
        pk_name = 'id_tipo_laminacion'
    elif section == 'estatus':
        model = EstatusLiberacion
        field_name = 'descripcion_status'
        pk_name = 'id_estatus'
    elif section == 'nuevo':
        model = Liberacion
        field_name = None
        pk_name = 'id'
    else:
        return redirect(url_for('main.liberaciones_section', section=section))

    if section == 'nuevo' and action_type == 'editar' and item_id:
        motivo = request.form.get('motivo', '').strip()
        fecha_liberacion = request.form.get('fecha_liberacion')
        hora_liberacion = request.form.get('hora_liberacion')
        id_cliente = request.form.get('id_cliente')
        id_tipo_laminacion = request.form.get('id_tipo_laminacion')
        id_maquina = request.form.get('id_maquina')
        id_status = request.form.get('id_status')

        if not motivo or not fecha_liberacion or not hora_liberacion or not id_cliente or not id_tipo_laminacion or not id_maquina or not id_status:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('main.liberaciones_section', section='nuevo', edit_id=item_id))

        obj = model.query.get_or_404(item_id)
        try:
            obj.motivo = motivo
            obj.fecha_liberacion = datetime.strptime(fecha_liberacion, '%Y-%m-%d').date()
            obj.hora_liberacion = datetime.strptime(hora_liberacion, '%H:%M').time()
            obj.id_cliente = int(id_cliente)
            obj.id_tipo_laminacion = int(id_tipo_laminacion)
            obj.id_maquina = int(id_maquina)
            obj.id_status = int(id_status)
            db.session.commit()
            flash('Liberación actualizada con éxito.')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la liberación: {e}')

    elif section == 'nuevo' and action_type == 'eliminar' and item_id:
        obj = model.query.get_or_404(item_id)
        try:
            db.session.delete(obj)
            db.session.commit()
            flash('Liberación eliminada correctamente.')
        except Exception as e:
            db.session.rollback()
            flash(f'No se pudo eliminar la liberación: {e}')

    elif section != 'nuevo' and action_type == 'crear':
        value = request.form.get(field_name, '').strip()
        if not value:
            flash('El campo requerido no puede estar vacío.')
            return redirect(url_for('main.liberaciones_section', section=section))

        if model.query.filter(getattr(model, field_name) == value).first():
            flash('Este registro ya existe en el sistema.')
        else:
            obj_kwargs = {field_name: value}
            if section == 'maquinas':
                obj_kwargs['descripcion'] = request.form.get('descripcion', '').strip() or None
            db.session.add(model(**obj_kwargs))
            db.session.commit()
            flash('Registro creado con éxito.')

    elif section != 'nuevo' and action_type == 'editar' and item_id:
        value = request.form.get(field_name, '').strip()
        if not value:
            flash('El campo requerido no puede estar vacío.')
            return redirect(url_for('main.liberaciones_section', section=section))

        obj = model.query.get_or_404(item_id)
        existing = model.query.filter(getattr(model, field_name) == value, getattr(model, pk_name) != item_id).first()
        if existing:
            flash('Ya existe otro registro con ese mismo valor.')
        else:
            setattr(obj, field_name, value)
            if section == 'maquinas':
                obj.descripcion = request.form.get('descripcion', '').strip() or None
            db.session.commit()
            flash('Registro actualizado con éxito.')

    elif section != 'nuevo' and action_type == 'eliminar' and item_id:
        obj = model.query.get_or_404(item_id)
        try:
            db.session.delete(obj)
            db.session.commit()
            flash('Registro eliminado correctamente.')
        except Exception as e:
            db.session.rollback()
            flash(f'No se pudo eliminar el registro: {e}')

    return redirect(url_for('main.liberaciones_section', section=section))