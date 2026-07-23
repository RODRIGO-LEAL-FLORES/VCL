"""
Lógica de pipeline de reclamaciones.

Reglas del negocio:
    - Confirmación:      límite 48 horas (2 días naturales) desde fecha_reporte
    - Contención (D0-D3): límite 3 días hábiles desde fecha_reporte
    - CR y AC (D4-D7):    límite 10 días hábiles desde fecha_reporte
    - Cierre (D8):        límite 20 días hábiles desde fecha_reporte

El ESTATUS de una reclamación se determina automáticamente según qué
fechas ya están capturadas (no se elige manualmente):

    - Si falta fecha_confirmacion  -> estatus = "Confirmación"
    - Si falta fecha_contencion    -> estatus = "Contención (D0-D3)"
    - Si falta fecha_CR_AC         -> estatus = "CR y AC (D4-D7)"
    - Si falta fecha_cierre        -> estatus = "Cierre (D8)"
    - Si todas están capturadas    -> estatus = "Cerrado"

Además, para cada etapa se calcula si va "en tiempo" o "atrasada"
comparando la fecha real (o la fecha de hoy si aún está pendiente)
contra la fecha límite calculada en días hábiles.
"""

from datetime import date, timedelta

from app import db
from app.models.reclamaciones_models import EstatusReclamacion


# =========================================================================
# CÁLCULO DE DÍAS HÁBILES
# =========================================================================
def sumar_dias_habiles(fecha_inicio: date, dias_habiles: int) -> date:
    """
    Suma N días hábiles (lunes a viernes) a una fecha.
    No considera días festivos; solo excluye sábados y domingos.
    """
    if fecha_inicio is None:
        return None

    fecha = fecha_inicio
    dias_sumados = 0
    while dias_sumados < dias_habiles:
        fecha += timedelta(days=1)
        if fecha.weekday() < 5:  # 0=lunes ... 4=viernes
            dias_sumados += 1
    return fecha


# =========================================================================
# DEFINICIÓN DEL PIPELINE
# =========================================================================
# Cada etapa define: el campo de fecha que la marca como "completada",
# el nombre del estatus asociado (debe existir en EstatusReclamacion),
# y cómo se calcula su fecha límite.
ETAPAS = [
    {
        "orden": 1,
        "nombre": "Confirmación",
        "campo_fecha": "fecha_confirmacion",
        "calcular_limite": lambda reporte: reporte + timedelta(days=2),  # 48 hrs
    },
    {
        "orden": 2,
        "nombre": "Contención (D0-D3)",
        "campo_fecha": "fecha_contencion",
        "calcular_limite": lambda reporte: sumar_dias_habiles(reporte, 3),
    },
    {
        "orden": 3,
        "nombre": "CR y AC (D4-D7)",
        "campo_fecha": "fecha_CR_AC",
        "calcular_limite": lambda reporte: sumar_dias_habiles(reporte, 10),
    },
    {
        "orden": 4,
        "nombre": "Cierre (D8)",
        "campo_fecha": "fecha_cierre",
        "calcular_limite": lambda reporte: sumar_dias_habiles(reporte, 20),
    },
    {
        "orden": 5,
        "nombre": "Cerrado",
        "campo_fecha": None,
        "calcular_limite": lambda reporte: None,
    },
]


# =========================================================================
# CÁLCULO DEL ESTATUS ACTUAL (para asignar id_estatus automáticamente)
# =========================================================================
def calcular_orden_actual(reclamacion) -> int:
    """
    Recorre las etapas en orden y regresa el número de 'orden' de la
    primera etapa que aún no tiene su fecha capturada.
    Si todas las fechas están capturadas, regresa el orden de 'Cerrado'.
    """
    for etapa in ETAPAS:
        campo = etapa["campo_fecha"]
        if campo is None:
            continue
        if getattr(reclamacion, campo) is None:
            return etapa["orden"]
    return ETAPAS[-1]["orden"]  # todas las fechas capturadas -> Cerrado


def obtener_estatus_por_orden(orden: int):
    """Busca en la BD el EstatusReclamacion que corresponde a ese orden."""
    return EstatusReclamacion.query.filter_by(orden=orden).first()


def actualizar_estatus_automatico(reclamacion):
    """
    Calcula y asigna el id_estatus correcto a una reclamación según sus
    fechas capturadas. Debe llamarse antes de db.session.commit(),
    tanto al crear como al editar un registro.
    """
    orden_actual = calcular_orden_actual(reclamacion)
    estatus = obtener_estatus_por_orden(orden_actual)
    if estatus:
        reclamacion.id_estatus = estatus.id_estatus
    return reclamacion


# =========================================================================
# CHECKLIST / TIMELINE PARA MOSTRAR EN LA VISTA
# =========================================================================
def calcular_checklist(reclamacion):
    """
    Regresa una lista de dicts, uno por etapa, listos para pintar en el
    template como un checklist/timeline:

        {
            "nombre": "Contención (D0-D3)",
            "completado": True/False,
            "es_actual": True/False,
            "fecha_limite": date | None,
            "fecha_real": date | None,
            "estado_tiempo": "en_tiempo" | "atrasado" | "pendiente" | "sin_iniciar",
        }
    """
    hoy = date.today()
    reporte = reclamacion.fecha_reporte
    orden_actual = calcular_orden_actual(reclamacion)

    checklist = []
    for etapa in ETAPAS:
        campo = etapa["campo_fecha"]
        fecha_real = getattr(reclamacion, campo) if campo else None
        fecha_limite = etapa["calcular_limite"](reporte) if reporte else None
        completado = campo is None or fecha_real is not None
        es_actual = etapa["orden"] == orden_actual

        if campo is None:
            # Etapa "Cerrado": completada solo si ya se llegó a ella
            estado_tiempo = "en_tiempo" if completado else "sin_iniciar"
        elif fecha_real is not None:
            estado_tiempo = "en_tiempo" if (fecha_limite is None or fecha_real <= fecha_limite) else "atrasado"
        elif fecha_limite is not None and hoy > fecha_limite:
            estado_tiempo = "atrasado"
        elif es_actual:
            estado_tiempo = "pendiente"
        else:
            estado_tiempo = "sin_iniciar"

        checklist.append({
            "nombre": etapa["nombre"],
            "completado": completado,
            "es_actual": es_actual,
            "fecha_limite": fecha_limite,
            "fecha_real": fecha_real,
            "estado_tiempo": estado_tiempo,
        })

    return checklist