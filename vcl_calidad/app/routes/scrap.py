from flask import render_template, request, redirect, url_for, session, flash,make_response
from datetime import datetime, date
from app import db

# Importaciones de los modelos del módulo de Scrap y generales
from app.models.scrap_models import (
    Scrap, Maquina, Operador, Turno, DefectoScrap, 
    ClasificacionScrap, Supervisor, TipoAcero, EstatusScrap,TipoLaminacion
)
from app.models.cliente import Cliente  # Modelo de Cliente corregido en singular
from app.routes.main import main_bp

from flask_login import login_required, login_user, current_user

from flask import jsonify


from io import BytesIO

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,Image, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


import matplotlib
matplotlib.use('Agg')          # backend sin pantalla — OBLIGATORIO en servidor
import matplotlib.pyplot as plt







def detectar_turno(hora_obj):
    """Detecta turno correctamente, incluso si cruza la medianoche."""
    for turno in Turno.query.all():
        if turno.hora_inicio <= turno.hora_fin:
            # Turno normal: 07:00 → 18:59
            if turno.hora_inicio <= hora_obj < turno.hora_fin:
                return turno
        else:
            # Turno nocturno: 19:00 → 06:59 (cruza medianoche)
            if hora_obj >= turno.hora_inicio or hora_obj < turno.hora_fin:
                return turno
    return None

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
                hora_dt     = datetime.strptime(hora_manual, '%H:%M').time()
                turno_det   = detectar_turno(hora_dt)
                fecha_final = datetime.strptime(f"{fecha_manual} {hora_manual}", '%Y-%m-%d %H:%M') if fecha_manual else datetime.now()
            else:
                hora_actual = datetime.now().time()
                turno_det   = detectar_turno(hora_actual)
                fecha_final = datetime.now()

            # 3. Guardar el nuevo registro
            try:
                nuevo_registro = Scrap(
                    id_maquina=request.form.get('id_maquina'),
                    id_operador=request.form.get('id_operador'),
                   

                    # DESPUÉS:
                    
                    id_turno=turno_det.id_turno if turno_det else None,
                    id_defecto_scrap=request.form.get('id_defecto_scrap'),
                    id_tipo_laminacion=request.form.get('id_tipo_laminacion'),
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
            tipos_acero=TipoAcero.query.all(),
            tipos_laminacion=TipoLaminacion.query.all()
            
            
            
        
            
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
        'tipos_laminacion': (TipoLaminacion, 'scrap/tipos_laminacion.html', 'especificacion'),
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
        'tipos_laminacion': (TipoLaminacion, 'especificacion', 'id_tipo_laminacion')  # Nuevo catálogo
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
        registro.id_tipo_laminacion = request.form.get('id_tipo_laminacion')

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
        hora_obj = datetime.strptime(hora_str, '%H:%M').time()
        turno = detectar_turno(hora_obj)
        if turno:
            return jsonify({'id_turno': turno.id_turno, 'nombre': turno.nombre_turno})
        else:
            return jsonify({'id_turno': None, 'nombre': 'Sin turno asignado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@main_bp.route('/scrap/reportes', methods=['GET'])
@login_required
def scrap_reportes():
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    # =============================================
    # 1. CAPTURA DE FILTROS DESDE ?query_params
    # =============================================
    filtros = {
        'fecha_inicio':      request.args.get('fecha_inicio', ''),
        'fecha_fin':         request.args.get('fecha_fin', ''),
        'id_maquina':        request.args.get('id_maquina', ''),
        'id_operador':       request.args.get('id_operador', ''),
        'id_cliente':        request.args.get('id_cliente', ''),
        'id_estatus_scrap':  request.args.get('id_estatus_scrap', ''),
        'id_defecto_scrap':  request.args.get('id_defecto_scrap', ''),
        'id_turno':          request.args.get('id_turno', ''),
        'id_supervisor':     request.args.get('id_supervisor', ''),
        'id_clasificacion':  request.args.get('id_clasificacion', ''),
        'id_tipo_acero':     request.args.get('id_tipo_acero', ''),
        'id_tipo_laminacion': request.args.get('id_tipo_laminacion', '')
    }

    # =============================================
    # 2. QUERY BASE CON FILTROS APLICADOS
    # =============================================
    query = Scrap.query

    if filtros['fecha_inicio']:
        query = query.filter(Scrap.fecha_registro >= datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d'))
    if filtros['fecha_fin']:
        # Incluir todo el día final
        fecha_fin_dt = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.filter(Scrap.fecha_registro <= fecha_fin_dt)
    if filtros['id_maquina']:
        query = query.filter(Scrap.id_maquina == int(filtros['id_maquina']))
    if filtros['id_operador']:
        query = query.filter(Scrap.id_operador == int(filtros['id_operador']))
    if filtros['id_cliente']:
        query = query.filter(Scrap.id_cliente == int(filtros['id_cliente']))
    if filtros['id_estatus_scrap']:
        query = query.filter(Scrap.id_estatus_scrap == int(filtros['id_estatus_scrap']))
    if filtros['id_defecto_scrap']:
        query = query.filter(Scrap.id_defecto_scrap == int(filtros['id_defecto_scrap']))
    if filtros['id_turno']:
        query = query.filter(Scrap.id_turno == int(filtros['id_turno']))
    if filtros['id_supervisor']:
        query = query.filter(Scrap.id_supervisor == int(filtros['id_supervisor']))
    if filtros['id_clasificacion']:
        query = query.filter(Scrap.id_clasificacion == int(filtros['id_clasificacion']))
    if filtros['id_tipo_acero']:
        query = query.filter(Scrap.id_tipo_acero == int(filtros['id_tipo_acero']))
    if filtros['id_tipo_laminacion']:
        query = query.filter(Scrap.id_tipo_laminacion == int(filtros['id_tipo_laminacion']))
    registros = query.order_by(Scrap.fecha_registro.desc()).all()

    # =============================================
    # 3. KPIs AGREGADOS
    # =============================================
    total_peso      = sum(r.peso or 0 for r in registros)
    total_ng        = sum(r.cantidad_ng or 0 for r in registros)
    total_retrabajo = sum(r.cantidad_retrabajado or 0 for r in registros)

    kpis = {
        'total_registros': len(registros),
        'peso_total':      total_peso,
        'total_ng':        total_ng,
        'total_retrabajo': total_retrabajo,
    }

    
    # =============================================
    # 5. CATÁLOGOS PARA LOS SELECTORES DE FILTRO
    # =============================================
    return render_template(
        'scrap/reportes_scrap.html',
        filtros=filtros,
        registros=registros,
        kpis=kpis,
    
        # Catálogos para los <select>
        maquinas=Maquina.query.order_by(Maquina.nombre).all(),
        operadores=Operador.query.order_by(Operador.nombre).all(),
        clientes=Cliente.query.order_by(Cliente.nombre).all(),
        estatus_list=EstatusScrap.query.all(),
        defectos=DefectoScrap.query.order_by(DefectoScrap.defecto).all(),
        turnos=Turno.query.all(),
        supervisores=Supervisor.query.order_by(Supervisor.nombre).all(),
        clasificaciones=ClasificacionScrap.query.all(),
        tipos_acero=TipoAcero.query.order_by(TipoAcero.especificacion).all(),
        tipos_laminacion=TipoLaminacion.query.order_by(TipoLaminacion.especificacion).all(),
    )
    
    
    
    
    
    
    





# ─── Paleta de colores ────────────────────────────────────────────────────────
PALETTE = ['#16a34a','#d97706','#dc2626','#2563eb','#a855f7',
           '#ec4899','#14b8a6','#f97316','#64748b','#84cc16']

C_HDR   = colors.HexColor('#0f172a')
C_WHITE = colors.white
C_ALT   = colors.HexColor('#f8fafc')
C_GREEN = colors.HexColor('#16a34a')
C_AMBER = colors.HexColor('#d97706')
C_RED   = colors.HexColor('#dc2626')
C_BLUE  = colors.HexColor('#2563eb')
C_TEXT  = colors.HexColor('#0f172a')
C_MUTED = colors.HexColor('#475569')
C_GRID  = colors.HexColor('#e2e8f0')


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE GRÁFICAS (matplotlib → PNG en memoria → Image de reportlab)
# ══════════════════════════════════════════════════════════════════════════════

def _save_fig(fig):
    """Guarda figura en BytesIO y cierra matplotlib."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf


def make_pie(data, title, w_mm=120, h_mm=72):
    """Gráfica de pastel con leyenda lateral.
    data = lista de (label, valor_numérico)
    """
    if not data:
        return None
    labels = [d[0] for d in data]
    values = [float(d[1]) for d in data]
    total  = sum(values) or 1

    fig, ax = plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), dpi=150)
    fig.patch.set_facecolor('white')

    wedges, _, autotexts = ax.pie(
        values, labels=None,
        autopct=lambda p: f'{p:.1f}%' if p > 4 else '',
        colors=PALETTE[:len(data)],
        startangle=90,
        wedgeprops=dict(linewidth=1, edgecolor='white'),
        pctdistance=0.72,
    )
    for at in autotexts:
        at.set_fontsize(5.5)
        at.set_color('white')
        at.set_fontweight('bold')

    legend_labels = [f'{l}  ({v:,.1f} · {v/total*100:.0f}%)' for l, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(0.95, 0.5),
              fontsize=5.2, frameon=False, labelcolor='#374151', handlelength=1)
    ax.set_title(title, fontsize=7.5, fontweight='bold', color='#0f172a', pad=5)
    plt.tight_layout()
    return _save_fig(fig)


def make_bar_h(data, title, color='#16a34a', w_mm=120, h_mm=72, unit='kg'):
    """Barras horizontales con valor al final de cada barra.
    data = lista de (label, valor_numérico)
    """
    if not data:
        return None
    labels = [d[0] for d in data]
    values = [float(d[1]) for d in data]
    max_v  = max(values) if values else 1

    fig, ax = plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), dpi=150)
    fig.patch.set_facecolor('white')

    for i in range(len(labels)):
        ax.axhspan(i - 0.44, i + 0.44, color='#f8fafc' if i % 2 == 0 else 'white', zorder=0)

    bars = ax.barh(range(len(labels)), values, color=color, alpha=0.82,
                   height=0.52, edgecolor='white', linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max_v * 0.015, bar.get_y() + bar.get_height() / 2,
                f'{val:,.1f} {unit}', va='center', ha='left', fontsize=5.5, color='#374151')

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6, color='#374151')
    ax.invert_yaxis()
    ax.set_xlim(0, max_v * 1.35)
    ax.set_title(title, fontsize=7.5, fontweight='bold', color='#0f172a', pad=5)
    ax.spines['top'].set_visible(False);  ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#e2e8f0'); ax.spines['left'].set_color('#e2e8f0')
    ax.tick_params(axis='x', labelsize=5, colors='#94a3b8')
    ax.tick_params(axis='y', length=0)
    ax.xaxis.grid(True, color='#f1f5f9', linewidth=0.4, zorder=1)
    plt.tight_layout()
    return _save_fig(fig)


def make_bar_v(data, title, color='#16a34a', w_mm=120, h_mm=68, unit=''):
    """Barras verticales (útil para pocas categorías).
    data = lista de (label, valor_numérico)
    """
    if not data:
        return None
    labels = [d[0] for d in data]
    values = [float(d[1]) for d in data]
    max_v  = max(values) if values else 1

    fig, ax = plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), dpi=150)
    fig.patch.set_facecolor('white')

    bars = ax.bar(range(len(labels)), values, color=color, alpha=0.82,
                  edgecolor='white', linewidth=0.5, width=0.55)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_v * 0.02,
                f'{val:,.0f}{(" " + unit) if unit else ""}',
                ha='center', va='bottom', fontsize=5.5, color='#374151', fontweight='bold')

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=6, color='#374151',
                       rotation=20 if len(labels) > 4 else 0, ha='right')
    ax.set_ylim(0, max_v * 1.18)
    ax.set_title(title, fontsize=7.5, fontweight='bold', color='#0f172a', pad=5)
    ax.spines['top'].set_visible(False);  ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#e2e8f0'); ax.spines['left'].set_color('#e2e8f0')
    ax.tick_params(axis='y', labelsize=5.5, colors='#94a3b8')
    ax.yaxis.grid(True, color='#f1f5f9', linewidth=0.4, zorder=0)
    plt.tight_layout()
    return _save_fig(fig)


def make_line_dual(data_dia, w_mm=257, h_mm=68):
    """Gráfica de línea doble: peso (eje izq) y NG (eje der) por día.
    data_dia = lista de {'fecha': str, 'peso': float, 'ng': int}
    """
    if not data_dia:
        return None
    fechas = [d['fecha'] for d in data_dia]
    pesos  = [d['peso']  for d in data_dia]
    ngs    = [d['ng']    for d in data_dia]
    xs     = range(len(fechas))

    fig, ax1 = plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), dpi=150)
    fig.patch.set_facecolor('white')
    ax2 = ax1.twinx()

    l1, = ax1.plot(xs, pesos, color='#d97706', linewidth=1.8,
                   marker='o', markersize=3, label='Peso (kg)', zorder=3)
    ax1.fill_between(xs, pesos, alpha=0.08, color='#d97706')

    l2, = ax2.plot(xs, ngs, color='#dc2626', linewidth=1.6,
                   marker='s', markersize=3, label='Piezas NG', linestyle='--', zorder=3)
    ax2.fill_between(xs, ngs, alpha=0.05, color='#dc2626')

    ax1.set_xticks(list(xs))
    ax1.set_xticklabels(fechas, fontsize=5.5, color='#64748b',
                        rotation=30 if len(fechas) > 10 else 0)
    ax1.set_ylabel('Peso (kg)', fontsize=6, color='#d97706')
    ax2.set_ylabel('Piezas NG', fontsize=6, color='#dc2626')

    for ax in [ax1, ax2]:
        ax.tick_params(axis='y', labelsize=5.5, colors='#64748b')
    ax1.spines['top'].set_visible(False);   ax1.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False);   ax2.spines['left'].set_visible(False)
    ax1.spines['bottom'].set_color('#e2e8f0')
    ax1.xaxis.grid(True, color='#f1f5f9', linewidth=0.4)

    fig.legend([l1, l2], ['Peso (kg)', 'Piezas NG'], loc='upper center', ncol=2,
               fontsize=6, frameon=False, bbox_to_anchor=(0.5, 1.0))
    ax1.set_title('Tendencia diaria — Peso vs Piezas NG',
                  fontsize=7.5, fontweight='bold', color='#0f172a', pad=14)
    plt.tight_layout()
    return _save_fig(fig)


def _img(buf, w_mm, h_mm):
    """Convierte un BytesIO PNG en un Image de reportlab. Devuelve None si buf es None."""
    if buf is None:
        return Spacer(w_mm * mm, h_mm * mm)
    return Image(buf, width=w_mm * mm, height=h_mm * mm)


def _section(text, style):
    """Devuelve [Spacer, Paragraph de título de sección, HRFlowable]."""
    return [
        Spacer(1, 4 * mm),
        Paragraph(text.upper(), style),
        HRFlowable(width='100%', thickness=0.4, color=C_GRID, spaceAfter=3),
    ]


def _side_by_side(left_buf, right_buf, w_mm, h_mm, gap_mm=4):
    """Coloca dos imágenes lado a lado en una tabla sin bordes."""
    half = (w_mm - gap_mm) / 2
    row  = [[_img(left_buf, half, h_mm), _img(right_buf, half, h_mm)]]
    tbl  = Table(row, colWidths=[half * mm, half * mm])
    tbl.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ('INNERGRID',    (0,0),(-1,-1), 0.3, C_GRID),
    ]))
    return tbl


def _triple(bufs, w_mm, h_mm, gap_mm=4):
    """Coloca tres imágenes en una fila."""
    third = (w_mm - 2 * gap_mm) / 3
    row   = [[_img(b, third, h_mm) for b in bufs]]
    tbl   = Table(row, colWidths=[third * mm] * 3)
    tbl.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ('INNERGRID',    (0,0),(-1,-1), 0.3, C_GRID),
    ]))
    return tbl


# ══════════════════════════════════════════════════════════════════════════════
# RUTA FLASK
# ══════════════════════════════════════════════════════════════════════════════

@main_bp.route('/scrap/reportes/pdf', methods=['GET'])
@login_required
def scrap_reporte_pdf():
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización para acceder a este módulo.")
        return redirect(url_for('main.home'))

    # ── 1. FILTROS (idénticos a scrap_reportes) ───────────────────────────────
    filtros = {
        'fecha_inicio':       request.args.get('fecha_inicio', ''),
        'fecha_fin':          request.args.get('fecha_fin', ''),
        'id_maquina':         request.args.get('id_maquina', ''),
        'id_operador':        request.args.get('id_operador', ''),
        'id_cliente':         request.args.get('id_cliente', ''),
        'id_estatus_scrap':   request.args.get('id_estatus_scrap', ''),
        'id_defecto_scrap':   request.args.get('id_defecto_scrap', ''),
        'id_turno':           request.args.get('id_turno', ''),
        'id_supervisor':      request.args.get('id_supervisor', ''),
        'id_clasificacion':   request.args.get('id_clasificacion', ''),
        'id_tipo_acero':      request.args.get('id_tipo_acero', ''),
        'id_tipo_laminacion': request.args.get('id_tipo_laminacion', ''),
    }

    query = Scrap.query
    if filtros['fecha_inicio']:
        query = query.filter(Scrap.fecha_registro >= datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d'))
    if filtros['fecha_fin']:
        fecha_fin_dt = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.filter(Scrap.fecha_registro <= fecha_fin_dt)
    if filtros['id_maquina']:
        query = query.filter(Scrap.id_maquina == int(filtros['id_maquina']))
    if filtros['id_operador']:
        query = query.filter(Scrap.id_operador == int(filtros['id_operador']))
    if filtros['id_cliente']:
        query = query.filter(Scrap.id_cliente == int(filtros['id_cliente']))
    if filtros['id_estatus_scrap']:
        query = query.filter(Scrap.id_estatus_scrap == int(filtros['id_estatus_scrap']))
    if filtros['id_defecto_scrap']:
        query = query.filter(Scrap.id_defecto_scrap == int(filtros['id_defecto_scrap']))
    if filtros['id_turno']:
        query = query.filter(Scrap.id_turno == int(filtros['id_turno']))
    if filtros['id_supervisor']:
        query = query.filter(Scrap.id_supervisor == int(filtros['id_supervisor']))
    if filtros['id_clasificacion']:
        query = query.filter(Scrap.id_clasificacion == int(filtros['id_clasificacion']))
    if filtros['id_tipo_acero']:
        query = query.filter(Scrap.id_tipo_acero == int(filtros['id_tipo_acero']))
    if filtros['id_tipo_laminacion']:
        query = query.filter(Scrap.id_tipo_laminacion == int(filtros['id_tipo_laminacion']))

    registros = query.order_by(Scrap.fecha_registro.asc()).all()

    # ── 2. KPIs ───────────────────────────────────────────────────────────────
    total_peso      = sum(float(r.peso or 0) for r in registros)
    total_ng        = sum(int(r.cantidad_ng or 0) for r in registros)
    total_retrabajo = sum(int(r.cantidad_retrabajado or 0) for r in registros)
    total_regs      = len(registros)
    peso_prom       = (total_peso / total_regs) if total_regs else 0

    # ── 3. AGREGACIONES POR CAMPO ─────────────────────────────────────────────
    def _agg(registros, key_fn, val_fn=lambda r: float(r.peso or 0)):
        m = {}
        for r in registros:
            k = key_fn(r)
            if k:
                m[k] = m.get(k, 0) + val_fn(r)
        return sorted(m.items(), key=lambda x: x[1], reverse=True)

    def peso(r):  return float(r.peso or 0)
    def ng(r):    return int(r.cantidad_ng or 0)

    data_defecto       = _agg(registros, lambda r: r.defecto.defecto          if r.defecto        else None)
    data_estatus_ng    = _agg(registros, lambda r: r.estatus.descripcion_status if r.estatus      else None, ng)
    data_maquina       = _agg(registros, lambda r: r.maquina.nombre            if r.maquina       else None)
    data_operador_ng   = _agg(registros, lambda r: r.operador.nombre           if r.operador      else None, ng)
    data_supervisor    = _agg(registros, lambda r: r.supervisor.nombre         if r.supervisor    else None)
    data_turno         = _agg(registros, lambda r: r.turno.nombre_turno        if r.turno         else None)
    data_cliente       = _agg(registros, lambda r: r.cliente.nombre            if r.cliente       else None)
    data_clasificacion = _agg(registros, lambda r: r.clasificacion.clasificacion if r.clasificacion else None)
    data_acero         = _agg(registros, lambda r: r.tipo_acero.especificacion  if r.tipo_acero   else None)
    data_laminacion    = _agg(registros, lambda r: r.tipo_laminacion.especificacion if r.tipo_laminacion else None)

    # Tendencia por día
    dia_map = {}
    for r in registros:
        if r.fecha_registro:
            k   = r.fecha_registro.strftime('%Y-%m-%d')
            lbl = r.fecha_registro.strftime('%d/%m')
            if k not in dia_map:
                dia_map[k] = {'fecha': lbl, 'peso': 0.0, 'ng': 0}
            dia_map[k]['peso'] = round(dia_map[k]['peso'] + float(r.peso or 0), 2)
            dia_map[k]['ng']  += int(r.cantidad_ng or 0)
    data_dia = [v for _, v in sorted(dia_map.items())]

    # ── 4. ESTILOS REPORTLAB ──────────────────────────────────────────────────
    fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
    sty = getSampleStyleSheet()
    s_title = ParagraphStyle('T2', parent=sty['Title'], fontSize=20, textColor=C_TEXT, spaceAfter=1, leading=24)
    s_sub   = ParagraphStyle('Sub', parent=sty['Normal'], fontSize=7.5, textColor=C_MUTED, spaceAfter=6)
    s_sec   = ParagraphStyle('Sec', parent=sty['Normal'], fontSize=8, textColor=C_MUTED,
                              fontName='Helvetica-Bold', spaceBefore=0, spaceAfter=2)
    s_cell  = ParagraphStyle('Cell', parent=sty['Normal'], fontSize=6.5, textColor=C_TEXT, leading=8.5)
    s_cmono = ParagraphStyle('CMono', parent=sty['Normal'], fontSize=6.5, fontName='Courier',
                              textColor=C_TEXT, leading=8.5)
    s_note  = ParagraphStyle('Note', parent=sty['Normal'], fontSize=6, textColor=C_MUTED, spaceAfter=4)

    # ── 5. DIMENSIONES ────────────────────────────────────────────────────────
    PAGE = landscape(A4)
    M    = 12 * mm
    W    = PAGE[0] - 2 * M       # ancho útil en puntos
    W_MM = W / mm                 # ídem en mm
    H    = 72                     # altura estándar de charts en mm

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE,
                            leftMargin=M, rightMargin=M,
                            topMargin=M, bottomMargin=14 * mm)

    story = []

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 1: ENCABEZADO + KPIs
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Reporte de Scrap", s_title))

    filtros_txt = []
    if filtros['fecha_inicio']: filtros_txt.append(f"Desde: {filtros['fecha_inicio']}")
    if filtros['fecha_fin']:    filtros_txt.append(f"Hasta: {filtros['fecha_fin']}")
    sub_text = f"Generado: {fecha_gen}"
    if filtros_txt:
        sub_text += "   ·   Filtros activos: " + "  /  ".join(filtros_txt)
    story.append(Paragraph(sub_text, s_sub))
    story.append(HRFlowable(width='100%', thickness=1.5, color=C_GREEN, spaceAfter=6))

    # KPIs
    kpi_data = [
        ['REGISTROS', 'PESO TOTAL (kg)', 'PESO NG', 'RETRABAJO', 'PESO PROM / REG'],
        [str(total_regs), f'{total_peso:,.1f}', str(total_ng), str(total_retrabajo),
         f'{peso_prom:,.1f}' if total_regs else '—'],
    ]
    kpi_w = [W / 5] * 5
    kpi_t = Table(kpi_data, colWidths=kpi_w)
    kpi_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR',     (0,0),(-1,0), C_MUTED),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 6.5),
        ('ALIGN',         (0,0),(-1,0), 'CENTER'),
        ('TOPPADDING',    (0,0),(-1,0), 5), ('BOTTOMPADDING',(0,0),(-1,0), 4),
        ('FONTNAME',      (0,1),(-1,1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,1),(-1,1), 18),
        ('ALIGN',         (0,1),(-1,1), 'CENTER'),
        ('TOPPADDING',    (0,1),(-1,1), 8), ('BOTTOMPADDING',(0,1),(-1,1), 8),
        ('TEXTCOLOR',     (0,1),(0,1), C_TEXT),
        ('TEXTCOLOR',     (1,1),(1,1), C_AMBER),
        ('TEXTCOLOR',     (2,1),(2,1), C_RED),
        ('TEXTCOLOR',     (3,1),(3,1), C_BLUE),
        ('TEXTCOLOR',     (4,1),(4,1), C_MUTED),
        ('BOX',           (0,0),(-1,-1), 0.5, C_GRID),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, C_GRID),
        ('ROWBACKGROUNDS',(0,1),(-1,1), [colors.white]),
    ]))
    story.append(kpi_t)

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 2: TENDENCIA DIARIA + DEFECTOS
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section('Tendencia Diaria', s_sec)
    story.append(_img(make_line_dual(data_dia, w_mm=W_MM, h_mm=H - 4), W_MM, H - 4))

    story += _section('Análisis por Defecto', s_sec)
    story.append(_side_by_side(
        make_pie(data_defecto[:8],  'Peso por Defecto (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_h(data_defecto[:8],'Peso por Defecto (barras)', color='#16a34a', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 3: ESTATUS + MÁQUINAS
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section('Análisis por Estatus (Peso NG)', s_sec)
    story.append(_side_by_side(
        make_pie(data_estatus_ng,   'NG por Estatus (pastel)',   w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_v(data_estatus_ng, 'NG por Estatus (barras)',   color='#dc2626', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    story += _section('Análisis por Máquina', s_sec)
    story.append(_side_by_side(
        make_pie(data_maquina[:8],   'Peso por Máquina (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_h(data_maquina[:8], 'Peso por Máquina (barras)', color='#d97706', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 4: OPERADORES + SUPERVISORES
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section('Análisis por Operador (Peso NG)', s_sec)
    story.append(_side_by_side(
        make_pie(data_operador_ng[:8],   'NG por Operador (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_h(data_operador_ng[:8], 'NG por Operador (barras)', color='#dc2626', w_mm=(W_MM-4)/2, h_mm=H, unit='NG'),
        W_MM, H,
    ))

    story += _section('Análisis por Supervisor', s_sec)
    story.append(_side_by_side(
        make_pie(data_supervisor[:8],   'Peso por Supervisor (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_h(data_supervisor[:8], 'Peso por Supervisor (barras)', color='#2563eb', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 5: TURNO + CLIENTE
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section('Análisis por Turno', s_sec)
    story.append(_side_by_side(
        make_pie(data_turno,   'Peso por Turno (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_v(data_turno, 'Peso por Turno (barras)', color='#a855f7', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    story += _section('Análisis por Cliente', s_sec)
    story.append(_side_by_side(
        make_pie(data_cliente[:8],   'Peso por Cliente (pastel)', w_mm=(W_MM-4)/2, h_mm=H),
        make_bar_h(data_cliente[:8], 'Peso por Cliente (barras)', color='#14b8a6', w_mm=(W_MM-4)/2, h_mm=H),
        W_MM, H,
    ))

    # ════════════════════════════════════════════════════════════════════════
    # PÁGINA 6: CLASIFICACIÓN / TIPO ACERO / LAMINACIÓN
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section('Análisis por Clasificación · Tipo Acero · Tipo Laminación', s_sec)

    W3 = (W_MM - 4) / 3
    H3 = H - 2

    story.append(_triple(
        [make_pie(data_clasificacion, 'Por Clasificación (pastel)',    w_mm=W3, h_mm=H3),
         make_pie(data_acero[:6],     'Por Tipo Acero (pastel)',       w_mm=W3, h_mm=H3),
         make_pie(data_laminacion,    'Por Tipo Laminación (pastel)',  w_mm=W3, h_mm=H3)],
        W_MM, H3,
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(_triple(
        [make_bar_v(data_clasificacion, 'Por Clasificación (barras)',   color='#84cc16', w_mm=W3, h_mm=H3),
         make_bar_h(data_acero[:6],     'Por Tipo Acero (barras)',      color='#64748b', w_mm=W3, h_mm=H3),
         make_bar_v(data_laminacion,    'Por Tipo Laminación (barras)', color='#f97316', w_mm=W3, h_mm=H3)],
        W_MM, H3,
    ))

    # ════════════════════════════════════════════════════════════════════════
    # ÚLTIMA PÁGINA: TABLA DE DETALLE
    # ════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section(f'Detalle de registros ({total_regs})', s_sec)

    col_h = ['Fecha','Lote','Máquina','Operador','Supervisor','Cliente',
              'Defecto','Clasificación','Estatus','Turno','Peso (kg)','Retrabajo','NG']
    col_w = [24, 15, 20, 22, 22, 20, 22, 20, 20, 16, 16, 14, 10]

    tbl_data = [col_h]
    for reg in registros:
        fecha_str = reg.fecha_registro.strftime('%d/%m/%y %H:%M') if reg.fecha_registro else '—'
        tbl_data.append([
            Paragraph(fecha_str,                                                            s_cmono),
            Paragraph(str(reg.lote or '—'),                                                s_cmono),
            Paragraph(reg.maquina.nombre              if reg.maquina         else '—',     s_cell),
            Paragraph(reg.operador.nombre             if reg.operador        else '—',     s_cell),
            Paragraph(reg.supervisor.nombre           if reg.supervisor      else '—',     s_cell),
            Paragraph(reg.cliente.nombre              if reg.cliente         else '—',     s_cell),
            Paragraph(reg.defecto.defecto             if reg.defecto         else '—',     s_cell),
            Paragraph(reg.clasificacion.clasificacion if reg.clasificacion   else '—',     s_cell),
            Paragraph(reg.estatus.descripcion_status  if reg.estatus         else '—',     s_cell),
            Paragraph(reg.turno.nombre_turno          if reg.turno           else '—',     s_cell),
            Paragraph(f'{reg.peso or 0:,.2f}',                                             s_cmono),
            Paragraph(str(reg.cantidad_retrabajado or 0),                                  s_cmono),
            Paragraph(str(reg.cantidad_ng or 0),                                           s_cmono),
        ])

    det = Table(tbl_data, colWidths=[w * mm for w in col_w], repeatRows=1)
    ts  = TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_HDR),
        ('TEXTCOLOR',     (0,0),(-1,0),  C_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0),  6.5),
        ('ALIGN',         (0,0),(-1,0),  'CENTER'),
        ('VALIGN',        (0,0),(-1,0),  'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,0),  4), ('BOTTOMPADDING',(0,0),(-1,0), 4),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 6.5),
        ('VALIGN',        (0,1),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,1),(-1,-1), 3), ('BOTTOMPADDING',(0,1),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 3), ('RIGHTPADDING',(0,0),(-1,-1), 3),
        ('ALIGN',         (10,1),(12,-1),'RIGHT'),
        ('BOX',           (0,0),(-1,-1), 0.5, C_GRID),
        ('INNERGRID',     (0,0),(-1,-1), 0.2, C_GRID),
    ])
    for i in range(1, len(tbl_data)):
        if i % 2 == 0:
            ts.add('BACKGROUND', (0,i), (-1,i), C_ALT)
    det.setStyle(ts)
    story.append(det)

    if total_regs == 0:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph('Sin registros con los filtros aplicados.', s_note))

    # ── Pie de página ─────────────────────────────────────────────────────────
    def on_page(canvas_obj, doc):
        canvas_obj.saveState()
        pw = doc.pagesize[0]
        canvas_obj.setStrokeColor(C_GRID)
        canvas_obj.setLineWidth(0.4)
        canvas_obj.line(M, 11 * mm, pw - M, 11 * mm)
        canvas_obj.setFont('Helvetica', 6.5)
        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.drawString(M, 8 * mm, "Reporte de Scrap  —  Confidencial")
        canvas_obj.drawRightString(pw - M, 8 * mm,
                                   f"Página {doc.page}  ·  Generado: {fecha_gen}")
        canvas_obj.restoreState()

    # ── 6. BUILD + RESPONSE ───────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        f'attachment; filename="reporte_scrap_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    )
    return response