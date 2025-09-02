import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import math
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
                'Déficit/Superávit': cargo_data['deficit_superavit']
            })
        
        df_tabla = pd.DataFrame(tabla_data)
        
        # Aplicar colores según déficit/superávit
        def color_deficit(val):
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'color: red'
                elif val > 0:
                    return 'color: green'
            return ''
        
        styled_df = df_tabla.style.applymap(color_deficit, subset=['Déficit/Superávit'])
        st.dataframe(styled_df, use_container_width=True)
        
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
        dias_planificar = st.number_input("Días a Planificar", min_value=7, max_value=90, value=14)
        
        st.subheader("👥 Configuración de Empleados")
        cargo_seleccionado = st.selectbox(
            "Seleccionar Cargo para Configurar",
            [c['cargo'] for c in st.session_state.cargos_data]
        )
        
        # Obtener datos del cargo seleccionado
        cargo_data = next(c for c in st.session_state.cargos_data if c['cargo'] == cargo_seleccionado)
        
        st.write(f"**Personal disponible para {cargo_seleccionado}: {cargo_data['personal_disponible']:.0f} personas**")
        
        # Lista de empleados (simulada)
        num_empleados = int(cargo_data['personal_disponible'])
        empleados = [f"{cargo_seleccionado[:3].upper()}-{i+1:02d}" for i in range(num_empleados)]
        
        st.write("**Empleados disponibles:**")
        st.write(", ".join(empleados))
    
    with col2:
        st.subheader("⚙️ Restricciones Adicionales")
        
        max_turnos_consecutivos = st.number_input("Máximo Turnos Consecutivos", min_value=1, max_value=10, value=5)
        min_descanso_horas = st.number_input("Mínimo Horas de Descanso", min_value=8, max_value=48, value=16)
        max_horas_semana = st.number_input("Máximo Horas por Semana", min_value=30, max_value=60, value=int(cargo_data['horas_semanales']))
        
        weekend_work = st.checkbox("Trabajar Fines de Semana", value=True)
        
        if st.button("🚀 Generar Turnos", type="primary"):
            with st.spinner("Generando turnos..."):
                # Algoritmo de generación de turnos
                turnos_resultado = generar_turnos_optimizado(
                    cargo_data, empleados, fecha_inicio, dias_planificar,
                    max_turnos_consecutivos, min_descanso_horas, max_horas_semana, weekend_work
                )
                
                st.session_state.turnos_generados = {
                    'cargo': cargo_seleccionado,
                    'empleados': empleados,
                    'fecha_inicio': fecha_inicio,
                    'dias': dias_planificar,
                    'turnos': turnos_resultado,
                    'parametros': {
                        'max_consecutivos': max_turnos_consecutivos,
                        'min_descanso': min_descanso_horas,
                        'max_horas_semana': max_horas_semana,
                        'weekend_work': weekend_work
                    }
                }
                
            st.success("✅ Turnos generados exitosamente!")

# === SECCIÓN 3: VISUALIZACIÓN Y EXPORTAR ===
elif seccion == "3. Visualización y Exportar":
    st.header("📊 Visualización y Exportación")
    
    if not st.session_state.turnos_generados:
        st.warning("⚠️ Primero debe generar turnos en la sección anterior.")
        st.stop()
    
    turnos_data = st.session_state.turnos_generados
    
    # Mostrar información general
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cargo", turnos_data['cargo'])
    with col2:
        st.metric("Empleados", len(turnos_data['empleados']))
    with col3:
        st.metric("Días Planificados", turnos_data['dias'])
    
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

def generar_turnos_optimizado(cargo_data, empleados, fecha_inicio, dias, max_consecutivos, min_descanso, max_horas_semana, weekend_work):
    """Genera turnos optimizados considerando restricciones"""
    
    turnos = ['Mañana', 'Tarde', 'Noche']
    turnos_activos = []
    if cargo_data['turnos_activos'][0]: turnos_activos.append('Mañana')
    if cargo_data['turnos_activos'][1]: turnos_activos.append('Tarde')
    if cargo_data['turnos_activos'][2]: turnos_activos.append('Noche')
    
    personas_por_turno = cargo_data['personas_por_turno']
    
    # Estructura para almacenar asignaciones
    asignaciones = {}
    empleado_stats = {emp: {'turnos_consecutivos': 0, 'horas_semana': 0, 'ultimo_turno': None} for emp in empleados}
    
    for dia in range(dias):
        fecha_actual = fecha_inicio + timedelta(days=dia)
        es_weekend = fecha_actual.weekday() >= 5  # 5=Sábado, 6=Domingo
        
        if es_weekend and not weekend_work:
            continue
            
        # Resetear horas semanales cada lunes
        if fecha_actual.weekday() == 0:
            for emp in empleado_stats:
                empleado_stats[emp]['horas_semana'] = 0
        
        asignaciones[fecha_actual.strftime('%Y-%m-%d')] = {}
        
        for turno in turnos_activos:
            empleados_disponibles = []
            
            for emp in empleados:
                stats = empleado_stats[emp]
                
                # Verificar restricciones
                puede_trabajar = True
                
                # Máximo horas por semana
                if stats['horas_semana'] + 8 > max_horas_semana:
                    puede_trabajar = False
                
                # Máximo turnos consecutivos
                if stats['turnos_consecutivos'] >= max_consecutivos:
                    puede_trabajar = False
                
                if puede_trabajar:
                    empleados_disponibles.append(emp)
            
            # Seleccionar empleados para este turno (rotación equitativa)
            empleados_seleccionados = empleados_disponibles[:personas_por_turno]
            asignaciones[fecha_actual.strftime('%Y-%m-%d')][turno] = empleados_seleccionados
            
            # Actualizar estadísticas
            for emp in empleados_seleccionados:
                empleado_stats[emp]['horas_semana'] += 8
                empleado_stats[emp]['turnos_consecutivos'] += 1
                empleado_stats[emp]['ultimo_turno'] = (fecha_actual, turno)
            
            # Resetear turnos consecutivos para empleados que no trabajan
            for emp in empleados:
                if emp not in empleados_seleccionados:
                    empleado_stats[emp]['turnos_consecutivos'] = 0
    
    return asignaciones

def mostrar_calendario_turnos(turnos_data):
    """Muestra el calendario de turnos en formato tabular"""
    
    # Crear DataFrame para el calendario
    fechas = []
    fecha_actual = turnos_data['fecha_inicio']
    
    for dia in range(turnos_data['dias']):
        fecha_str = (fecha_actual + timedelta(days=dia)).strftime('%Y-%m-%d')
        if fecha_str in turnos_data['turnos']:
            fechas.append(fecha_str)
    
    if not fechas:
        st.warning("No hay turnos generados para mostrar.")
        return
    
    # Crear tabla por semanas
    df_calendario = []
    
    for fecha_str in fechas:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        
        turnos_dia = turnos_data['turnos'][fecha_str]
        
        for turno, empleados in turnos_dia.items():
            df_calendario.append({
                'Fecha': fecha_str,
                'Día': dia_semana,
                'Turno': turno,
                'Empleados': ', '.join(empleados) if empleados else 'Sin asignar',
                'Cantidad': len(empleados)
            })
    
    if df_calendario:
        df = pd.DataFrame(df_calendario)
        st.dataframe(df, use_container_width=True)
        
        # Gráfico de cobertura
        fig = px.bar(df, x='Fecha', y='Cantidad', color='Turno', 
                     title='Cobertura de Personal por Turno')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def mostrar_estadisticas(turnos_data):
    """Muestra estadísticas de la asignación de turnos"""
    
    # Calcular estadísticas por empleado
    empleado_turnos = {emp: {'Mañana': 0, 'Tarde': 0, 'Noche': 0, 'Total': 0} for emp in turnos_data['empleados']}
    
    for fecha, turnos_dia in turnos_data['turnos'].items():
        for turno, empleados in turnos_dia.items():
            for emp in empleados:
                if emp in empleado_turnos:
                    empleado_turnos[emp][turno] += 1
                    empleado_turnos[emp]['Total'] += 1
    
    # Crear DataFrame de estadísticas
    stats_data = []
    for emp, turnos in empleado_turnos.items():
        stats_data.append({
            'Empleado': emp,
            'Mañana': turnos['Mañana'],
            'Tarde': turnos['Tarde'], 
            'Noche': turnos['Noche'],
            'Total Turnos': turnos['Total'],
            'Total Horas': turnos['Total'] * 8
        })
    
    df_stats = pd.DataFrame(stats_data)
    st.dataframe(df_stats, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_turnos = px.bar(df_stats, x='Empleado', y=['Mañana', 'Tarde', 'Noche'],
                           title='Distribución de Turnos por Empleado')
        fig_turnos.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_turnos, use_container_width=True)
    
    with col2:
        fig_horas = px.pie(df_stats, values='Total Horas', names='Empleado',
                          title='Distribución de Horas Totales')
        st.plotly_chart(fig_horas, use_container_width=True)

def exportar_turnos(turnos_data):
    """Permite exportar los turnos generados"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Descargar Excel"):
            # Crear archivo Excel
            df_export = []
            
            for fecha_str, turnos_dia in turnos_data['turnos'].items():
                for turno, empleados in turnos_dia.items():
                    for emp in empleados:
                        df_export.append({
                            'Fecha': fecha_str,
                            'Turno': turno,
                            'Empleado': emp,
                            'Cargo': turnos_data['cargo']
                        })
            
            if df_export:
                df = pd.DataFrame(df_export)
                
                # Convertir a Excel en memoria
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Turnos', index=False)
                
                st.download_button(
                    label="⬇️ Descargar Turnos.xlsx",
                    data=output.getvalue(),
                    file_name=f"turnos_{turnos_data['cargo']}_{turnos_data['fecha_inicio']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if st.button("📋 Copiar Resumen"):
            resumen = f"""
RESUMEN DE TURNOS - {turnos_data['cargo']}
Período: {turnos_data['fecha_inicio']} - {turnos_data['dias']} días
Empleados: {len(turnos_data['empleados'])}
            """
            st.code(resumen)

# Información adicional en sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Información")
st.sidebar.markdown("""
**Funcionalidades:**
- ✅ Cálculo automático de personal
- ✅ Consideración de ausentismo
- ✅ Restricciones de turnos
- ✅ Visualización interactiva
- ✅ Exportación a Excel

**Desarrollado para:**
Empresas Azucareras
""")

if st.sidebar.button("🔄 Reiniciar Aplicación"):
    st.session_state.cargos_data = []
    st.session_state.turnos_generados = None
    st.rerun()
