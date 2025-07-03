import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Fantasy Fútbol", layout="wide")

# --- Crear carpeta 'data' si no existe ---
os.makedirs("data", exist_ok=True)

# --- Rutas de archivos ---
PUNTOS_PATH = "data/puntos.csv"
HISTORIAL_PATH = "data/historial.csv"
PARTICIPANTES_PATH = "data/participantes.csv"

# --- Inicializar archivos si no existen ---
if not os.path.exists(PUNTOS_PATH):
    pd.DataFrame(columns=["Jugador", "Jornada", "Puntos"]).to_csv(PUNTOS_PATH, index=False)
if not os.path.exists(HISTORIAL_PATH):
    pd.DataFrame(columns=["Temporada", "Torneo", "Ganador", "Puntos", "Posicion"]).to_csv(HISTORIAL_PATH, index=False)
if not os.path.exists(PARTICIPANTES_PATH):
    pd.DataFrame(columns=["Nombre", "Equipo", "Estado"]).to_csv(PARTICIPANTES_PATH, index=False)

# --- Cargar archivos ---
df_puntos = pd.read_csv(PUNTOS_PATH)
df_historial = pd.read_csv(HISTORIAL_PATH)
df_participantes = pd.read_csv(PARTICIPANTES_PATH)
nombres_participantes = sorted(df_participantes["Nombre"].unique())

# --- Título ---
st.title("⚽ Fantasy Fútbol - Panel de Amigos")

# --- Tabs ---
tabs = st.tabs([
    "📅 Cargar puntos", "✏️ Editar puntos", "📊 Tabla", "📈 Evolución",
    "🏆 Historial", "➕ Agregar campeón", "🏋️ Podios", "👥 Participantes"
])

# --- 📅 Cargar puntos ---
with tabs[0]:
    st.header("📅 Cargar Puntos de Jornada")
    with st.form("form_puntos"):
        jugador = st.selectbox("Selecciona jugador", nombres_participantes)
        jornada = st.number_input("Número de jornada", min_value=1, step=1)
        puntos = st.number_input("Puntos obtenidos", step=1)
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo = pd.DataFrame([{"Jugador": jugador, "Jornada": jornada, "Puntos": puntos}])
            df_puntos = pd.concat([df_puntos, nuevo], ignore_index=True)
            df_puntos.to_csv(PUNTOS_PATH, index=False)
            st.success(f"Puntos guardados para {jugador} en jornada {jornada}")

# --- ✏️ Editar puntos ---
with tabs[1]:
    st.header("✏️ Editar Puntos Existentes")
    if df_puntos.empty:
        st.info("No hay puntos cargados todavía.")
    else:
        jugador_sel = st.selectbox("Selecciona jugador", nombres_participantes)
        jornadas = sorted(df_puntos[df_puntos["Jugador"] == jugador_sel]["Jornada"].unique())
        if jornadas:
            jornada_sel = st.selectbox("Selecciona jornada", jornadas)
            current_points = df_puntos[(df_puntos["Jugador"] == jugador_sel) & (df_puntos["Jornada"] == jornada_sel)]["Puntos"].values[0]
            st.write(f"Puntos actuales: **{current_points}**")
            nuevos_puntos = st.number_input("Nuevos puntos", value=int(current_points), step=1)
            if st.button("Actualizar puntos"):
                df_puntos.loc[(df_puntos["Jugador"] == jugador_sel) & (df_puntos["Jornada"] == jornada_sel), "Puntos"] = nuevos_puntos
                df_puntos.to_csv(PUNTOS_PATH, index=False)
                st.success(f"Puntos actualizados para {jugador_sel} en jornada {jornada_sel}")

# --- 📊 Tabla de posiciones ---
with tabs[2]:
    st.header("📊 Tabla de Posiciones")
    if not df_puntos.empty:
        tabla = df_puntos.groupby("Jugador")["Puntos"].sum().sort_values(ascending=False).reset_index()
        tabla.index += 1
        st.table(tabla)
    else:
        st.info("Todavía no hay puntos cargados.")

# --- 📈 Evolución por jornada ---
with tabs[3]:
    st.header("📈 Evolución por Jornada")
    if not df_puntos.empty:
        df_evo = df_puntos.pivot_table(index="Jornada", columns="Jugador", values="Puntos", aggfunc="sum").fillna(0)
        df_evo = df_evo.cumsum().reset_index().melt(id_vars="Jornada", var_name="Jugador", value_name="Puntos acumulados")
        chart = alt.Chart(df_evo).mark_line(point=True).encode(
            x="Jornada:O", y="Puntos acumulados:Q", color="Jugador:N",
            tooltip=["Jugador", "Jornada", "Puntos acumulados"]
        ).properties(width=700, height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aún no hay datos suficientes para mostrar la gráfica.")

# --- 🏆 Historial de campeones ---
with tabs[4]:
    st.header("🏆 Historial de Ganadores")
    if not df_historial.empty:
        st.dataframe(df_historial.sort_values(["Temporada", "Posicion"]))
    else:
        st.info("No hay historial aún.")

# --- ➕ Agregar campeón ---
with tabs[5]:
    st.header("➕ Agregar Torneo al Historial")
    clave_correcta = "Cholonogana"
    with st.expander("Formulario protegido"):
        clave_ingresada = st.text_input("Ingresa la clave para editar", type="password")
        if clave_ingresada == clave_correcta:
            with st.form("form_historial"):
                temporada = st.text_input("Temporada (ej. 2024)")
                torneo = st.text_input("Nombre del Torneo")
                ganador = st.selectbox("Nombre del jugador", nombres_participantes)
                puntos = st.number_input("Puntos obtenidos", step=1)
                posicion = st.number_input("Posicion final (1 = campeón)", step=1, min_value=1)
                guardar = st.form_submit_button("Guardar")
                if guardar:
                    nueva_fila = pd.DataFrame([{"Temporada": temporada, "Torneo": torneo, "Ganador": ganador,
                                                "Puntos": puntos, "Posicion": posicion}])
                    df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                    df_historial.to_csv(HISTORIAL_PATH, index=False)
                    st.success(f"Historial actualizado: {ganador} terminó en posicion {posicion} en {temporada}")
        elif clave_ingresada:
            st.error("Clave incorrecta")

# --- 🏋️ Podios ---
with tabs[6]:
    st.header("🏋️ Podios Históricos")
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(df_historial.columns):
        top3 = df_historial[df_historial["Posicion"] <= 3].copy()
        top3["Medalla"] = top3["Posicion"].map({1: "🥇", 2: "🥈", 3: "🥉"})
        st.dataframe(top3.sort_values(by=["Temporada", "Torneo", "Posicion"]))
    else:
        st.error("El archivo historial no contiene las columnas necesarias ('Temporada', 'Torneo', 'Posicion').")

# --- 👥 Participantes ---
with tabs[7]:
    st.header("👥 Participantes")
    with st.form("form_participantes"):
        nombre = st.text_input("Nombre")
        equipo = st.text_input("Nombre del equipo")
        estado = st.selectbox("Estado", ["Activo", "Inactivo"])
        guardar = st.form_submit_button("Agregar participante")
        if guardar and nombre:
            nuevo = pd.DataFrame([{"Nombre": nombre, "Equipo": equipo, "Estado": estado}])
            df_participantes = pd.concat([df_participantes, nuevo], ignore_index=True)
            df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
            st.success(f"Participante {nombre} agregado con éxito")
    st.dataframe(df_participantes.sort_values("Nombre"))
