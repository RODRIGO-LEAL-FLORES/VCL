from flask import render_template, request, redirect, url_for, session, flash
from datetime import datetime
from app import db

# Importaciones de los modelos del módulo de Scrap y generales
from app.models.scrap_models import (
    Scrap, Maquina, Operador, Turno, DefectoScrap, 
    ClasificacionScrap, Supervisor, TipoAcero, EstatusScrap
)
from app.models.cliente import Cliente  # Modelo de Cliente corregido en singular
from app.routes.main import main_bp

from flask_login import login_required, login_user, current_user
from datetime import datetime


from flask import jsonify



# =========================================================================
# VISTA PRINCIPAL: MENÚ DE OPCIONES DE SCRAP
# =========================================================================
@main_bp.route('/scrap')
@login_required
def scrap():
    print(f"Usuario actual: {current_user.rol.id}")
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))
    
    
        
    return render_template('scrap/scrap.html')





# =========================================================================
# CONTROLADOR DINÁMICO POR SECCIONES (VISTAS GET)
# =========================================================================
@main_bp.route('/scrap/<section>', methods=['GET', 'POST'])
@login_required
def scrap_section(section):
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    edit_id = request.args.get('edit_id', type=int)

    # --- LÓGICA PARA REGISTROS DE SCRAP ---
    if section == 'nuevo':
        if request.method == 'POST':
            # 1. Captura de inputs manuales
            hora_manual = request.form.get('hora_registro')
            fecha_manual = request.form.get('fecha_registro')

            # 2. Determinar Turno y Fecha
            # Si hay hora manual, calculamos el turno basado en esa hora; si no, hora actual
            if hora_manual:
                hora_dt = datetime.strptime(hora_manual, '%H:%M').time()
                turno_det = Turno.query.filter(Turno.hora_inicio <= hora_dt, Turno.hora_fin > hora_dt).first()
                # Combinar fecha y hora
                fecha_final = datetime.strptime(f"{fecha_manual} {hora_manual}", '%Y-%m-%d %H:%M') if fecha_manual else datetime.now()
            else:
                hora_actual = datetime.now().time()
                turno_det = Turno.query.filter(Turno.hora_inicio <= hora_actual, Turno.hora_fin > hora_actual).first()
                fecha_final = datetime.now()

            # 3. Guardar el nuevo registro
            try:
                nuevo_registro = Scrap(
                    id_maquina=request.form.get('id_maquina'),
                    id_operador=request.form.get('id_operador'),
                    id_turno=turno_det.id_turno if turno_det else 1,
                    id_defecto_scrap=request.form.get('id_defecto_scrap'),
                    id_clasificacion=request.form.get('id_clasificacion'),
                    id_supervisor=request.form.get('id_supervisor'),
                    id_cliente=request.form.get('id_cliente'),
                    id_tipo_acero=request.form.get('id_tipo_acero'),
                    id_estatus_scrap=request.form.get('id_estatus_scrap'),
                    numero_parte=request.form.get('numero_parte', '').strip(),
                    lote=request.form.get('lote', '').strip(),
                    peso=float(request.form.get('peso', 0)),
                    cantidad_retrabajado=int(request.form.get('cantidad_retrabajado', 0)),
                    cantidad_ng=int(request.form.get('cantidad_ng', 0)),
                    usuario_registro_id=current_user.id,
                    fecha_registro=fecha_final
                )
                db.session.add(nuevo_registro)
                db.session.commit()
                flash('Registro generado exitosamente.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al guardar: {e}')
            
            return redirect(url_for('main.scrap_section', section='nuevo'))

        # GET: Renderizar formulario con datos para selectores
        return render_template('scrap/generar_registro.html',
            registros=Scrap.query.order_by(Scrap.id.desc()).limit(20).all(),
            maquinas=Maquina.query.all(),
            operadores=Operador.query.all(),
            defectos=DefectoScrap.query.all(),
            clasificaciones=ClasificacionScrap.query.all(),
            supervisores=Supervisor.query.all(),
            clientes=Cliente.query.all(),
            estatus_list=EstatusScrap.query.all(),
            tipos_acero=TipoAcero.query.all()
        )

    # --- LÓGICA PARA CATÁLOGOS ---
    mapping = {
        'maquinas': (Maquina, 'scrap/maquinas.html', 'nombre'),
        'operadores': (Operador, 'scrap/operadores.html', 'nombre'),
        'turnos': (Turno, 'scrap/turnos.html', 'nombre_turno'),
        'defectos': (DefectoScrap, 'scrap/scrap_defectos.html', 'defecto'),
        'clasificaciones': (ClasificacionScrap, 'scrap/clasificaciones.html', 'clasificacion'),
        'supervisores': (Supervisor, 'scrap/supervisores.html', 'nombre'),
        'clientes': (Cliente, 'scrap/clientes_scrap.html', 'nombre'),
        'tipos_acero': (TipoAcero, 'scrap/tipos_acero.html', 'especificacion'),
        'estatus': (EstatusScrap, 'scrap/estatus.html', 'descripcion_status')
    }

    if section in mapping:
        model, template, field = mapping[section]
        return render_template(template, 
                               items=model.query.order_by(field).all(), 
                               edit_item=model.query.get(edit_id) if edit_id else None)

    return redirect(url_for('main.scrap_section', section='nuevo'))

  

# =========================================================================
# RUTAS POST: PROCESAMIENTO CRUD CENTRALIZADO Y SEGURO
# =========================================================================

@main_bp.route('/scrap/action/<section>/<action_type>', methods=['POST'])
@main_bp.route('/scrap/action/<section>/<action_type>/<int:item_id>', methods=['POST'])
@login_required
def scrap_actions(section, action_type, item_id=None):
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    # Mapeo estructurado: (ClaseModelo, NombreColumnaString, NombreColumnaLlavePrimaria)
    model_mapping = {
        'maquinas': (Maquina, 'nombre', 'id_maquina'),
        'operadores': (Operador, 'nombre', 'id_operador'),
        'defectos': (DefectoScrap, 'defecto', 'id_defecto_scrap'),
        'clasificaciones': (ClasificacionScrap, 'clasificacion', 'id_clasificacion'),
        'supervisores': (Supervisor, 'nombre', 'id_supervisor'),
        'tipos_acero': (TipoAcero, 'especificacion', 'id_tipo_acero'),
        'estatus': (EstatusScrap, 'descripcion_status', 'id_estatus_scrap'),
        'clientes': (Cliente, 'nombre', 'id_cliente'),  # Integración del catálogo compartido
    }

    if section in model_mapping:
        model, field_name, pk_name = model_mapping[section]
        
        # OPERACIÓN: CREAR O EDITAR
        if action_type in ['crear', 'editar']:
            value = request.form.get(field_name, '').strip()
            if not value:
                flash('El campo requerido no puede estar vacío.')
                return redirect(url_for('main.scrap_section', section=section))

            if action_type == 'crear':
                # Validar duplicados exactos antes de insertar
                if model.query.filter(getattr(model, field_name) == value).first():
                    flash('Este registro ya existe en el sistema.')
                else:
                    new_obj = model(**{field_name: value})
                    # Caso único: Maquinas maneja descripción opcional
                    if section == 'maquinas':
                        new_obj.descripcion = request.form.get('descripcion', '').strip() or None
                    db.session.add(new_obj)
                    db.session.commit()
                    flash('Registro creado con éxito.')
            
            elif action_type == 'editar' and item_id:
                obj = model.query.get_or_404(item_id)
                
                # Validación inteligente de duplicados usando la PK correspondiente
                pk_column = getattr(model, pk_name)
                existing = model.query.filter(getattr(model, field_name) == value, pk_column != item_id).first()
                
                if existing:
                    flash('Ya existe otro registro con ese mismo nombre.')
                else:
                    setattr(obj, field_name, value)
                    if section == 'maquinas':
                        obj.descripcion = request.form.get('descripcion', '').strip() or None
                    db.session.commit()
                    flash('Registro actualizado con éxito.')

        # OPERACIÓN: ELIMINAR
        elif action_type == 'eliminar' and item_id:
            obj = model.query.get_or_404(item_id)
            db.session.delete(obj)
            db.session.commit()
            flash('Registro eliminado correctamente.')

    # CASO COMPLEJO: CRUD DE TURNOS (Procesa strings HTML a objetos TIME de Python)
    elif section == 'turnos':
        if action_type == 'crear':
            try:
                nuevo_turno = Turno(
                    nombre_turno=request.form.get('nombre_turno').strip(),
                    hora_inicio=datetime.strptime(request.form.get('hora_inicio'), '%H:%M').time(),
                    hora_fin=datetime.strptime(request.form.get('hora_fin'), '%H:%M').time()
                )
                db.session.add(nuevo_turno)
                db.session.commit()
                flash('Turno guardado con éxito.')
            except ValueError:
                flash('Error en el formato de hora suministrado.')
                
        elif action_type == 'editar' and item_id:
            try:
                obj = Turno.query.get_or_404(item_id)
                obj.nombre_turno = request.form.get('nombre_turno').strip()
                obj.hora_inicio = datetime.strptime(request.form.get('hora_inicio'), '%H:%M').time()
                obj.hora_fin = datetime.strptime(request.form.get('hora_fin'), '%H:%M').time()
                
                db.session.commit()
                flash('Turno actualizado con éxito.')
            except ValueError:
                flash('Error en el formato de hora suministrado al editar.')

        elif action_type == 'eliminar' and item_id:
            obj = Turno.query.get_or_404(item_id)
            db.session.delete(obj)
            db.session.commit()
            flash('Turno eliminado correctamente.')

    return redirect(url_for('main.scrap_section', section=section))

@main_bp.route('/historial_usuario/<int:user_id>')
@login_required
def historial_usuario(user_id):
    # Aquí buscas los registros hechos por ese usuario y renderizas el historial
    registros = Scrap.query.filter_by(usuario_registro_id=user_id).all()
    return render_template('historial.html', registros=registros)

@main_bp.route('/scrap/action/nuevo/editar/<int:item_id>', methods=['POST'])
@login_required
def scrap_editar(item_id):
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Scrap.query.get_or_404(item_id)

    try:
        registro.id_maquina        = request.form.get('id_maquina')
        registro.id_operador       = request.form.get('id_operador')
        registro.id_supervisor     = request.form.get('id_supervisor')
        registro.id_defecto_scrap  = request.form.get('id_defecto_scrap')
        registro.id_clasificacion  = request.form.get('id_clasificacion')
        registro.id_cliente        = request.form.get('id_cliente')
        registro.id_estatus_scrap  = request.form.get('id_estatus_scrap')
        registro.id_tipo_acero     = request.form.get('id_tipo_acero')
        registro.lote              = request.form.get('lote', '').strip()
        registro.peso              = float(request.form.get('peso', 0))
        registro.cantidad_retrabajado = int(request.form.get('cantidad_retrabajado', 0))
        registro.cantidad_ng       = int(request.form.get('cantidad_ng', 0))

        db.session.commit()
        flash('Registro actualizado correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {e}')

    return redirect(url_for('main.scrap_section', section='nuevo'))


@main_bp.route('/scrap/action/nuevo/eliminar/<int:item_id>', methods=['POST'])
@login_required
def scrap_eliminar(item_id):
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización.")
        return redirect(url_for('main.home'))

    registro = Scrap.query.get_or_404(item_id)

    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Registro eliminado correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {e}')

    return redirect(url_for('main.scrap_section', section='nuevo'))



@main_bp.route('/scrap/get-turno', methods=['GET'])
@login_required
def get_turno():
    hora_str = request.args.get('hora')
    if not hora_str:
        return jsonify({'error': 'Hora no proporcionada'}), 400
    
    try:
        # Convertimos la hora recibida a objeto time
        hora_obj = datetime.strptime(hora_str, '%H:%M').time()
        
        # Buscamos en la BD el turno que cubra esa hora
        turno = Turno.query.filter(
            Turno.hora_inicio <= hora_obj, 
            Turno.hora_fin > hora_obj
        ).first()
        
        if turno:
            return jsonify({'id_turno': turno.id_turno, 'nombre': turno.nombre_turno})
        else:
            return jsonify({'id_turno': None, 'nombre': 'Sin turno asignado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500