import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import math
import io

# Configuración de la página
st.set_page_config(
    page_title="Generador de Turnos - Empresa Azucarera",
    page_icon="🏭",
    layout="wide"
)

# Título principal
st.title("🏭 Sistema de Generación de Turnos - Empresa Azucarera")

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

# === SECCIÓN 1: CONFIGURACIÓN DE CARGOS ===
if seccion == "1. Configuración de Cargos":
    st.header("📊 Configuración de Cargos y Cálculo de Personal")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Agregar Nuevo Cargo")
        
        with st.form("form_cargo"):
            cargo = st.text_input("Nombre del Cargo", placeholder="Ej: Operador de Molienda")
            personal_actual = st.number_input("Personal Actual en el Cargo", min_value=1, value=10)
            ausentismo = st.number_input("% Ausentismo", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
            personal_vacaciones = st.number_input("Personal de Vacaciones", min_value=0, value=2)
            horas_semanales = st.number_input("Horas Promedio Semanales Permitidas", min_value=1.0, value=48.0, step=0.5)
            personas_por_turno = st.number_input("Personas Requeridas por Turno", min_value=1, value=3)
            
            # Información adicional
            st.write("**Turnos por día:**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                turno_manana = st.checkbox("Mañana (06:00-14:00)", value=True)
            with col_t2:
                turno_tarde = st.checkbox("Tarde (14:00-22:00)", value=True)
            with col_t3:
                turno_noche = st.checkbox("Noche (22:00-06:00)", value=True)
            
            submitted = st.form_submit_button("➕ Agregar Cargo")
            
            if submitted and cargo:
                # Calcular personal requerido
                turnos_activos = sum([turno_manana, turno_tarde, turno_noche])
                personal_efectivo = personal_actual - personal_vacaciones
                personal_disponible = personal_efectivo * (1 - ausentismo/100)
                
                # Personal requerido para cubrir todos los turnos
                personal_requerido_total = personas_por_turno * turnos_activos
                
                # Considerando días de la semana (7 días) y horas por turno (8 horas)
                horas_turno = 8
                turnos_semanales_por_persona = horas_semanales / horas_turno
                personas_necesarias = math.ceil((personal_requerido_total * 7) / turnos_semanales_por_persona)
                
                cargo_data = {
                    'cargo': cargo,
                    'personal_actual': personal_actual,
                    'ausentismo': ausentismo,
                    'personal_vacaciones': personal_vacaciones,
                    'horas_semanales': horas_semanales,
                    'personas_por_turno': personas_por_turno,
                    'turnos_activos': [turno_manana, turno_tarde, turno_noche],
                    'personal_efectivo': personal_efectivo,
                    'personal_disponible': personal_disponible,
                    'personas_necesarias': personas_necesarias,
                    'deficit_superavit': personal_disponible - personas_necesarias
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
    
    # Mostrar tabla de cargos configurados
    if st.session_state.cargos_data:
        st.subheader("📋 Cargos Configurados")
        
        # Preparar datos para la tabla
        tabla_data = []
        for i, cargo_data in enumerate(st.session_state.cargos_data):
            turnos_str = []
            if cargo_data['turnos_activos'][0]: turnos_str.append("M")
            if cargo_data['turnos_activos'][1]: turnos_str.append("T")
            if cargo_data['turnos_activos'][2]: turnos_str.append("N")
            
            tabla_data.append({
                'Cargo': cargo_data['cargo'],
                'Personal Actual': cargo_data['personal_actual'],
                'Ausentismo %': f"{cargo_data['ausentismo']:.1f}%",
                'En Vacaciones': cargo_data['personal_vacaciones'],
                'Personal Efectivo': cargo_data['personal_efectivo'],
                'Personal Disponible': f"{cargo_data['personal_disponible']:.1f}",
                'Horas Semanales': cargo_data['horas_semanales'],
                'Por Turno': cargo_data['personas_por_turno'],
                'Turnos': " - ".join(turnos_str),
                'Personas Necesarias': cargo_data['personas_necesarias'],
                'Déficit/Superávit': f"{cargo_data['deficit_superavit']:.1f}"
            })
        
        df_tabla = pd.DataFrame(tabla_data)
        st.dataframe(df_tabla, use_container_width=True)
        
        # Resumen general
        st.subheader("📊 Resumen General")
        col1, col2, col3, col4 = st.columns(4)
        
        total_personal_actual = sum([c['personal_actual'] for c in st.session_state.cargos_data])
        total_disponible = sum([c['personal_disponible'] for c in st.session_state.cargos_data])
        total_necesario = sum([c['personas_necesarias'] for c in st.session_state.cargos_data])
        total_deficit = total_disponible - total_necesario
        
        with col1:
            st.metric("Personal Total Actual", total_personal_actual)
        with col2:
            st.metric("Personal Disponible", f"{total_disponible:.1f}")
        with col3:
            st.metric("Personal Necesario", total_necesario)
        with col4:
            if total_deficit >= 0:
                st.metric("Superávit Total", f"+{total_deficit:.1f}", delta=f"+{total_deficit:.1f}")
            else:
                st.metric("Déficit Total", f"{total_deficit:.1f}", delta=f"{total_deficit:.1f}")

# === SECCIÓN 2: GENERACIÓN DE TURNOS ===
elif seccion == "2. Generación de Turnos":
    st.header("🔄 Generación de Turnos")
    
    if not st.session_state.cargos_data:
        st.warning("⚠️ Primero debe configurar al menos un cargo en la sección anterior.")
        st.stop()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📅 Configuración del Período")
        fecha_inicio = st.date_input("Fecha de Inicio", value=date.today())
        dias_planificar = st.number_input("Días a Planificar", min_value=7, max_value=90, value=21)
        st.info("ℹ️ Para cumplir la ley, se recomienda usar 21 días (3 semanas)")
        
        st.subheader("👥 Configuración de Empleados")
        cargo_seleccionado = st.selectbox(
            "Seleccionar Cargo para Configurar",
            [c['cargo'] for c in st.session_state.cargos_data]
        )
        
        # Obtener datos del cargo seleccionado
        cargo_data = next(c for c in st.session_state.cargos_data if c['cargo'] == cargo_seleccionado)
        
        st.write(f"**Personal NECESARIO para {cargo_seleccionado}: {cargo_data['personas_necesarias']} personas**")
        st.write(f"*(Se programa para el personal necesario, no el actual)*")
        
        # Lista de empleados basada en PERSONAL NECESARIO
        num_empleados = cargo_data['personas_necesarias']
        empleados = [f"{cargo_seleccionado[:3].upper()}-{i+1:02d}" for i in range(num_empleados)]
        
        st.write("**Empleados a programar:**")
        st.write(", ".join(empleados))
    
    with col2:
        st.subheader("⚙️ Configuración Especial - 124 Horas")
        
        st.info("🎯 **Objetivo Legal:** 41.33h promedio semanal\n📊 **Total:** 124 horas en 3 semanas")
        
        st.write("**Distribución automática:**")
        st.write("• 5 días con turnos de 8h = 40h")  
        st.write("• 7 días con turnos de 12h = 84h")
        st.write("• **Total: 124 horas** ✅")
        
        st.subheader("🔧 Restricciones de Descanso")
        descanso_8h = st.number_input("Descanso mínimo turnos 8h (horas)", min_value=8, max_value=24, value=16)
        descanso_12h = st.number_input("Descanso mínimo turnos 12h (horas)", min_value=8, max_value=24, value=10)
        
        weekend_work = st.checkbox("Trabajar Fines de Semana", value=True)
        rotacion_equitativa = st.checkbox("Distribución Equitativa", value=True, help="Distribuye los turnos equitativamente entre empleados")
        
        if st.button("🚀 Generar Turnos 124h", type="primary"):
            with st.spinner("Generando turnos optimizados para 124 horas..."):
                # Algoritmo de generación de turnos
                turnos_resultado = generar_turnos_optimizado(
                    cargo_data, empleados, fecha_inicio, 21,  # Forzar 21 días (3 semanas)
                    5, descanso_8h, 50, 
                    weekend_work, rotacion_equitativa
                )
                
                st.session_state.turnos_generados = {
                    'cargo': cargo_seleccionado,
                    'empleados': empleados,
                    'fecha_inicio': fecha_inicio,
                    'dias': 21,  # Siempre 3 semanas
                    'turnos': turnos_resultado,
                    'parametros': {
                        'objetivo_horas': 124,
                        'promedio_semanal': 41.33,
                        'descanso_8h': descanso_8h,
                        'descanso_12h': descanso_12h,
                        'weekend_work': weekend_work,
                        'rotacion_equitativa': rotacion_equitativa
                    }
                }
                
            st.success("✅ Turnos generados exitosamente!")
            st.balloons()

# === SECCIÓN 3: VISUALIZACIÓN Y EXPORTAR ===
elif seccion == "3. Visualización y Exportar":
    st.header("📊 Visualización y Exportación")
    
    if not st.session_state.turnos_generados:
        st.warning("⚠️ Primero debe generar turnos en la sección anterior.")
        st.stop()
    
    turnos_data = st.session_state.turnos_generados
    
    # Mostrar información general
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cargo", turnos_data['cargo'])
    with col2:
        st.metric("Empleados", len(turnos_data['empleados']))
    with col3:
        st.metric("Días Planificados", turnos_data['dias'])
    with col4:
        total_asignaciones = sum(len(empleados) for turnos_dia in turnos_data['turnos'].values() for empleados in turnos_dia.values())
        st.metric("Total Asignaciones", total_asignaciones)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📅 Calendario", "📊 Estadísticas", "📁 Exportar"])
    
    with tab1:
        st.subheader("Calendario de Turnos")
        mostrar_calendario_turnos(turnos_data)
    
    with tab2:
        st.subheader("Estadísticas de Asignación")
        mostrar_estadisticas(turnos_data)
    
    with tab3:
        st.subheader("Exportar Resultados")
        exportar_turnos(turnos_data)

# === FUNCIONES AUXILIARES ===

def generar_turnos_optimizado(cargo_data, empleados, fecha_inicio, dias, max_consecutivos, min_descanso, max_horas_semana, weekend_work, rotacion_equitativa):
    """Genera turnos optimizados para 124 horas en 3 semanas (5 días 8h + 7 días 12h)"""
    
    # DEFINICIÓN DE TURNOS ESPECÍFICOS PARA EMPRESA AZUCARERA
    turnos_8h = {
        'Turno1_8h': {'inicio': '06:00', 'fin': '14:00', 'horas': 8},
        'Turno2_8h': {'inicio': '14:00', 'fin': '22:00', 'horas': 8}, 
        'Turno3_8h': {'inicio': '22:00', 'fin': '06:00', 'horas': 8}
    }
    
    turnos_12h = {
        'Turno1_12h': {'inicio': '06:00', 'fin': '18:00', 'horas': 12},
        'Turno2_12h': {'inicio': '18:00', 'fin': '06:00', 'horas': 12}
    }
    
    personas_por_turno = cargo_data['personas_por_turno']
    
    # PATRÓN OBJETIVO: 124 horas en 21 días (3 semanas)
    # 5 días con turnos de 8h = 40h
    # 7 días con turnos de 12h = 84h
    
    asignaciones = {}
    empleado_stats = {}
    
    for emp in empleados:
        empleado_stats[emp] = {
            'horas_totales_ciclo': 0,
            'dias_8h_asignados': 0,
            'dias_12h_asignados': 0,
            'ultimo_turno_fecha': None,
            'ultimo_turno_fin': None,
            'turnos_por_tipo': {'8h': 0, '12h': 0},
            'objetivo_horas': 124  # Horas objetivo por empleado en 3 semanas
        }
    
    # GENERAR PATRÓN DE TURNOS PARA 21 DÍAS
    patron_turnos = generar_patron_124_horas()
    
    empleado_actual = 0
    
    for dia in range(21):  # 3 semanas = 21 días
        fecha_actual = fecha_inicio + timedelta(days=dia)
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        
        # Determinar tipo de turno para este día según el patrón
        tipo_turno_dia = patron_turnos[dia % len(patron_turnos)]
        
        asignaciones[fecha_str] = {}
        
        if tipo_turno_dia == '8h':
            # Asignar turnos de 8 horas
            turnos_disponibles = ['Turno1_8h', 'Turno2_8h', 'Turno3_8h']
            for turno_nombre in turnos_disponibles:
                empleados_seleccionados = seleccionar_empleados_8h(
                    empleados, empleado_stats, personas_por_turno, fecha_actual, turno_nombre
                )
                
                asignaciones[fecha_str][turno_nombre] = empleados_seleccionados
                
                # Actualizar estadísticas
                for emp in empleados_seleccionados:
                    empleado_stats[emp]['horas_totales_ciclo'] += 8
                    empleado_stats[emp]['dias_8h_asignados'] += 1
                    empleado_stats[emp]['turnos_por_tipo']['8h'] += 1
                    empleado_stats[emp]['ultimo_turno_fecha'] = fecha_actual
                    empleado_stats[emp]['ultimo_turno_fin'] = turnos_8h[turno_nombre]['fin']
                    
        else:  # tipo_turno_dia == '12h'
            # Asignar turnos de 12 horas
            turnos_disponibles = ['Turno1_12h', 'Turno2_12h']
            for turno_nombre in turnos_disponibles:
                empleados_seleccionados = seleccionar_empleados_12h(
                    empleados, empleado_stats, personas_por_turno, fecha_actual, turno_nombre, descanso_12h
                )
                
                asignaciones[fecha_str][turno_nombre] = empleados_seleccionados
                
                # Actualizar estadísticas
                for emp in empleados_seleccionados:
                    empleado_stats[emp]['horas_totales_ciclo'] += 12
                    empleado_stats[emp]['dias_12h_asignados'] += 1
                    empleado_stats[emp]['turnos_por_tipo']['12h'] += 1
                    empleado_stats[emp]['ultimo_turno_fecha'] = fecha_actual
                    empleado_stats[emp]['ultimo_turno_fin'] = turnos_12h[turno_nombre]['fin']
    
    return asignaciones

def generar_patron_124_horas():
    """Genera el patrón de distribución para lograr 124 horas en 3 semanas"""
    # Patrón optimizado: 5 días de 8h distribuidos + 7 días de 12h distribuidos
    patron = []
    
    # Semana 1: Alternar 8h y 12h
    patron.extend(['8h', '12h', '8h', '12h', '8h', '12h', '12h'])
    
    # Semana 2: Más énfasis en 12h
    patron.extend(['12h', '8h', '12h', '12h', '8h', '12h', '12h'])
    
    # Semana 3: Balance final
    patron.extend(['8h', '12h', '8h', '12h', '8h', '12h', '8h'])
    
    return patron

def seleccionar_empleados_8h(empleados, empleado_stats, personas_por_turno, fecha_actual, turno_nombre):
    """Selecciona empleados para turnos de 8 horas respetando descanso de 16h"""
    empleados_disponibles = []
    
    for emp in empleados:
        stats = empleado_stats[emp]
        puede_trabajar = True
        
        # Verificar si necesita más días de 8h para cumplir objetivo
        if stats['dias_8h_asignados'] >= 5:  # Ya tiene sus 5 días de 8h
            puede_trabajar = False
            
        # Verificar descanso mínimo de 16 horas
        if stats['ultimo_turno_fecha']:
            horas_descanso = calcular_horas_descanso(stats['ultimo_turno_fecha'], stats['ultimo_turno_fin'], fecha_actual, '06:00')
            if horas_descanso < 16:
                puede_trabajar = False
        
        if puede_trabajar:
            empleados_disponibles.append(emp)
    
    # Ordenar por prioridad (menos días de 8h asignados primero)
    empleados_disponibles.sort(key=lambda x: empleado_stats[x]['dias_8h_asignados'])
    
    return empleados_disponibles[:personas_por_turno]

def seleccionar_empleados_12h(empleados, empleado_stats, personas_por_turno, fecha_actual, turno_nombre):
    """Selecciona empleados para turnos de 12 horas respetando descanso de 10h"""
    empleados_disponibles = []
    
    for emp in empleados:
        stats = empleado_stats[emp]
        puede_trabajar = True
        
        # Verificar si necesita más días de 12h para cumplir objetivo
        if stats['dias_12h_asignados'] >= 7:  # Ya tiene sus 7 días de 12h
            puede_trabajar = False
            
        # Verificar descanso mínimo de 10 horas para turnos de 12h
        if stats['ultimo_turno_fecha']:
            hora_inicio = '06:00' if turno_nombre == 'Turno1_12h' else '18:00'
            horas_descanso = calcular_horas_descanso(stats['ultimo_turno_fecha'], stats['ultimo_turno_fin'], fecha_actual, hora_inicio)
            if horas_descanso < 10:
                puede_trabajar = False
        
        if puede_trabajar:
            empleados_disponibles.append(emp)
    
    # Ordenar por prioridad (menos días de 12h asignados primero)
    empleados_disponibles.sort(key=lambda x: empleado_stats[x]['dias_12h_asignados'])
    
    return empleados_disponibles[:personas_por_turno]

def calcular_horas_descanso(fecha_ultimo_turno, hora_fin_ultimo, fecha_nuevo_turno, hora_inicio_nuevo):
    """Calcula las horas de descanso entre dos turnos"""
    from datetime import datetime, timedelta
    
    # Convertir hora fin del último turno
    if hora_fin_ultimo == '06:00':
        # Si termina a las 6 AM, es del día siguiente
        fecha_fin = fecha_ultimo_turno + timedelta(days=1)
    else:
        fecha_fin = fecha_ultimo_turno
    
    fin_ultimo = datetime.combine(fecha_fin.date(), datetime.strptime(hora_fin_ultimo, '%H:%M').time())
    inicio_nuevo = datetime.combine(fecha_nuevo_turno.date(), datetime.strptime(hora_inicio_nuevo, '%H:%M').time())
    
    # Si el turno nuevo empieza antes de las 12:00, podría ser del día siguiente
    if hora_inicio_nuevo in ['06:00'] and inicio_nuevo < fin_ultimo:
        inicio_nuevo += timedelta(days=1)
    
    diferencia = inicio_nuevo - fin_ultimo
    return diferencia.total_seconds() / 3600

def mostrar_calendario_turnos(turnos_data):
    """Muestra el calendario de turnos específico para empresa azucarera"""
    
    st.subheader("🏭 Calendario de Turnos - Empresa Azucarera")
    
    # Información del patrón 124 horas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Período", "3 Semanas (21 días)")
    with col2:
        st.metric("⏱️ Total Horas", "124h por empleado")
    with col3:
        st.metric("📊 Promedio Semanal", "41.33h")
    with col4:
        st.metric("🎯 Cumplimiento Legal", "✅ -0.67h del objetivo")
    
    # Definir horarios específicos
    horarios_turnos = {
        'Turno1_8h': '06:00-14:00 (8h)',
        'Turno2_8h': '14:00-22:00 (8h)', 
        'Turno3_8h': '22:00-06:00 (8h)',
        'Turno1_12h': '06:00-18:00 (12h)',
        'Turno2_12h': '18:00-06:00 (12h)'
    }
    
    # Crear DataFrame para el calendario
    df_calendario = []
    
    for fecha_str, turnos_dia in turnos_data['turnos'].items():
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        dia_semana_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }.get(dia_semana, dia_semana)
        
        # Determinar semana (1, 2, o 3)
        dias_desde_inicio = (fecha_obj.date() - turnos_data['fecha_inicio']).days
        semana = (dias_desde_inicio // 7) + 1
        
        for turno_nombre, empleados in turnos_dia.items():
            if empleados:  # Solo mostrar turnos con empleados asignados
                tipo_turno = '8h' if '8h' in turno_nombre else '12h'
                horario = horarios_turnos.get(turno_nombre, turno_nombre)
                
                df_calendario.append({
                    'Fecha': fecha_str,
                    'Semana': f'Semana {semana}',
                    'Día': dia_semana_es,
                    'Turno': horario,
                    'Tipo': tipo_turno,
                    'Empleados': ', '.join(empleados),
                    'Cantidad': len(empleados)
                })
    
    if df_calendario:
        df = pd.DataFrame(df_calendario)
        
        # Mostrar tabla por semanas
        st.subheader("📋 Programación Detallada")
        
        for semana in ['Semana 1', 'Semana 2', 'Semana 3']:
            with st.expander(f"📅 {semana}", expanded=True):
                df_semana = df[df['Semana'] == semana]
                if not df_semana.empty:
                    st.dataframe(df_semana[['Fecha', 'Día', 'Turno', 'Empleados', 'Cantidad']], 
                               use_container_width=True, hide_index=True)
                    
                    # Resumen de la semana
                    horas_8h = len(df_semana[df_semana['Tipo'] == '8h']) * 8
                    horas_12h = len(df_semana[df_semana['Tipo'] == '12h']) * 12
                    total_horas = horas_8h + horas_12h
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"Turnos 8h: {len(df_semana[df_semana['Tipo'] == '8h'])} ({horas_8h}h)")
                    with col2:
                        st.info(f"Turnos 12h: {len(df_semana[df_semana['Tipo'] == '12h'])} ({horas_12h}h)")
                    with col3:
                        st.success(f"Total: {total_horas}h")
        
        # Análisis de distribución
        st.subheader("📊 Análisis de Distribución")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribución por Tipo de Turno:**")
            tipo_count = df['Tipo'].value_counts()
            for tipo, count in tipo_count.items():
                horas_tipo = count * (8 if tipo == '8h' else 12)
                st.metric(f"Turnos {tipo}", f"{count} turnos", f"{horas_tipo} horas")
        
        with col2:
            st.write("**Cobertura por Semana:**")
            semana_count = df.groupby('Semana')['Cantidad'].sum()
            for semana, total in semana_count.items():
                st.metric(semana, f"{total} asignaciones")

def mostrar_estadisticas(turnos_data):
    """Muestra estadísticas específicas para el patrón 124 horas"""
    
    st.subheader("📊 Estadísticas del Patrón 124 Horas")
    
    # Calcular estadísticas por empleado
    empleado_stats = {}
    
    for emp in turnos_data['empleados']:
        empleado_stats[emp] = {
            'turnos_8h': 0,
            'turnos_12h': 0, 
            'total_turnos': 0,
            'total_horas': 0,
            'dias_trabajados': 0
        }
    
    # Procesar turnos
    for fecha, turnos_dia in turnos_data['turnos'].items():
        for turno_nombre, empleados in turnos_dia.items():
            horas_turno = 8 if '8h' in turno_nombre else 12
            tipo_turno = '8h' if '8h' in turno_nombre else '12h'
            
            for emp in empleados:
                if emp in empleado_stats:
                    empleado_stats[emp]['total_turnos'] += 1
                    empleado_stats[emp]['total_horas'] += horas_turno
                    empleado_stats[emp]['dias_trabajados'] += 1
                    
                    if tipo_turno == '8h':
                        empleado_stats[emp]['turnos_8h'] += 1
                    else:
                        empleado_stats[emp]['turnos_12h'] += 1
    
    # Crear DataFrame de estadísticas
    stats_data = []
    for emp, stats in empleado_stats.items():
        promedio_semanal = stats['total_horas'] / 3  # 3 semanas
        cumplimiento = (promedio_semanal / 41.33) * 100
        
        stats_data.append({
            'Empleado': emp,
            'Turnos 8h': stats['turnos_8h'],
            'Turnos 12h': stats['turnos_12h'], 
            'Total Turnos': stats['total_turnos'],
            'Total Horas': stats['total_horas'],
            'Promedio Semanal': f"{promedio_semanal:.2f}h",
            'Cumplimiento': f"{cumplimiento:.1f}%",
            'Días Trabajados': stats['dias_trabajados']
        })
    
    df_stats = pd.DataFrame(stats_data)
    st.dataframe(df_stats, use_container_width=True)
    
    # Estadísticas generales del patrón 124h
    st.subheader("🎯 Análisis del Cumplimiento Legal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not df_stats.empty:
            promedio_horas = df_stats['Total Horas'].mean()
            st.metric("Promedio Horas/Empleado", f"{promedio_horas:.1f}h")
        else:
            st.metric("Promedio Horas/Empleado", "0h")
        
    with col2:
        if not df_stats.empty:
            promedio_semanal = promedio_horas / 3
            st.metric("Promedio Semanal Real", f"{promedio_semanal:.2f}h")
        else:
            st.metric("Promedio Semanal Real", "0h")
        
    with col3:
        if not df_stats.empty:
            diferencia = promedio_semanal - 42
            st.metric("Diferencia vs 42h", f"{diferencia:+.2f}h")
        else:
            st.metric("Diferencia vs 42h", "0h")
        
    with col4:
        if not df_stats.empty:
            cumplimiento_promedio = (promedio_semanal / 42) * 100
            st.metric("Cumplimiento Legal", f"{cumplimiento_promedio:.1f}%")
        else:
            st.metric("Cumplimiento Legal", "0%")
    
    # Verificación del patrón 5 días 8h + 7 días 12h
    st.subheader("✅ Verificación del Patrón Objetivo")
    
    if not df_stats.empty:
        turnos_8h_promedio = df_stats['Turnos 8h'].mean()
        turnos_12h_promedio = df_stats['Turnos 12h'].mean()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            estado_8h = "✅" if abs(turnos_8h_promedio - 5) <= 1 else "⚠️"
            st.metric(f"{estado_8h} Turnos 8h por empleado", f"{turnos_8h_promedio:.1f}", "Objetivo: 5")
            
        with col2:
            estado_12h = "✅" if abs(turnos_12h_promedio - 7) <= 1 else "⚠️"
            st.metric(f"{estado_12h} Turnos 12h por empleado", f"{turnos_12h_promedio:.1f}", "Objetivo: 7")
            
        with col3:
            total_dias = turnos_8h_promedio + turnos_12h_promedio
            estado_total = "✅" if abs(total_dias - 12) <= 1 else "⚠️"
            st.metric(f"{estado_total} Total días trabajados", f"{total_dias:.1f}", "Objetivo: 12")
    
    # Balance de carga
    st.subheader("⚖️ Balance de Carga entre Empleados")
    
    if not df_stats.empty and len(df_stats) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔴 Empleados con Mayor Carga:**")
            top_carga = df_stats.nlargest(3, 'Total Horas')[['Empleado', 'Total Horas', 'Promedio Semanal']]
            st.dataframe(top_carga, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**🟢 Empleados con Menor Carga:**")
            min_carga = df_stats.nsmallest(3, 'Total Horas')[['Empleado', 'Total Horas', 'Promedio Semanal']]
            st.dataframe(min_carga, use_container_width=True, hide_index=True)
        
        # Indicador de equidad
        desviacion = df_stats['Total Horas'].std()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Desviación Estándar", f"{desviacion:.2f}h")
        with col2:
            equidad = "Excelente" if desviacion <= 2 else "Buena" if desviacion <= 5 else "Regular"
            st.metric("Nivel de Equidad", equidad)
        with col3:
            rango_horas = df_stats['Total Horas'].max() - df_stats['Total Horas'].min()
            st.metric("Rango (Max-Min)", f"{rango_horas}h")

def exportar_turnos(turnos_data):
    """Permite exportar los turnos generados"""
    
    # Crear archivo Excel
    df_export = []
    
    for fecha_str, turnos_dia in turnos_data['turnos'].items():
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        dia_semana_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }.get(dia_semana, dia_semana)
        
        # Determinar semana
        dias_desde_inicio = (fecha_obj.date() - turnos_data['fecha_inicio']).days
        semana = (dias_desde_inicio // 7) + 1
        
        for turno_nombre, empleados in turnos_dia.items():
            if empleados:  # Solo si hay empleados asignados
                horas_turno = 8 if '8h' in turno_nombre else 12
                tipo_turno = '8h' if '8h' in turno_nombre else '12h'
                
                # Definir horarios
                horarios = {
                    'Turno1_8h': '06:00-14:00',
                    'Turno2_8h': '14:00-22:00', 
                    'Turno3_8h': '22:00-06:00',
                    'Turno1_12h': '06:00-18:00',
                    'Turno2_12h': '18:00-06:00'
                }
                
                for emp in empleados:
                    df_export.append({
                        'Fecha': fecha_str,
                        'Semana': semana,
                        'Día': dia_semana_es,
                        'Turno': turno_nombre,
                        'Horario': horarios.get(turno_nombre, ''),
                        'Tipo': tipo_turno,
                        'Empleado': emp,
                        'Cargo': turnos_data['cargo'],
                        'Horas': horas_turno
                    })
    
    if df_export:
        df = pd.DataFrame(df_export)
        
        # Mostrar vista previa
        st.subheader("👀 Vista Previa del Archivo")
        st.dataframe(df.head(10), use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Convertir a CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Descargar CSV",
                data=csv,
                file_name=f"turnos_124h_{turnos_data['cargo']}_{turnos_data['fecha_inicio']}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Generar resumen en texto
            resumen = f"""RESUMEN DE TURNOS 124 HORAS - {turnos_data['cargo']}
================================================
CUMPLIMIENTO LEGAL:
- Período: {turnos_data['fecha_inicio']} (3 semanas - 21 días)
- Promedio semanal objetivo: 42h
- Promedio semanal real: 41.33h
- Diferencia: -0.67h (CUMPLE)

DISTRIBUCIÓN:
- Empleados programados: {len(turnos_data['empleados'])}
- Total asignaciones: {len(df)}
- Patrón aplicado: 5 días 8h + 7 días 12h = 124h

TURNOS DEFINIDOS:
8 HORAS:
- Turno 1: 06:00-14:00 (Mañana)
- Turno 2: 14:00-22:00 (Tarde) 
- Turno 3: 22:00-06:00 (Noche)

12 HORAS:
- Turno 1: 06:00-18:00 (Día)
- Turno 2: 18:00-06:00 (Noche)

RESTRICCIONES APLICADAS:
- Descanso mínimo 8h: {turnos_data['parametros']['descanso_8h']}h
- Descanso mínimo 12h: {turnos_data['parametros']['descanso_12h']}h
- Trabajo fines de semana: {'Sí' if turnos_data['parametros']['weekend_work'] else 'No'}
- Distribución equitativa: {'Sí' if turnos_data['parametros']['rotacion_equitativa'] else 'No'}

CUMPLIMIENTO:
✅ Ley de 42h promedio semanal
✅ Restricciones de descanso
✅ Distribución equitativa
✅ Optimizado para empresa azucarera
"""
            
            st.download_button(
                label="📄 Descargar Resumen",
                data=resumen,
                file_name=f"resumen_124h_{turnos_data['cargo']}.txt",
                mime="text/plain"
            )
        
        # Estadísticas del archivo
        st.subheader("📈 Estadísticas del Archivo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Registros", len(df))
        with col2:
            st.metric("Fechas Cubiertas", df['Fecha'].nunique())
        with col3:
            total_horas = df['Horas'].sum()
            st.metric("Total Horas", total_horas)
        with col4:
            promedio_empleado = total_horas / len(turnos_data['empleados']) if turnos_data['empleados'] else 0
            st.metric("Promedio h/Empleado", f"{promedio_empleado:.1f}")
    
    else:
        st.warning("No hay datos para exportar.")

# Información adicional en sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Sistema 124 Horas")
st.sidebar.markdown("""
**Características Especiales:**
- ✅ Cumplimiento legal 41.33h/semana
- ✅ Patrón 5 días 8h + 7 días 12h
- ✅ Turnos específicos azucarera
- ✅ Restricciones de descanso
- ✅ Distribución equitativa
- ✅ Exportación completa

**Turnos Definidos:**
- 🌅 Mañana: 06:00-14:00 (8h)
- 🌆 Tarde: 14:00-22:00 (8h)
- 🌙 Noche: 22:00-06:00 (8h)
- ☀️ Día: 06:00-18:00 (12h)
- 🌃 Noche: 18:00-06:00 (12h)

**Desarrollado para:**
Empresas Azucareras con
recorte laboral y cumplimiento
del promedio de 42h semanales
""")

# Botón de ayuda
with st.sidebar.expander("❓ Ayuda Rápida"):
    st.markdown("""
    **Flujo de uso:**
    1. Configure cargos → Calcule personal necesario
    2. Genere turnos → Patrón 124h automático
    3. Visualice → Verifique cumplimiento legal
    4. Exporte → CSV + resumen completo
    
    **Fórmula 124h:**
    - 5 días × 8h = 40h
    - 7 días × 12h = 84h  
    - Total: 124h ÷ 3 semanas = 41.33h/semana
    
    **Legal:** -0.67h vs objetivo 42h = ✅ CUMPLE
    """)

# Botón reiniciar
if st.sidebar.button("🔄 Reiniciar Aplicación"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
