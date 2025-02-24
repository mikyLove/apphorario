import streamlit as st
import pandas as pd
import numpy as np

st.title("Optimizador de Horarios Académicos")
st.markdown("""
**Objetivo:** Automatizar la generación de horarios académicos, 
teniendo en cuenta restricciones de disponibilidad, infraestructura y normativas internas.
""")

st.sidebar.header("Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo Excel (formato .xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cargar la hoja 'ANEXO 09'
        df = pd.read_excel(uploaded_file, sheet_name="ANEXO 09")
        st.subheader("Datos Cargados (primeras filas)")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
    
    # Procesar los datos para extraer la información de cada curso
    st.subheader("Procesamiento de Datos")
    # Se asume que las columnas importantes son: 
    # "CODIGO DEL CURSO", "NOMBRE DEL CURSO", "CICLO (2)", "TIPO CURSO (3)", 
    # "GRUPO (4)", "TURNO (5)", "NUMERO AULA", "HORAS", "APELLIDOS Y NOMBRESDEL DOCENTE"
    courses = []
    for index, row in df.iterrows():
        # Consideramos solo filas que tengan un código de curso definido
        if pd.isna(row["CODIGO DEL CURSO"]):
            continue
        course = {
            "codigo": row["CODIGO DEL CURSO"],
            "nombre": row["NOMBRE DEL CURSO"],
            "ciclo": row["CICLO (2)"],
            "tipo": row["TIPO CURSO (3)"],
            "grupo": row["GRUPO (4)"],
            "turno": row["TURNO (5)"].strip() if isinstance(row["TURNO (5)"], str) else "M",
            "aula": row["NUMERO AULA"],
            "horas": int(row["HORAS"]) if not pd.isna(row["HORAS"]) else 0,
            "docente": row["APELLIDOS Y NOMBRESDEL DOCENTE"] if "APELLIDOS Y NOMBRESDEL DOCENTE" in row else None,
        }
        courses.append(course)
    
    st.write("Cursos a programar:")
    st.write(courses)

    # Definir la estructura de turnos y días
    st.subheader("Generación del Horario")
    # Días laborales
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    # Definir turnos: "M" para mañana (7:00-13:00) y "T" para tarde (13:00-19:00)
    shifts = {
        "M": {"start": 7, "end": 13, "duracion": 6},  # 6 horas disponibles
        "T": {"start": 13, "end": 19, "duracion": 6}   # 6 horas disponibles
    }
    
    # Crear una estructura de horario: para cada día y turno, se crean bloques de 1 hora (lista de 6 elementos)
    schedule = {day: {"M": [None]*shifts["M"]["duracion"], "T": [None]*shifts["T"]["duracion"]} for day in days}
    
    conflict_alerts = []

    # Algoritmo simple: asignar a cada curso un bloque de tiempo consecutivo en el turno designado,
    # buscando en cada día un bloque libre de la duración requerida.
    for course in courses:
        required_hours = course["horas"]
        turno = course["turno"]
        assigned = False
        
        # Buscar en cada día la posibilidad de asignar los bloques requeridos
        for day in days:
            slots = schedule[day][turno]
            count = 0
            start_index = 0
            for i in range(len(slots)):
                if slots[i] is None:
                    if count == 0:
                        start_index = i
                    count += 1
                    if count == required_hours:
                        # Asignar el curso a estos bloques
                        for j in range(start_index, start_index + required_hours):
                            slots[j] = course["codigo"]
                        assigned = True
                        break
                else:
                    count = 0  # Reiniciar si se encuentra un bloque ocupado
            if assigned:
                break
        if not assigned:
            conflict_alerts.append(f"No se pudo asignar el curso {course['codigo']} - {course['nombre']} (requiere {required_hours} hora(s) en turno {turno}).")
    
    st.subheader("Horario Generado")
    # Crear una tabla para visualizar el horario: cada día y turno se muestra con sus bloques horarios
    schedule_data = []
    for day in days:
        row = {"Día": day}
        for turno_key in ["M", "T"]:
            shift_slots = schedule[day][turno_key]
            start_hour = shifts[turno_key]["start"]
            slot_info = []
            for i, course_code in enumerate(shift_slots):
                time_slot = f"{start_hour + i}:00-{start_hour + i + 1}:00"
                slot_info.append(f"{time_slot}: {course_code if course_code is not None else '-'}")
            row[f"Turno {turno_key}"] = "\n".join(slot_info)
        schedule_data.append(row)
    
    schedule_df = pd.DataFrame(schedule_data)
    st.dataframe(schedule_df)

    # Mostrar alertas de conflictos, si existen
    if conflict_alerts:
        st.error("Conflictos detectados:")
        for alert in conflict_alerts:
            st.error(alert)
    else:
        st.success("Todos los cursos se asignaron correctamente.")

    # Botón para exportar el horario generado a un archivo Excel
    if st.button("Exportar Horario a Excel"):
        output_file = "horario_generado.xlsx"
        try:
            schedule_df.to_excel(output_file, index=False)
            st.success(f"Horario exportado exitosamente como {output_file}.")
        except Exception as e:
            st.error(f"Error al exportar: {e}")
else:
    st.info("Por favor, sube el archivo Excel para comenzar.")
