import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import math
import io

# === FUNCIONES AUXILIARES ===
def generar_turnos_optimizado(cargo_data, empleados, fecha_inicio, dias, max_consecutivos, min_descanso, max_horas_semana, weekend_work, rotacion_equitativa):
    """Genera turnos optimizados considerando restricciones"""
    
    turnos_activos = []
    if cargo_data['turnos_activos'][0]: turnos_activos.append('Mañana')
    if cargo_data['turnos_activos'][1]: turnos_activos.append('Tarde')
    if cargo_data['turnos_activos'][2]: turnos_activos.append('Noche')
    
    personas_por_turno = cargo_data['personas_por_turno']
    
    # Estructura para almacenar asignaciones
    asignaciones = {}
    empleado_stats = {emp: {
        'turnos_consecutivos': 0, 
        'horas_semana': 0, 
        'ultimo_turno_fecha': None,
        'ultimo_turno_tipo': None,
        'total_turnos': 0,
        'turnos_por_tipo': {'Mañana': 0, 'Tarde': 0, 'Noche': 0}
    } for emp in empleados}
    
    # Índice para rotación equitativa
    indice_rotacion = 0
    
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
                puede_trabajar = True
                
                if stats['horas_semana'] + 8 > max_horas_semana:
                    puede_trabajar = False
                if stats['turnos_consecutivos'] >= max_consecutivos:
                    puede_trabajar = False
                if stats['ultimo_turno_fecha']:
                    horas_desde_ultimo = (fecha_actual - stats['ultimo_turno_fecha']).total_seconds() / 3600
                    if horas_desde_ultimo < min_descanso:
                        puede_trabajar = False
                
                if puede_trabajar:
                    empleados_disponibles.append(emp)
            
            if rotacion_equitativa:
                empleados_disponibles.sort(key=lambda x: (
                    empleado_stats[x]['turnos_por_tipo'][turno], 
                    empleado_stats[x]['total_turnos']
                ))
            else:
                empleados_disponibles = empleados_disponibles[indice_rotacion:] + empleados_disponibles[:indice_rotacion]
                indice_rotacion = (indice_rotacion + 1) % len(empleados) if empleados else 0
            
            empleados_seleccionados = empleados_disponibles[:personas_por_turno]
            asignaciones[fecha_actual.strftime('%Y-%m-%d')][turno] = empleados_seleccionados
            
            for emp in empleados_seleccionados:
                empleado_stats[emp]['horas_semana'] += 8
                empleado_stats[emp]['turnos_consecutivos'] += 1
                empleado_stats[emp]['ultimo_turno_fecha'] = fecha_actual
                empleado_stats[emp]['ultimo_turno_tipo'] = turno
                empleado_stats[emp]['total_turnos'] += 1
                empleado_stats[emp]['turnos_por_tipo'][turno] += 1
            
            for emp in empleados:
                if emp not in empleados_seleccionados:
                    empleado_stats[emp]['turnos_consecutivos'] = 0
    
    return asignaciones


def mostrar_calendario_turnos(turnos_data):
    """Muestra el calendario de turnos en formato tabular"""
    fechas = []
    fecha_actual = turnos_data['fecha_inicio']
    for dia in range(turnos_data['dias']):
        fecha_str = (fecha_actual + timedelta(days=dia)).strftime('%Y-%m-%d')
        if fecha_str in turnos_data['turnos']:
            fechas.append(fecha_str)
    if not fechas:
        st.warning("No hay turnos generados para mostrar.")
        return
    df_calendario = []
    for fecha_str in fechas:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        dia_semana_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }.get(dia_semana, dia_semana)
        turnos_dia = turnos_data['turnos'][fecha_str]
        for turno, empleados in turnos_dia.items():
            df_calendario.append({
                'Fecha': fecha_str,
                'Día': dia_semana_es,
                'Turno': turno,
                'Empleados': ', '.join(empleados) if empleados else 'Sin asignar',
                'Cantidad': len(empleados)
            })
    if df_calendario:
        df = pd.DataFrame(df_calendario)
        st.dataframe(df, use_container_width=True)
        st.subheader("📈 Análisis de Cobertura")
        cobertura_por_turno = df.groupby('Turno')['Cantidad'].agg(['mean', 'min', 'max']).round(1)
        cols = st.columns(len(cobertura_por_turno))
        for i, (turno, stats) in enumerate(cobertura_por_turno.iterrows()):
            with cols[i]:
                st.metric(f"Turno {turno}", f"Prom: {stats['mean']}", f"Min: {stats['min']} | Max: {stats['max']}")


def mostrar_estadisticas(turnos_data):
    """Muestra estadísticas de la asignación de turnos"""
    empleado_turnos = {emp: {'Mañana': 0, 'Tarde': 0, 'Noche': 0, 'Total': 0} for emp in turnos_data['empleados']}
    for fecha, turnos_dia in turnos_data['turnos'].items():
        for turno, empleados in turnos_dia.items():
            for emp in empleados:
                if emp in empleado_turnos:
                    empleado_turnos[emp][turno] += 1
                    empleado_turnos[emp]['Total'] += 1
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
    st.subheader("📊 Resumen Estadístico")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Promedio Turnos/Empleado", f"{df_stats['Total Turnos'].mean():.1f}")
        st.metric("Empleado con Más Turnos", f"{df_stats['Total Turnos'].max()}")
        st.metric("Empleado con Menos Turnos", f"{df_stats['Total Turnos'].min()}")
    with col2:
        st.metric("Total Turnos Mañana", df_stats['Mañana'].sum())
        st.metric("Total Turnos Tarde", df_stats['Tarde'].sum())
        st.metric("Total Turnos Noche", df_stats['Noche'].sum())
    with col3:
        st.metric("Promedio Horas/Empleado", f"{df_stats['Total Horas'].mean():.1f}")
        st.metric("Total Horas Asignadas", df_stats['Total Horas'].sum())
        desviacion = df_stats['Total Turnos'].std()
        st.metric("Equidad (Desv. Std.)", f"{desviacion:.2f}")
    st.subheader("⚖️ Balance de Carga")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**🔴 Empleados con Mayor Carga:**")
        top_carga = df_stats.nlargest(3, 'Total Turnos')[['Empleado', 'Total Turnos', 'Total Horas']]
        st.dataframe(top_carga, use_container_width=True, hide_index=True)
    with col2:
        st.write("**🟢 Empleados con Menor Carga:**")
        min_carga = df_stats.nsmallest(3, 'Total Turnos')[['Empleado', 'Total Turnos', 'Total Horas']]
        st.dataframe(min_carga, use_container_width=True, hide_index=True)


def exportar_turnos(turnos_data):
    """Permite exportar los turnos generados"""
    df_export = []
    for fecha_str, turnos_dia in turnos_data['turnos'].items():
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        dia_semana_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }.get(dia_semana, dia_semana)
        for turno, empleados in turnos_dia.items():
            if empleados:
                for emp in empleados:
                    df_export.append({
                        'Fecha': fecha_str,
                        'Día': dia_semana_es,
                        'Turno': turno,
                        'Empleado': emp,
                        'Cargo': turnos_data['cargo'],
                        'Horas': 8
                    })
    if df_export:
        df = pd.DataFrame(df_export)
        st.subheader("👀 Vista Previa del Archivo")
        st.dataframe(df.head(10), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Descargar CSV",
                data=csv,
                file_name=f"turnos_{turnos_data['cargo']}_{turnos_data['fecha_inicio']}.csv",
                mime="text/csv"
            )
        with col2:
            resumen = f"""RESUMEN DE TURNOS - {turnos_data['cargo']}
================================
Período: {turnos_data['fecha_inicio']} ({turnos_data['dias']} días)
Empleados: {len(turnos_data['empleados'])}
Total Asignaciones: {len(df)}
Total Horas: {len(df) * 8}

PARÁMETROS UTILIZADOS:
- Máx. Turnos Consecutivos: {turnos_data['parametros']['max_consecutivos']}
- Mín. Horas Descanso: {turnos_data['parametros']['min_descanso']}
- Máx. Horas/Semana: {turnos_data['parametros']['max_horas_semana']}
- Trabajo Fines de Semana: {'Sí' if turnos_data['parametros']['weekend_work'] else 'No'}
"""
            st.download_button(
                label="📄 Descargar Resumen",
                data=resumen,
                file_name=f"resumen_turnos_{turnos_data['cargo']}.txt",
                mime="text/plain"
            )
        st.subheader("📈 Estadísticas del Archivo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Registros", len(df))
        with col2:
            st.metric("Fechas Cubiertas", df['Fecha'].nunique())
        with col3:
            st.metric("Total Horas", len(df) * 8)

# === APP PRINCIPAL ===
# (Aquí va todo tu código original de secciones 1, 2, 3 sin cambios, ya que ahora las funciones están definidas arriba)
# ...
