import streamlit as st
import pandas as pd
import random

# ==============================
# Definir estructura de semanas
# ==============================
# Semana A: 2 turnos por día (12h)
semana_a = [(12, 2)] * 7

# Semana B: 3 turnos por día (8h)
semana_b = [(8, 3)] * 7

# Semana C: 2 turnos por día (combinado 12h y 8h)
semana_c = [(12, 2), (8, 2), (12, 2), (8, 2), (12, 2), (8, 2), (12, 2)]

semanas = [semana_a, semana_b, semana_c]

# ======================================
# Función para generar la programación
# ======================================
def generar_programacion(num_empleados, nombres=None):
    if not nombres:
        nombres = [f"Empleado {i+1}" for i in range(num_empleados)]

    programacion = []
    empleado_idx = 0  # índice para repartir personal en orden

    for semana_idx, semana in enumerate(semanas, start=1):
        for dia_idx, dia in enumerate(semana, start=1):
            if isinstance(dia, tuple):
                # formato (horas_turno, cantidad_turnos)
                horas, num_turnos = dia
                for turno in range(num_turnos):
                    asignado = nombres[empleado_idx % num_empleados]
                    programacion.append([f"Semana {semana_idx}", f"Día {dia_idx}", f"{horas}h", asignado])
                    empleado_idx += 1
            elif isinstance(dia, list):  # Si es lista de varios turnos diferentes
                for horas, num_turnos in dia:
                    for turno in range(num_turnos):
                        asignado = nombres[empleado_idx % num_empleados]
                        programacion.append([f"Semana {semana_idx}", f"Día {dia_idx}", f"{horas}h", asignado])
                        empleado_idx += 1

    return pd.DataFrame(programacion, columns=["Semana", "Día", "Turno", "Empleado"])

# =========================
# Interfaz Streamlit
# =========================
st.title("📅 Generador de Programación de Turnos")
st.write("Este generador organiza turnos en semanas A, B y C con jornadas de 8h y 12h.")

# Entrada: número de empleados
num_empleados = st.number_input("Número de empleados:", min_value=1, step=1)

# Entrada: nombres de empleados
empleados_input = st.text_area("Nombres de empleados (uno por línea, opcional):")
if empleados_input:
    nombres = empleados_input.strip().split("\n")
else:
    nombres = None

# Botón para generar programación
if st.button("Generar Programación"):
    df = generar_programacion(num_empleados, nombres)
    st.dataframe(df)

    # Descargar en Excel
    st.download_button(
        label="📥 Descargar en Excel",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="programacion_turnos.csv",
        mime="text/csv",
    )
