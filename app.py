import streamlit as st
import pandas as pd
import altair as alt
import os
from github import Github

# --- Configuración inicial ---
st.set_page_config(page_title="Fantasy Fútbol", layout="wide")

# --- Rutas de archivos ---
PUNTOS_PATH = "puntos.csv"
HISTORIAL_PATH = "historial.csv"
PARTICIPANTES_PATH = "participantes.csv"

# --- Función segura para cargar CSV ---
def cargar_csv_seguro(path, columnas):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columnas)
    else:
        return pd.DataFrame(columns=columnas)

# --- Cargar archivos ---
df_puntos = cargar_csv_seguro(PUNTOS_PATH, ["Jugador", "Jornada", "Puntos"])
df_historial = cargar_csv_seguro(HISTORIAL_PATH, ["Temporada", "Torneo", "Ganador", "Puntos", "Posicion"])
df_participantes = cargar_csv_seguro(PARTICIPANTES_PATH, ["Nombre", "Equipo", "Estado", "Favorito"])
nombres_participantes = sorted(df_participantes["Nombre"].unique())

# --- Funciones para GitHub ---

def guardar_en_github(nombre_archivo, contenido_csv, mensaje_commit):
    try:
        token = st.secrets["GITHUB_TOKEN"]
    except KeyError:
        st.warning("No está configurado el token de GitHub en st.secrets. No se guardarán los cambios automáticamente.")
        return False

    repo_name = "Ozzors/futbol-fantasy"
    g = Github(token)
    repo = g.get_repo(repo_name)

    try:
        archivo = repo.get_contents(nombre_archivo)
        repo.update_file(archivo.path, mensaje_commit, contenido_csv, archivo.sha)
    except Exception:
        repo.create_file(nombre_archivo, mensaje_commit, contenido_csv)
    return True

def recargar_desde_github():
    try:
        import requests
        URL_BASE = "https://raw.githubusercontent.com/Ozzors/futbol-fantasy/main/"
        df_p = pd.read_csv(f"{URL_BASE}puntos.csv")
        df_h = pd.read_csv(f"{URL_BASE}historial.csv")
        df_pa = pd.read_csv(f"{URL_BASE}participantes.csv")

        if not df_p.empty:
            st.session_state.df_puntos = df_p
        if not df_h.empty:
            st.session_state.df_historial = df_h
        if not df_pa.empty:
            st.session_state.df_participantes = df_pa
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Error al recargar desde GitHub: {e}")

# --- Inicializar session_state para usar GitHub datos si existen ---
if "df_puntos" not in st.session_state:
    st.session_state.df_puntos = df_puntos
if "df_historial" not in st.session_state:
    st.session_state.df_historial = df_historial
if "df_participantes" not in st.session_state:
    st.session_state.df_participantes = df_participantes

# --- Título ---
st.title("⚽ Fantasy Fútbol - Panel de Amigos")

# --- Botones para guardar y actualizar en GitHub ---
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Guardar cambios en GitHub"):
        ok1 = guardar_en_github("puntos.csv", st.session_state.df_puntos.to_csv(index=False), "Guardado puntos desde app")
        ok2 = guardar_en_github("historial.csv", st.session_state.df_historial.to_csv(index=False), "Guardado historial desde app")
        ok3 = guardar_en_github("participantes.csv", st.session_state.df_participantes.to_csv(index=False), "Guardado participantes desde app")
        if ok1 and ok2 and ok3:
            st.success("Cambios guardados correctamente en GitHub.")
        else:
            st.error("Error al guardar en GitHub.")

with col2:
    if st.button("🔄 Actualizar datos desde GitHub"):
        recargar_desde_github()

# --- Tabs ---
tabs = st.tabs([
    "📅 Cargar puntos", "✏️ Editar puntos", "📊 Tabla", "📈 Evolución",
    "🏆 Historial", "➕ Agregar campeón", "📃 Editar historial", "🏋️ Podios", "👥 Participantes"
])

# --- 📅 Cargar puntos ---
with tabs[0]:
    st.header("📅 Cargar Puntos de Jornada")
    with st.form("form_puntos"):
        jugador = st.selectbox("Selecciona jugador", sorted(st.session_state.df_participantes["Nombre"].unique()))
        jornada = st.number_input("Número de jornada", min_value=1, step=1)
        puntos = st.number_input("Puntos obtenidos", step=1)
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo = pd.DataFrame([{"Jugador": jugador, "Jornada": jornada, "Puntos": puntos}])
            st.session_state.df_puntos = pd.concat([st.session_state.df_puntos, nuevo], ignore_index=True)
            st.session_state.df_puntos.to_csv(PUNTOS_PATH, index=False)
            st.success(f"Puntos guardados para {jugador} en jornada {jornada}")

# --- ✏️ Editar puntos ---
with tabs[1]:
    st.header("✏️ Editar Puntos Existentes")
    if st.session_state.df_puntos.empty:
        st.info("No hay puntos cargados todavía.")
    else:
        jugador_sel = st.selectbox("Selecciona jugador", sorted(st.session_state.df_participantes["Nombre"].unique()))
        jornadas = sorted(st.session_state.df_puntos[st.session_state.df_puntos["Jugador"] == jugador_sel]["Jornada"].unique())
        if jornadas:
            jornada_sel = st.selectbox("Selecciona jornada", jornadas)
            current_points = st.session_state.df_puntos[(st.session_state.df_puntos["Jugador"] == jugador_sel) & (st.session_state.df_puntos["Jornada"] == jornada_sel)]["Puntos"].values[0]
            st.write(f"Puntos actuales: **{current_points}**")
            nuevos_puntos = st.number_input("Nuevos puntos", value=int(current_points), step=1)
            if st.button("Actualizar puntos"):
                st.session_state.df_puntos.loc[(st.session_state.df_puntos["Jugador"] == jugador_sel) & (st.session_state.df_puntos["Jornada"] == jornada_sel), "Puntos"] = nuevos_puntos
                st.session_state.df_puntos.to_csv(PUNTOS_PATH, index=False)
                st.success(f"Puntos actualizados para {jugador_sel} en jornada {jornada_sel}")

# --- 📊 Tabla de posiciones ---
with tabs[2]:
    st.header("📊 Tabla de Posiciones")
    if not st.session_state.df_puntos.empty:
        tabla = st.session_state.df_puntos.groupby("Jugador")["Puntos"].sum().sort_values(ascending=False).reset_index()
        tabla.index += 1
        st.table(tabla)
    else:
        st.info("Todavía no hay puntos cargados.")

# --- 📈 Evolución por jornada ---
with tabs[3]:
    st.header("📈 Evolución por Jornada")
    if not st.session_state.df_puntos.empty:
        df_evo = st.session_state.df_puntos.pivot_table(index="Jornada", columns="Jugador", values="Puntos", aggfunc="sum").fillna(0)
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
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(st.session_state.df_historial.columns):
        st.dataframe(st.session_state.df_historial.sort_values(["Temporada", "Posicion"]))
    else:
        st.error("El archivo historial no contiene las columnas necesarias para mostrar el historial correctamente.")

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
                ganador = st.selectbox("Nombre del jugador", sorted(st.session_state.df_participantes["Nombre"].unique()))
                puntos = st.number_input("Puntos obtenidos", step=1)
                posicion = st.number_input("Posición final (1 = campeón)", step=1, min_value=1)
                guardar = st.form_submit_button("Guardar")
                if guardar:
                    nueva_fila = pd.DataFrame([{"Temporada": temporada, "Torneo": torneo, "Ganador": ganador,
                                                "Puntos": puntos, "Posicion": posicion}])
                    st.session_state.df_historial = pd.concat([st.session_state.df_historial, nueva_fila], ignore_index=True)
                    st.session_state.df_historial.to_csv(HISTORIAL_PATH, index=False)
                    st.success(f"Historial actualizado: {ganador} terminó en posición {posicion} en {temporada}")
        elif clave_ingresada:
            st.error("Clave incorrecta")

# --- 📃 Editar historial ---
with tabs[6]:
    st.header("📃 Editar datos del Historial")
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(st.session_state.df_historial.columns) and not st.session_state.df_historial.empty:
        fila_idx = st.selectbox("Selecciona el torneo a editar", st.session_state.df_historial.index)
        fila = st.session_state.df_historial.loc[fila_idx]
        with st.form("form_editar_historial"):
            temporada = st.text_input("Temporada", value=fila["Temporada"])
            torneo = st.text_input("Torneo", value=fila["Torneo"])
            ganador = st.selectbox("Ganador", sorted(st.session_state.df_participantes["Nombre"].unique()), index=sorted(st.session_state.df_participantes["Nombre"].unique()).index(fila["Ganador"]))
            puntos = st.number_input("Puntos", value=int(fila["Puntos"]))
            posicion = st.number_input("Posición", value=int(fila["Posicion"]), step=1, min_value=1)
            actualizar = st.form_submit_button("Actualizar historial")
            if actualizar:
                st.session_state.df_historial.loc[fila_idx] = [temporada, torneo, ganador, puntos, posicion]
                st.session_state.df_historial.to_csv(HISTORIAL_PATH, index=False)
                st.success("Registro actualizado correctamente.")
    else:
        st.warning("El historial está vacío o no tiene las columnas necesarias (Temporada, Torneo, Ganador, Puntos, Posicion).")

# --- 🏋️ Podios ---
with tabs[7]:
    st.header("🏋️ Podios Históricos")
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(st.session_state.df_historial.columns):
        top3 = st.session_state.df_historial[st.session_state.df_historial["Posicion"] <= 3].copy()
        top3["Medalla"] = top3["Posicion"].map({1: "🥇", 2: "🥈", 3: "🥉"})
        st.dataframe(top3.sort_values(by=["Temporada", "Torneo", "Posicion"]))
    else:
        st.error("El archivo historial no contiene las columnas necesarias ('Temporada', 'Torneo', 'Posicion').")

# --- 👥 Participantes ---
with tabs[8]:
    st.header("👥 Participantes")
    with st.form("form_participantes"):
        nombre = st.text_input("Nombre")
        equipo = st.text_input("Nombre del equipo")
        favorito = st.text_input("Equipo favorito")
        estado = st.selectbox("Estado", ["Activo", "Inactivo"])
        guardar = st.form_submit_button("Agregar participante")
        if guardar and nombre:
            nuevo = pd.DataFrame([{"Nombre": nombre, "Equipo": equipo, "Estado": estado, "Favorito": favorito}])
            st.session_state.df_participantes = pd.concat([st.session_state.df_participantes, nuevo], ignore_index=True)
            st.session_state.df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
            st.success(f"Participante {nombre} agregado con éxito")

    st.dataframe(st.session_state.df_participantes.sort_values("Nombre"))

    st.subheader("🔄 Editar Participante")
    if not st.session_state.df_participantes.empty:
        seleccion = st.selectbox("Selecciona participante", st.session_state.df_participantes.index)
        fila = st.session_state.df_participantes.loc[seleccion]
        with st.form("form_editar_participante"):
            nuevo_nombre = st.text_input("Nombre", value=fila.get("Nombre", ""))
            nuevo_equipo = st.text_input("Equipo", value=fila.get("Equipo", ""))
            nuevo_favorito = st.text_input("Equipo favorito", value=fila.get("Favorito", ""))
            nuevo_estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(fila.get("Estado", "Activo")))
            actualizar = st.form_submit_button("Actualizar")
            eliminar = st.form_submit_button("Eliminar")
            if actualizar:
                st.session_state.df_participantes.loc[seleccion] = [nuevo_nombre, nuevo_equipo, nuevo_estado, nuevo_favorito]
                st.session_state.df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
                st.success("Participante actualizado.")
            if eliminar:
                st.session_state.df_participantes = st.session_state.df_participantes.drop(index=seleccion).reset_index(drop=True)
                st.session_state.df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
                st.success("Participante eliminado.")
