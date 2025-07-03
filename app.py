import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Fantasy Fútbol", layout="wide")

# --- Crear carpeta 'data' si no existe ---
if not os.path.exists("data"):
    os.makedirs("data")

# --- Rutas de archivos ---
PUNTOS_PATH = "data/puntos.csv"
HISTORIAL_PATH = "data/historial.csv"

# --- Crear archivo puntos.csv si no existe ---
if not os.path.exists(PUNTOS_PATH):
    df_vacio = pd.DataFrame(columns=["Jugador", "Jornada", "Puntos"])
    df_vacio.to_csv(PUNTOS_PATH, index=False)

# --- Cargar datos existentes ---
df_puntos = pd.read_csv(PUNTOS_PATH)

# --- Título ---
st.title("⚽ Fantasy Fútbol - Panel de Amigos")

# --- Subir puntos por jornada ---
st.header("📥 Cargar Puntos de Jornada")
with st.form("form_puntos"):
    jugador = st.text_input("Nombre del jugador")
    jornada = st.number_input("Número de jornada", min_value=1, step=1)
    puntos = st.number_input("Puntos obtenidos", step=1)
    submit = st.form_submit_button("Guardar")

    if submit and jugador:
        nuevo = pd.DataFrame([{"Jugador": jugador, "Jornada": jornada, "Puntos": puntos}])
        df_puntos = pd.concat([df_puntos, nuevo], ignore_index=True)
        df_puntos.to_csv(PUNTOS_PATH, index=False)
        st.success(f"Puntos guardados para {jugador} en jornada {jornada}")

# --- Tabla de puntos acumulados ---
st.header("📊 Tabla de Posiciones")
if not df_puntos.empty:
    tabla = df_puntos.groupby("Jugador")["Puntos"].sum().sort_values(ascending=False).reset_index()
    tabla.index += 1
    st.table(tabla)
else:
    st.info("Todavía no hay puntos cargados.")

# --- Gráfico de evolución ---
st.header("📈 Evolución por Jornada")
if not df_puntos.empty:
    df_evo = df_puntos.pivot_table(index="Jornada", columns="Jugador", values="Puntos", aggfunc="sum").fillna(0)
    df_evo = df_evo.cumsum()
    df_evo = df_evo.reset_index().melt(id_vars="Jornada", var_name="Jugador", value_name="Puntos acumulados")

    chart = alt.Chart(df_evo).mark_line(point=True).encode(
        x="Jornada:O",
        y="Puntos acumulados:Q",
        color="Jugador:N",
        tooltip=["Jugador", "Jornada", "Puntos acumulados"]
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

# --- Historial de campeones ---
st.header("🏆 Historial de Ganadores")
if os.path.exists(HISTORIAL_PATH):
    historial = pd.read_csv(HISTORIAL_PATH)
    st.table(historial)
else:
    st.info("No hay historial aún. Puedes cargar uno en 'data/historial.csv'")

# --- Agregar nuevo torneo al historial ---
st.header("➕ Agregar Torneo al Historial")

# Clave protegida
clave_correcta = "Cholonogana"

with st.expander("Formulario protegido para agregar historial"):
    clave_ingresada = st.text_input("Ingresa la clave para editar", type="password")

    if clave_ingresada == clave_correcta:
        with st.form("form_historial"):
            temporada = st.text_input("Temporada (ej. 2024)")
            ganador = st.text_input("Nombre del ganador")
            puntos = st.number_input("Puntos obtenidos", step=1)
            guardar = st.form_submit_button("Guardar")

            if guardar and temporada and ganador:
                nueva_fila = pd.DataFrame([{
                    "Temporada": temporada,
                    "Ganador": ganador,
                    "Puntos": puntos
                }])

                if os.path.exists(HISTORIAL_PATH):
                    historial = pd.read_csv(HISTORIAL_PATH)
                    historial = pd.concat([historial, nueva_fila], ignore_index=True)
                else:
                    historial = nueva_fila

                historial.to_csv(HISTORIAL_PATH, index=False)
                st.success(f"Historial actualizado: {ganador} ganó en {temporada}")
    elif clave_ingresada != "":
        st.error("Clave incorrecta")
