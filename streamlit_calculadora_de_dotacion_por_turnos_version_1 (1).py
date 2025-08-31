import streamlit as st
import math
import pandas as pd

# Título de la aplicación
st.title("Calculadora de Personal y Programación de Turnos")
st.write("Ingrese los parámetros a continuación para calcular el personal necesario y generar la programación de turnos.")

# --- Sección de Parámetros de Entrada ---
st.header("Parámetros de la Programación")

# Campos de entrada de texto para el cargo
cargo = st.text_input("Cargo del personal (ej: Operador de Máquina)", "Operador")

# Campos de entrada numéricos con valores mínimos y máximos
personal_actual = st.number_input("Cantidad de personal actual en el cargo", min_value=0, value=1)
ausentismo_porcentaje = st.number_input("Porcentaje de ausentismo (%)", min_value=0.0, max_value=100.0, value=5.0)
dias_a_cubrir = st.number_input("Días a cubrir por semana", min_value=1, max_value=7, value=7)
horas_promedio_semanal = st.number_input("Horas promedio semanales por operador (últimas 3 semanas)", min_value=1, value=42)
personal_vacaciones = st.number_input("Personal de vacaciones en el período de programación", min_value=0, value=0)
operadores_por_turno = st.number_input("Cantidad de operadores requeridos por turno", min_value=1, value=1)

# Selección de turnos y validación de horas por turno
st.subheader("Configuración de Turnos")
cantidad_turnos = st.selectbox("Cantidad de turnos", [2, 3], index=1)
if cantidad_turnos == 3:
    horas_por_turno = 8
    st.write("Horas por turno (automático): 8 horas (para 3 turnos)")
else:
    horas_por_turno = 12
    st.write("Horas por turno (automático): 12 horas (para 2 turnos)")

# --- Botón para Iniciar el Cálculo ---
if st.button("Calcular Personal Necesario y Turnos"):
    try:
        # Validación de valores para evitar errores de cálculo
        if personal_actual <= 0 or dias_a_cubrir <= 0 or horas_promedio_semanal <= 0 or operadores_por_turno <= 0:
            st.error("Por favor, ingrese valores válidos mayores a cero.")
        else:
            # --- Lógica de Cálculo ---
            
            # 1. Calcular las horas de trabajo totales requeridas por semana
            horas_operacion_diarias = cantidad_turnos * horas_por_turno
            horas_trabajo_totales_semanales = dias_a_cubrir * horas_operacion_diarias * operadores_por_turno
            
            # 2. Calcular el personal teórico necesario (sin ausentismo/vacaciones)
            personal_teorico = horas_trabajo_totales_semanales / horas_promedio_semanal
            
            # 3. Ajustar el personal por ausentismo
            factor_ausentismo = 1 - (ausentismo_porcentaje / 100)
            if factor_ausentismo <= 0:
                 st.error("El porcentaje de ausentismo no puede ser 100% o más. Por favor, ajuste el valor.")
            else:
                personal_ajustado_ausentismo = personal_teorico / factor_ausentismo
                
                # 4. Sumar el personal de vacaciones
                personal_final_necesario = round(personal_ajustado_ausentismo + personal_vacaciones)
                
                # 5. Calcular la brecha de personal (si la hay)
                diferencia_personal = personal_final_necesario - personal_actual
                
                # Validar que el personal necesario sea suficiente para cubrir los turnos
                if personal_final_necesario < operadores_por_turno * cantidad_turnos:
                    st.error(f"Error: El personal requerido ({personal_final_necesario}) no es suficiente para cubrir los {operadores_por_turno} operadores por turno en {cantidad_turnos} turnos.")
                else:
                    # --- Sección de Resultados ---
                    st.header("Resultados del Cálculo")
                    
                    # Usamos una columna para los resultados y otra para la explicación
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Personal Requerido para no generar horas extras", value=f"{personal_final_necesario} persona(s)")
                        st.metric(label=f"Horas de trabajo totales requeridas a la semana para {cargo}", value=f"{horas_trabajo_totales_semanales} horas")
                    with col2:
                        st.markdown("---")
                        st.markdown("**Cómo se calcula el personal requerido:**")
                        st.markdown(f"1. **Horas totales:** `{dias_a_cubrir} (días) * {horas_operacion_diarias} (horas/día) * {operadores_por_turno} (op/turno) = {horas_trabajo_totales_semanales} (horas totales)`")
                        st.markdown(f"2. **Personal teórico:** `{horas_trabajo_totales_semanales} (horas totales) / {horas_promedio_semanal} (horas/op) = {personal_teorico:.2f} (personal teórico)`")
                        st.markdown(f"3. **Ajuste:** `({personal_teorico:.2f} / (1 - {ausentismo_porcentaje}/100)) + {personal_vacaciones} (vacaciones)`")
                        st.markdown(f"4. **Resultado final:** `{round(personal_ajustado_ausentismo + personal_vacaciones)} (personal redondeado)`")
                        st.markdown("---")
                    
                    # Mostrar la brecha de personal
                    if diferencia_personal > 0:
                        st.warning(f"Se necesitan **{diferencia_personal}** personas adicionales para cubrir la operación.")
                    elif diferencia_personal < 0:
                        st.info(f"Tienes **{abs(diferencia_personal)}** personas de más, lo que podría reducir costos o permitir más personal de reserva.")
                    else:
                        st.success("¡El personal actual es el ideal para esta operación!")
                    
                    # --- Programación de Turnos Sugerida con Descanso Rotativo y Balance de Horas ---
                    st.header("Programación de Turnos Sugerida (basada en el personal requerido)")
                    
                    turnos_horarios = []
                    if cantidad_turnos == 3:
                        turnos_horarios = ["06:00 - 14:00", "14:00 - 22:00", "22:00 - 06:00"]
                    else:
                        turnos_horarios = ["06:00 - 18:00", "18:00 - 06:00"]
                    
                    # Definir el número de días a programar (tres semanas)
                    dias_a_programar = dias_a_cubrir * 3
                    dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    columnas_dias = [f"{dias_semana_nombres[d % 7]} Sem{d // 7 + 1}" for d in range(dias_a_programar)]

                    # Horas totales a cumplir por cada operador (objetivo)
                    # El objetivo se ajusta para ser un múltiplo de las horas de turno, lo más cercano a 42h/semana.
                    target_total_hours = horas_promedio_semanal * 3
                    num_turnos_por_operador_total = math.floor(target_total_hours / horas_por_turno)
                    horas_totales_por_operador = num_turnos_por_operador_total * horas_por_turno

                    # Se informa al usuario sobre el ajuste de horas
                    st.info(f"El objetivo de horas total por operador se ha ajustado a {horas_totales_por_operador} ({horas_totales_por_operador/3:.2f} promedio semanal) para un balance preciso con turnos de {horas_por_turno} horas.")

                    # Inicializar un diccionario para llevar el seguimiento de las horas trabajadas por operador
                    horas_trabajadas_por_operador = {op_idx: 0 for op_idx in range(personal_final_necesario)}
                    
                    # Distribuir el personal en las tablas de forma secuencial
                    base_empleados_por_turno = personal_final_necesario // cantidad_turnos
                    resto_empleados = personal_final_necesario % cantidad_turnos

                    start_index_global = 0
                    for i in range(cantidad_turnos):
                        # Determinar el número de empleados para esta tabla/turno
                        num_empleados_este_turno = base_empleados_por_turno + (1 if i < resto_empleados else 0)
                        end_index_global = start_index_global + num_empleados_este_turno

                        st.subheader(f"Tabla Turno {i + 1}: {turnos_horarios[i]}")
                        
                        # Crear el DataFrame para esta tabla
                        data = {'Operador': [f"{cargo} {op_idx + 1}" for op_idx in range(start_index_global, end_index_global)]}
                        df_turno = pd.DataFrame(data)
                        
                        # Llenar las columnas de los días con la rotación de turnos y descansos
                        for dia in range(dias_a_programar):
                            columna = columnas_dias[dia]
                            dia_programacion = []
                            
                            num_trabajando = operadores_por_turno
                            num_descansando = num_empleados_este_turno - num_trabajando
                            
                            indices_descanso = []
                            if num_descansando > 0:
                                start_descanso_idx = (dia * num_descansando) % num_empleados_este_turno
                                for k in range(num_descansando):
                                    indices_descanso.append((start_descanso_idx + k) % num_empleados_este_turno)

                            # Asignar rotación de turnos entre semanas
                            turno_base_idx = i
                            semana = dia // dias_a_cubrir
                            if cantidad_turnos == 3:
                                turno_base_idx = (i + semana) % 3
                            else:
                                turno_base_idx = (i + semana) % 2
                                
                            for j in range(num_empleados_este_turno):
                                global_op_idx = start_index_global + j
                                
                                if horas_trabajadas_por_operador.get(global_op_idx, 0) >= horas_totales_por_operador:
                                    dia_programacion.append("Descanso")
                                else:
                                    if j in indices_descanso:
                                        dia_programacion.append("Descanso")
                                    else:
                                        dia_programacion.append(f"Turno {turno_base_idx + 1}")
                                        horas_trabajadas_por_operador[global_op_idx] = horas_trabajadas_por_operador.get(global_op_idx, 0) + horas_por_turno
                            
                            df_turno[columna] = dia_programacion

                        # Añadir columnas de total de horas y promedio semanal
                        total_horas = [horas_trabajadas_por_operador.get(op_idx, 0) for op_idx in range(start_index_global, end_index_global)]
                        promedio_semanal = [h / 3 for h in total_horas]

                        df_turno['Total Horas'] = total_horas
                        df_turno['Promedio Semanal'] = [f"{ps:.2f}" for ps in promedio_semanal]

                        st.dataframe(df_turno, hide_index=True, use_container_width=True)

                        start_index_global = end_index_global
                    

    except Exception as e:
        st.error(f"Ha ocurrido un error en el cálculo. Por favor, revise los valores ingresados. Error: {e}")
