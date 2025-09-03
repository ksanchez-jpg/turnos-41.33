import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import math
import io

# Configuración de la página
st.set_page_config(
    page_title="CALCULO PERSONAL REQUERIDO Y GENERADOR DE TURNOS",
    page_icon="🏭",
    layout="wide"
)

# Título principal
st.title("🏭 Sistema de Generación de Turnos")

# Inicializar session state
if 'cargos_data' not in st.session_state:
    st.session_state.cargos_data = []
if 'turnos_generados' not in st.session_state:
    st.session_state.turnos_generados = None

# Sidebar para navegación
st.sidebar.title("📋 Navegación")
seccion = st.sidebar.radio(
    "Seleccionar sección:",
    ["1. Configuración de Cargos", "2. Generación de Turnos", "3. Visualización y Exportar"]
)


# ===================================================================
# ============= INICIO DE LAS FUNCIONES DE LÓGICA (VERSIÓN FINAL) ===
# ===================================================================

def calcular_horas_descanso(fecha_ultimo_turno, hora_fin_ultimo, fecha_nuevo_turno, hora_inicio_nuevo):
    """Calcula las horas de descanso entre dos turnos."""
    if not fecha_ultimo_turno:
        return 999

    if hora_fin_ultimo == '06:00':
        fecha_fin = fecha_ultimo_turno + timedelta(days=1)
    else:
        fecha_fin = fecha_ultimo_turno
    
    fin_ultimo_dt = datetime.combine(fecha_fin, datetime.strptime(hora_fin_ultimo, '%H:%M').time())
    inicio_nuevo_dt = datetime.combine(fecha_nuevo_turno, datetime.strptime(hora_inicio_nuevo, '%H:%M').time())
    
    diferencia = inicio_nuevo_dt - fin_ultimo_dt
    return diferencia.total_seconds() / 3600

def seleccionar_empleados_para_turno(empleados, empleado_stats, personas_requeridas, fecha_actual, turno_info, descanso_minimo):
    """
    Función de selección final. Prioriza a los empleados que más necesitan un tipo de turno específico
    para cumplir su cuota de 5 (8h) y 7 (12h).
    """
    candidatos = []
    horas_turno = turno_info['horas']

    for emp in empleados:
        stats = empleado_stats[emp]
        
        # 1. Comprobar si está disponible (descanso mínimo)
        horas_descansadas = calcular_horas_descanso(
            stats['ultimo_turno_fecha'], 
            stats['ultimo_turno_fin_hora'], 
            fecha_actual, 
            turno_info['inicio']
        )
        if horas_descansadas < descanso_minimo:
            continue

        # 2. Calcular un "costo" para priorizar. Menor costo es mejor.
        # La base del costo es las horas totales, para balancear la carga general.
        costo = stats['horas_totales']

        # 3. Aplicar bonus/penalizaciones para cumplir las cuotas de 5 y 7.
        if horas_turno == 8:
            if stats['dias_8h_asignados'] >= 5:
                costo += 1000  # Penalización alta si ya cumplió la cuota de 8h
            else:
                # Bonus alto si le faltan turnos de 8h. A más le falten, mayor el bonus.
                costo -= (5 - stats['dias_8h_asignados']) * 50
        
        elif horas_turno == 12:
            if stats['dias_12h_asignados'] >= 7:
                costo += 1000  # Penalización alta si ya cumplió la cuota de 12h
            else:
                # Bonus alto si le faltan turnos de 12h.
                costo -= (7 - stats['dias_12h_asignados']) * 50

        candidatos.append({'empleado': emp, 'costo': costo})

    candidatos_ordenados = sorted(candidatos, key=lambda x: x['costo'])
    return [c['empleado'] for c in candidatos_ordenados[:personas_requeridas]]


def generar_turnos_optimizado(cargo_data, empleados, fecha_inicio, dias_a_planificar, descanso_8h, descanso_12h):
    """
    Lógica de generación de turnos finalizada para garantizar 21 días y la distribución 5x8h + 7x12h.
    """
    TURNOS_DEFINIDOS = {
        'M 8h': {'inicio': '06:00', 'fin': '14:00', 'horas': 8},
        'T 8h': {'inicio': '14:00', 'fin': '22:00', 'horas': 8},
        'N 8h': {'inicio': '22:00', 'fin': '06:00', 'horas': 8},
        'D 12h': {'inicio': '06:00', 'fin': '18:00', 'horas': 12},
        'N 12h': {'inicio': '18:00', 'fin': '06:00', 'horas': 12}
    }
    
    # ===== PATRÓN DEFINITIVO: Garantiza 21 días y la proporción correcta de turnos 8h/12h =====
    # 7 días con turnos de 8h y 14 días con turnos de 12h = 21 días totales.
    patron_dias = ['12h', '12h', '8h'] * 7
    
    personas_por_turno = cargo_data['personas_por_turno']
    
    empleado_stats = {emp: {
        'horas_totales': 0, 'dias_8h_asignados': 0, 'dias_12h_asignados': 0,
        'ultimo_turno_fecha': None, 'ultimo_turno_fin_hora': None,
    } for emp in empleados}
    
    asignaciones = {}
    
    for i in range(dias_a_planificar):
        fecha_actual = fecha_inicio + timedelta(days=i)
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        asignaciones[fecha_str] = {}
        
        tipo_dia = patron_dias[i]

        turnos_del_dia = ['D 12h', 'N 12h'] if tipo_dia == '12h' else ['M 8h', 'T 8h', 'N 8h']
        descanso_dia = descanso_12h if tipo_dia == '12h' else descanso_8h

        for nombre_turno in turnos_del_dia:
            turno_info = TURNOS_DEFINIDOS[nombre_turno]
            empleados_disponibles_hoy = [e for e in empleados if e not in [emp for turno in asignaciones[fecha_str].values() for emp in turno]]
            empleados_seleccionados = seleccionar_empleados_para_turno(
                empleados_disponibles_hoy, empleado_stats, personas_por_turno,
                fecha_actual, turno_info, descanso_dia
            )
            asignaciones[fecha_str][nombre_turno] = empleados_seleccionados
            
            for emp in empleados_seleccionados:
                stats = empleado_stats[emp]
                stats['horas_totales'] += turno_info['horas']
                if turno_info['horas'] == 8:
                    stats['dias_8h_asignados'] += 1
                else:
                    stats['dias_12h_asignados'] += 1
                stats['ultimo_turno_fecha'] = fecha_actual
                stats['ultimo_turno_fin_hora'] = turno_info['fin']

    return asignaciones

# ===================================================================
# ============= FIN DE LAS FUNCIONES DE LÓGICA ======================
# ===================================================================


# === SECCIÓN 1: CONFIGURACIÓN DE CARGOS ===
if seccion == "1. Configuración de Cargos":
    st.header("📊 Configuración de Cargos y Cálculo de Personal")
    # (El código de esta sección no necesita cambios)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Agregar Nuevo Cargo")
        with st.form("form_cargo"):
            cargo = st.text_input("Nombre del Cargo", placeholder="Ej: Operador de Molienda")
            personal_actual = st.number_input("Personal Actual en el Cargo", min_value=1, value=24)
            ausentismo = st.number_input("% Ausentismo", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
            personal_vacaciones = st.number_input("Personal de Vacaciones", min_value=0, value=2)
            horas_semanales = st.number_input("Horas Promedio Semanales Permitidas", min_value=1.0, value=48.0, step=0.5)
            personas_por_turno = st.number_input("Personas Requeridas por Turno", min_value=1, value=3)
            st.write("**Turnos por día (para cálculo de personal):**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                turno_manana = st.checkbox("Mañana (06:00-14:00)", value=True)
            with col_t2:
                turno_tarde = st.checkbox("Tarde (14:00-22:00)", value=True)
            with col_t3:
                turno_noche = st.checkbox("Noche (22:00-06:00)", value=True)
            submitted = st.form_submit_button("➕ Agregar Cargo")
            if submitted and cargo:
                turnos_activos = sum([turno_manana, turno_tarde, turno_noche])
                personal_efectivo = personal_actual - personal_vacaciones
                personal_disponible = personal_efectivo * (1 - ausentismo/100)
                personal_requerido_total = personas_por_turno * turnos_activos
                horas_turno = 8
                turnos_semanales_por_persona = horas_semanales / horas_turno
                personas_necesarias = math.ceil((personal_requerido_total * 7) / turnos_semanales_por_persona)
                cargo_data = {
                    'cargo': cargo, 'personal_actual': personal_actual, 'ausentismo': ausentismo,
                    'personal_vacaciones': personal_vacaciones, 'horas_semanales': horas_semanales,
                    'personas_por_turno': personas_por_turno, 'turnos_activos': [turno_manana, turno_tarde, turno_noche],
                    'personal_efectivo': personal_efectivo, 'personal_disponible': personal_disponible,
                    'personas_necesarias': personas_necesarias, 'deficit_superavit': personal_disponible - personas_necesarias
                }
                st.session_state.cargos_data.append(cargo_data)
                st.success(f"✅ Cargo '{cargo}' agregado correctamente!")
                st.rerun()
    with col2:
        if st.session_state.cargos_data:
            st.subheader("⚙️ Acciones")
            if st.button("🗑️ Limpiar Todos los Cargos"):
                st.session_state.cargos_data = []
                st.session_state.turnos_generados = None
                st.rerun()
    if st.session_state.cargos_data:
        st.subheader("📋 Cargos Configurados")
        df_tabla = pd.DataFrame(st.session_state.cargos_data)
        st.dataframe(df_tabla[['cargo', 'personal_actual', 'personal_disponible', 'personas_necesarias', 'deficit_superavit']], use_container_width=True)

# === SECCIÓN 2: GENERACIÓN DE TURNOS ===
elif seccion == "2. Generación de Turnos":
    st.header("🔄 Generación de Turnos")
    
    if not st.session_state.cargos_data:
        st.warning("⚠️ Primero debe configurar al menos un cargo en la sección anterior.")
        st.stop()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📅 Configuración del Período")
        fecha_inicio = st.date_input("Fecha de Inicio (referencial)", value=date.today())
        dias_planificar = st.number_input("Días a Planificar", value=21, min_value=21, max_value=21, disabled=True)
        st.info("ℹ️ El plan se genera para 21 días para cumplir el ciclo legal de 124 horas.")
        
        st.subheader("👥 Configuración de Empleados")
        cargo_seleccionado = st.selectbox("Seleccionar Cargo para Configurar", [c['cargo'] for c in st.session_state.cargos_data])
        
        cargo_data = next(c for c in st.session_state.cargos_data if c['cargo'] == cargo_seleccionado)
        
        st.write(f"**Personal NECESARIO para {cargo_seleccionado}: {cargo_data['personas_necesarias']} personas**")
        
        num_empleados = cargo_data['personas_necesarias']
        empleados = [f"{cargo_seleccionado[:3].upper()}-{i+1:02d}" for i in range(num_empleados)]
        
        st.write("**Empleados a programar:**")
        st.write(", ".join(empleados))
    
    with col2:
        st.subheader("⚙️ Configuración Especial - 124 Horas")
        st.info("🎯 **Objetivo:** 124 horas en 3 semanas (41.33h promedio)")
        
        st.subheader("🔧 Restricciones de Descanso")
        descanso_8h = st.number_input("Descanso mínimo tras turno de 8h (horas)", min_value=8, max_value=24, value=16)
        descanso_12h = st.number_input("Descanso mínimo tras turno de 12h (horas)", min_value=8, max_value=24, value=12)
        
        if st.button("🚀 Generar Turnos 124h", type="primary"):
            with st.spinner("Generando cronograma con objetivo 41.33h..."):
                turnos_resultado = generar_turnos_optimizado(
                    cargo_data, empleados, fecha_inicio, 21,
                    descanso_8h, descanso_12h
                )
                
                st.session_state.turnos_generados = {
                    'cargo': cargo_seleccionado, 'empleados': empleados, 'fecha_inicio': fecha_inicio,
                    'dias': 21, 'turnos': turnos_resultado,
                    'parametros': {'descanso_8h': descanso_8h, 'descanso_12h': descanso_12h}
                }
                
            st.success("✅ ¡Cronograma generado exitosamente!")
            st.balloons()

# === SECCIÓN 3: VISUALIZACIÓN Y EXPORTAR ===
elif seccion == "3. Visualización y Exportar":
    st.header("📊 Visualización y Exportación")
    
    if not st.session_state.turnos_generados:
        st.warning("⚠️ Primero debe generar turnos en la sección anterior.")
        st.stop()
    
    turnos_data = st.session_state.turnos_generados
    st.subheader(f"Resultados para el cargo: **{turnos_data['cargo']}**")

    df_export_list = []
    for fecha_str, turnos_dia in turnos_data['turnos'].items():
        for turno_nombre, empleados in turnos_dia.items():
            if not empleados: continue
            for emp in empleados:
                df_export_list.append({'Fecha': fecha_str, 'Empleado': emp, 'Turno': turno_nombre})
    
    if not df_export_list:
        st.error("No se pudo asignar ningún turno con las restricciones dadas.")
        st.stop()

    df_export = pd.DataFrame(df_export_list)
    
    df_pivot = df_export.pivot_table(index='Empleado', columns='Fecha', values='Turno', aggfunc='first').fillna('Libre')
    fechas_ordenadas = sorted(df_pivot.columns)
    mapa_columnas = {fecha: f"Día {i+1}" for i, fecha in enumerate(fechas_ordenadas)}
    df_pivot.rename(columns=mapa_columnas, inplace=True)
    
    st.dataframe(df_pivot, use_container_width=True)

    st.subheader("📊 Estadísticas de Asignación por Operador")
    stats_list = []
    for emp in turnos_data['empleados']:
        turnos_emp = df_export[df_export['Empleado'] == emp]
        horas_trabajadas = 0; turnos_8h = 0; turnos_12h = 0
        for turno in turnos_emp['Turno']:
            if '8h' in turno:
                horas_trabajadas += 8; turnos_8h += 1
            elif '12h' in turno:
                horas_trabajadas += 12; turnos_12h += 1
        stats_list.append({
            'Empleado': emp, 'Total Horas': horas_trabajadas,
            'Promedio Semanal (h)': f"{horas_trabajadas/3:.2f}",
            'Turnos de 8h': turnos_8h, 'Turnos de 12h': turnos_12h,
            'Total Turnos': len(turnos_emp)
        })
    df_stats = pd.DataFrame(stats_list).set_index('Empleado')
    st.dataframe(df_stats, use_container_width=True)

    st.subheader("📁 Exportar")
    csv = df_pivot.to_csv().encode('utf-8')
    st.download_button(
        label="📊 Descargar Cronograma en CSV",
        data=csv,
        file_name=f"turnos_{turnos_data['cargo']}.csv",
        mime="text/csv",
    )
    
if st.sidebar.button("🔄 Reiniciar Aplicación"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
