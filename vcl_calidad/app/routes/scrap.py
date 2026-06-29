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
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle






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
    
    
    


SCHEMES = {
    'green':  ('#bbf7d0','#16a34a','#14532d'),
    'amber':  ('#fef9c3','#d97706','#78350f'),
    'red':    ('#fee2e2','#dc2626','#7f1d1d'),
    'blue':   ('#dbeafe','#2563eb','#1e3a8a'),
    'purple': ('#f3e8ff','#a855f7','#581c87'),
    'teal':   ('#ccfbf1','#14b8a6','#134e4a'),
    'orange': ('#ffedd5','#f97316','#7c2d12'),
    'slate':  ('#f1f5f9','#64748b','#0f172a'),
    'lime':   ('#d9f99d','#84cc16','#365314'),
}

def _save(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig); buf.seek(0)
    return buf

def bar(data, title, scheme='green', w_mm=120, h_mm=70, unit='kg', n=8):
    data = [(str(l), float(v)) for l,v in data if float(v)>0][:n]
    if not data: return None
    labels, values = zip(*data)
    total = sum(values) or 1; max_v = max(values)
    light, mid, dark = SCHEMES[scheme]
    fig, ax = plt.subplots(figsize=(w_mm/25.4, max(h_mm/25.4, len(labels)*.6+1)), dpi=150)
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    for i in range(len(labels)):
        ax.axhspan(i-.48, i+.48, color='#f8fafc' if i%2==0 else 'white', zorder=0)
    ax.barh(range(len(labels)), [max_v]*len(labels), height=.52, color=light, alpha=.4, zorder=1)
    bars_ = ax.barh(range(len(labels)), values, height=.52, color=mid, alpha=.88, zorder=2)
    bars_[0].set_facecolor(dark); bars_[0].set_alpha(1)
    for i,b in enumerate(bars_):
        ax.plot([0,0],[b.get_y(),b.get_y()+b.get_height()],
                color=dark if i==0 else mid, linewidth=2.5, solid_capstyle='round', zorder=3)
    for i,(b,val) in enumerate(zip(bars_,values)):
        ax.text(b.get_width()+max_v*.015, b.get_y()+b.get_height()/2,
                f'{val:,.1f} {unit}  ({val/total*100:.0f}%)',
                va='center', ha='left', fontsize=6,
                color=dark if i==0 else '#374151',
                fontweight='bold' if i==0 else 'normal')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([f'#{i+1} {l}' for i,l in enumerate(labels)], fontsize=6.2, color='#0f172a')
    ax.invert_yaxis(); ax.set_xlim(0, max_v*1.55)
    ax.xaxis.set_visible(False)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False); ax.spines['left'].set_color('#e2e8f0')
    ax.tick_params(axis='y', length=0, pad=3)
    for p in [.25,.5,.75,1]: ax.axvline(max_v*p, color='#e2e8f0', lw=.5, zorder=0)
    ax.set_title(title, fontsize=7.5, fontweight='bold', color='#0f172a', loc='left', pad=6)
    plt.tight_layout(pad=.5)
    return _save(fig)

def line(data_dia, w_mm=257, h_mm=58):
    if not data_dia: return None
    fechas=[d['fecha'] for d in data_dia]; pesos=[d['peso'] for d in data_dia]; ngs=[d['ng'] for d in data_dia]
    xs=np.arange(len(fechas))
    fig,ax1=plt.subplots(figsize=(w_mm/25.4,h_mm/25.4),dpi=150)
    fig.patch.set_facecolor('white'); ax1.set_facecolor('white'); ax2=ax1.twinx()
    ax1.fill_between(xs,pesos,alpha=.1,color='#d97706')
    ax2.fill_between(xs,ngs,alpha=.07,color='#dc2626')
    l1,=ax1.plot(xs,pesos,color='#d97706',lw=2,marker='o',ms=3.5,markerfacecolor='white',markeredgewidth=1.5,markeredgecolor='#d97706',label='Peso (kg)',zorder=4)
    l2,=ax2.plot(xs,ngs,color='#dc2626',lw=2,marker='s',ms=3.5,markerfacecolor='white',markeredgewidth=1.5,markeredgecolor='#dc2626',label='Piezas NG',zorder=4)
    ax1.set_xticks(xs); ax1.set_xticklabels(fechas,fontsize=5.8,color='#64748b',rotation=30 if len(fechas)>10 else 0,ha='right')
    ax1.set_ylabel('Peso (kg)',fontsize=6,color='#d97706'); ax2.set_ylabel('Piezas NG',fontsize=6,color='#dc2626')
    ax1.tick_params(axis='y',labelsize=5.5,colors='#94a3b8'); ax2.tick_params(axis='y',labelsize=5.5,colors='#94a3b8')
    ax1.yaxis.grid(True,color='#e2e8f0',lw=.4,zorder=0); ax1.set_axisbelow(True)
    for ax in [ax1,ax2]: ax.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False); ax2.spines['left'].set_visible(False)
    ax1.spines['left'].set_color('#e2e8f0'); ax1.spines['bottom'].set_color('#e2e8f0')
    fig.legend([l1,l2],['Peso (kg)','Piezas NG'],loc='upper right',fontsize=6,frameon=True,fancybox=False,edgecolor='#e2e8f0',bbox_to_anchor=(.99,.97))
    ax1.set_title('Tendencia diaria',fontsize=7.5,fontweight='bold',color='#0f172a',loc='left',pad=6)
    plt.tight_layout(pad=.5)
    return _save(fig)

def _img(buf,w,h): return Image(buf,width=w*mm,height=h*mm) if buf else Spacer(w*mm,h*mm)

def _grid(items):
    # items = [(buf, w_mm, h_mm), ...]
    t = Table([[_img(b,w,h) for b,w,h in items]], colWidths=[w*mm for _,w,_ in items])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    return t

def _sec(txt,s): return [Spacer(1,3*mm),Paragraph(txt.upper(),s),HRFlowable(width='100%',thickness=.4,color=colors.HexColor('#e2e8f0'),spaceAfter=2)]


@main_bp.route('/scrap/reportes/pdf', methods=['GET'])
@login_required
def scrap_reporte_pdf():
    if not current_user.puede_ver_scrap:
        flash("No tienes autorización."); return redirect(url_for('main.home'))

    # ── Filtros ───────────────────────────────────────────────────────────────
    filtros = {k: request.args.get(k,'') for k in [
        'fecha_inicio','fecha_fin','id_maquina','id_operador','id_cliente',
        'id_estatus_scrap','id_defecto_scrap','id_turno','id_supervisor',
        'id_clasificacion','id_tipo_acero','id_tipo_laminacion']}

    q = Scrap.query
    if filtros['fecha_inicio']: q=q.filter(Scrap.fecha_registro>=datetime.strptime(filtros['fecha_inicio'],'%Y-%m-%d'))
    if filtros['fecha_fin']:    q=q.filter(Scrap.fecha_registro<=datetime.strptime(filtros['fecha_fin'],'%Y-%m-%d').replace(hour=23,minute=59,second=59))
    for field in ['id_maquina','id_operador','id_cliente','id_estatus_scrap','id_defecto_scrap','id_turno','id_supervisor','id_clasificacion','id_tipo_acero','id_tipo_laminacion']:
        if filtros[field]: q=q.filter(getattr(Scrap,field)==int(filtros[field]))
    registros = q.order_by(Scrap.fecha_registro.asc()).all()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_peso = sum(float(r.peso or 0) for r in registros)
    total_ng   = sum(int(r.cantidad_ng or 0) for r in registros)
    total_ret  = sum(int(r.cantidad_retrabajado or 0) for r in registros)
    n_regs     = len(registros)

    # ── Agregaciones ─────────────────────────────────────────────────────────
    def agg(kfn, vfn=lambda r: float(r.peso or 0)):
        m={}
        for r in registros:
            k=kfn(r)
            if k: m[k]=m.get(k,0.0)+vfn(r)
        return sorted(m.items(),key=lambda x:x[1],reverse=True)

    ng_ = lambda r: int(r.cantidad_ng or 0)
    data_def = agg(lambda r: r.defecto.defecto               if r.defecto        else None)
    data_maq = agg(lambda r: r.maquina.nombre                if r.maquina        else None)
    data_op  = agg(lambda r: r.operador.nombre               if r.operador       else None, ng_)
    data_est = agg(lambda r: r.estatus.descripcion_status    if r.estatus        else None, ng_)
    data_tur = agg(lambda r: r.turno.nombre_turno            if r.turno          else None)
    data_cli = agg(lambda r: r.cliente.nombre                if r.cliente        else None)
    data_sup = agg(lambda r: r.supervisor.nombre             if r.supervisor     else None)
    data_ace = agg(lambda r: r.tipo_acero.especificacion     if r.tipo_acero     else None)
    data_lam = agg(lambda r: r.tipo_laminacion.especificacion if r.tipo_laminacion else None)
    data_cla = agg(lambda r: r.clasificacion.clasificacion   if r.clasificacion  else None)

    dia_map={}
    for r in registros:
        if r.fecha_registro:
            k=r.fecha_registro.strftime('%Y-%m-%d'); lbl=r.fecha_registro.strftime('%d/%m')
            if k not in dia_map: dia_map[k]={'fecha':lbl,'peso':0.0,'ng':0}
            dia_map[k]['peso']=round(dia_map[k]['peso']+float(r.peso or 0),2)
            dia_map[k]['ng']+=int(r.cantidad_ng or 0)
    data_dia=[v for _,v in sorted(dia_map.items())]

    # ── Estilos ───────────────────────────────────────────────────────────────
    fecha_gen=datetime.now().strftime('%d/%m/%Y %H:%M')
    sty=getSampleStyleSheet()
    s_t=ParagraphStyle('t',parent=sty['Title'],fontSize=18,textColor=colors.HexColor('#0f172a'),spaceAfter=1,leading=22)
    s_s=ParagraphStyle('s',parent=sty['Normal'],fontSize=7,textColor=colors.HexColor('#64748b'),spaceAfter=5)
    s_h=ParagraphStyle('h',parent=sty['Normal'],fontSize=7,textColor=colors.HexColor('#64748b'),fontName='Helvetica-Bold',spaceAfter=2)

    PAGE=landscape(A4); M=12*mm; W=PAGE[0]-2*M; WM=W/mm; H=75
    buf_pdf=BytesIO()
    doc=SimpleDocTemplate(buf_pdf,pagesize=PAGE,leftMargin=M,rightMargin=M,topMargin=M,bottomMargin=13*mm)
    story=[]

    # ══ PÁGINA 1: KPIs + Tendencia + Defectos/Máquinas ══════════════════════
    story.append(Paragraph("Reporte de Scrap",s_t))
    story.append(Paragraph(f"Generado: {fecha_gen}",s_s))
    story.append(HRFlowable(width='100%',thickness=1.2,color=colors.HexColor('#16a34a'),spaceAfter=6))

    kd=[['REGISTROS','PESO (kg)','PIEZAS NG','RETRABAJO','PROM / REG'],
        [str(n_regs),f'{total_peso:,.1f}',str(total_ng),str(total_ret),
         f'{total_peso/n_regs:,.1f}' if n_regs else '—']]
    kt=Table(kd,colWidths=[WM/5*mm]*5)
    kt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#64748b')),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),6.5),
        ('ALIGN',(0,0),(-1,0),'CENTER'),('TOPPADDING',(0,0),(-1,0),4),('BOTTOMPADDING',(0,0),(-1,0),4),
        ('FONTNAME',(0,1),(-1,1),'Helvetica-Bold'),('FONTSIZE',(0,1),(-1,1),17),
        ('ALIGN',(0,1),(-1,1),'CENTER'),('TOPPADDING',(0,1),(-1,1),7),('BOTTOMPADDING',(0,1),(-1,1),7),
        ('TEXTCOLOR',(1,1),(1,1),colors.HexColor('#d97706')),
        ('TEXTCOLOR',(2,1),(2,1),colors.HexColor('#dc2626')),
        ('TEXTCOLOR',(3,1),(3,1),colors.HexColor('#2563eb')),
        ('TEXTCOLOR',(4,1),(4,1),colors.HexColor('#64748b')),
        ('BOX',(0,0),(-1,-1),.5,colors.HexColor('#e2e8f0')),
        ('INNERGRID',(0,0),(-1,-1),.3,colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,1),(-1,1),[colors.white]),
    ]))
    story.append(kt); story.append(Spacer(1,4*mm))

    story+=_sec('Tendencia diaria',s_h)
    story.append(_img(line(data_dia,w_mm=WM,h_mm=56),WM,56))
    story.append(Spacer(1,4*mm))

    story+=_sec('Defectos · Máquinas',s_h)
    w2=(WM-4)/2; h2=H-8
    story.append(_grid([(bar(data_def,'Top Defectos — Peso (kg)',scheme='green',w_mm=w2,h_mm=h2),w2,h2),
                         (bar(data_maq,'Top Máquinas — Peso (kg)',scheme='amber',w_mm=w2,h_mm=h2),w2,h2)]))

    # ══ PÁGINA 2: Operadores/Estatus + Turno/Cliente/Supervisor + Acero/Lam/Clas ══
    story.append(PageBreak())
    story+=_sec('Operadores · Estatus',s_h)
    story.append(_grid([(bar(data_op,'Top Operadores — Peso NG',scheme='red',w_mm=w2,h_mm=h2,unit='pzs'),w2,h2),
                         (bar(data_est,'NG por Estatus',scheme='purple',w_mm=w2,h_mm=h2,unit='pzs',n=6),w2,h2)]))
    story.append(Spacer(1,4*mm))

    story+=_sec('Turnos · Clientes · Supervisores',s_h)
    w3=(WM-8)/3; h3=H-10
    story.append(_grid([(bar(data_tur,'Por Turno',scheme='teal',w_mm=w3,h_mm=h3,unit='kg',n=4),w3,h3),
                         (bar(data_cli,'Por Cliente',scheme='blue',w_mm=w3,h_mm=h3,unit='kg'),w3,h3),
                         (bar(data_sup,'Por Supervisor',scheme='slate',w_mm=w3,h_mm=h3,unit='kg'),w3,h3)]))
    story.append(Spacer(1,4*mm))

    story+=_sec('Tipo Acero · Laminación · Clasificación',s_h)
    story.append(_grid([(bar(data_ace,'Por Tipo Acero',scheme='orange',w_mm=w3,h_mm=h3,unit='kg'),w3,h3),
                         (bar(data_lam,'Por Laminación',scheme='lime',w_mm=w3,h_mm=h3,unit='kg',n=4),w3,h3),
                         (bar(data_cla,'Por Clasificación',scheme='red',w_mm=w3,h_mm=h3,unit='kg',n=4),w3,h3)]))

    def footer(cv,doc):
        cv.saveState(); pw=doc.pagesize[0]
        cv.setStrokeColor(colors.HexColor('#e2e8f0')); cv.setLineWidth(.4)
        cv.line(M,11*mm,pw-M,11*mm)
        cv.setFont('Helvetica',6.5); cv.setFillColor(colors.HexColor('#64748b'))
        cv.drawString(M,8*mm,"Reporte de Scrap")
        cv.drawRightString(pw-M,8*mm,f"Pág. {doc.page}  ·  {fecha_gen}")
        cv.restoreState()

    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    buf_pdf.seek(0)
    resp=make_response(buf_pdf.read())
    resp.headers['Content-Type']='application/pdf'
    resp.headers['Content-Disposition']=f'attachment; filename="reporte_scrap_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    return resp
    
    
    



