import streamlit as st
import pandas as pd
import altair as alt
import os
from github import Github

# --- Configuración inicial ---
st.set_page_config(page_title="Fantasy Fútbol", layout="wide")

# --- Rutas de archivos (sin carpeta 'data/') ---
PUNTOS_PATH = "puntos.csv"
HISTORIAL_PATH = "historial.csv"
PARTICIPANTES_PATH = "participantes.csv"

# --- Inicializar archivos si no existen ---
if not os.path.exists(PUNTOS_PATH):
    pd.DataFrame(columns=["Jugador", "Jornada", "Puntos"]).to_csv(PUNTOS_PATH, index=False)
if not os.path.exists(HISTORIAL_PATH):
    pd.DataFrame(columns=["Temporada", "Torneo", "Ganador", "Puntos", "Posicion"]).to_csv(HISTORIAL_PATH, index=False)
if not os.path.exists(PARTICIPANTES_PATH):
    pd.DataFrame(columns=["Nombre", "Equipo", "Estado", "Favorito"]).to_csv(PARTICIPANTES_PATH, index=False)

# --- Cargar archivos ---
df_puntos = pd.read_csv(PUNTOS_PATH)
df_historial = pd.read_csv(HISTORIAL_PATH)
df_participantes = pd.read_csv(PARTICIPANTES_PATH)
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
        repo_url = "https://raw.githubusercontent.com/Ozzors/futbol-fantasy/main/"
        puntos_url = repo_url + "puntos.csv"
        historial_url = repo_url + "historial.csv"
        participantes_url = repo_url + "participantes.csv"

        df_puntos_new = pd.read_csv(puntos_url)
        df_historial_new = pd.read_csv(historial_url)
        df_participantes_new = pd.read_csv(participantes_url)

        return df_puntos_new, df_historial_new, df_participantes_new
    except Exception as e:
        st.error(f"Error al cargar datos desde GitHub: {e}")
        return None, None, None

# --- Botones para guardar y actualizar en GitHub ---
col1, col2 = st.columns([1,1])
with col1:
    if st.button("💾 Guardar datos en GitHub"):
        ok1 = guardar_en_github("puntos.csv", df_puntos.to_csv(index=False), "Guardar puntos desde app")
        ok2 = guardar_en_github("historial.csv", df_historial.to_csv(index=False), "Guardar historial desde app")
        ok3 = guardar_en_github("participantes.csv", df_participantes.to_csv(index=False), "Guardar participantes desde app")
        if ok1 and ok2 and ok3:
            st.success("Datos guardados correctamente en GitHub.")
        else:
            st.error("Error al guardar algunos archivos en GitHub.")

with col2:
    if st.button("🔄 Actualizar datos desde GitHub"):
        puntos_new, historial_new, participantes_new = recargar_desde_github()
        if puntos_new is not None:
            df_puntos = puntos_new
            df_historial = historial_new
            df_participantes = participantes_new
            nombres_participantes = sorted(df_participantes["Nombre"].unique())

            # Guardar localmente para mantener consistencia
            df_puntos.to_csv(PUNTOS_PATH, index=False)
            df_historial.to_csv(HISTORIAL_PATH, index=False)
            df_participantes.to_csv(PARTICIPANTES_PATH, index=False)

            st.experimental_rerun()

# --- Título ---
st.title("⚽ Fantasy Fútbol - Panel de Amigos")

# --- Tabs ---
tabs = st.tabs([
    "📅 Cargar puntos", "✏️ Editar puntos", "📊 Tabla", "📈 Evolución",
    "🏆 Historial", "➕ Agregar campeón", "📃 Editar historial", "🏋️ Podios", "👥 Participantes"
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
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(df_historial.columns):
        st.dataframe(df_historial.sort_values(["Temporada", "Posicion"]))
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
                ganador = st.selectbox("Nombre del jugador", nombres_participantes)
                puntos = st.number_input("Puntos obtenidos", step=1)
                posicion = st.number_input("Posicion final (1 = campeón)", step=1, min_value=1)
                guardar = st.form_submit_button("Guardar")
                if guardar:
                    nueva_fila = pd.DataFrame([{"Temporada": temporada, "Torneo": torneo, "Ganador": ganador,
                                                "Puntos": puntos, "Posicion": posicion}])
                    df_historial = pd.concat([df_historial, nueva_fila], ignore_index=True)
                    df_historial.to_csv(HISTORIAL_PATH, index=False)
                    st.success(f"Historial actualizado: {ganador} terminó en posición {posicion} en {temporada}")
        elif clave_ingresada:
            st.error("Clave incorrecta")

# --- 📃 Editar historial ---
with tabs[6]:
    st.header("📃 Editar datos del Historial")
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(df_historial.columns) and not df_historial.empty:
        fila_idx = st.selectbox("Selecciona el torneo a editar", df_historial.index)
        fila = df_historial.loc[fila_idx]
        with st.form("form_editar_historial"):
            temporada = st.text_input("Temporada", value=fila["Temporada"])
            torneo = st.text_input("Torneo", value=fila["Torneo"])
            ganador = st.selectbox("Ganador", nombres_participantes, index=nombres_participantes.index(fila["Ganador"]))
            puntos = st.number_input("Puntos", value=int(fila["Puntos"]))
            posicion = st.number_input("Posicion", value=int(fila["Posicion"]), step=1, min_value=1)
            actualizar = st.form_submit_button("Actualizar historial")
            if actualizar:
                df_historial.loc[fila_idx] = [temporada, torneo, ganador, puntos, posicion]
                df_historial.to_csv(HISTORIAL_PATH, index=False)
                st.success("Registro actualizado correctamente.")
    else:
        st.warning("El historial está vacío o no tiene las columnas necesarias (Temporada, Torneo, Ganador, Puntos, Posicion).")

# --- 🏋️ Podios ---
with tabs[7]:
    st.header("🏋️ Podios Históricos")
    columnas_necesarias = {"Temporada", "Torneo", "Ganador", "Puntos", "Posicion"}
    if columnas_necesarias.issubset(df_historial.columns):
        top3 = df_historial[df_historial["Posicion"] <= 3].copy()
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
            df_participantes = pd.concat([df_participantes, nuevo], ignore_index=True)
            df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
            st.success(f"Participante {nombre} agregado con éxito")

    st.dataframe(df_participantes.sort_values("Nombre"))

    st.subheader("🔄 Editar Participante")
    if not df_participantes.empty:
        seleccion = st.selectbox("Selecciona participante", df_participantes.index)
        fila = df_participantes.loc[seleccion]
        with st.form("form_editar_participante"):
            nuevo_nombre = st.text_input("Nombre", value=fila.get("Nombre", ""))
            nuevo_equipo = st.text_input("Equipo", value=fila.get("Equipo", ""))
            nuevo_favorito = st.text_input("Equipo favorito", value=fila.get("Favorito", ""))
            nuevo_estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(fila.get("Estado", "Activo")))
            actualizar = st.form_submit_button("Actualizar")
            eliminar = st.form_submit_button("Eliminar")
            if actualizar:
                df_participantes.loc[seleccion] = [nuevo_nombre, nuevo_equipo, nuevo_estado, nuevo_favorito]
                df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
                st.success("Participante actualizado.")
            if eliminar:
                df_participantes = df_participantes.drop(index=seleccion).reset_index(drop=True)
                df_participantes.to_csv(PARTICIPANTES_PATH, index=False)
                st.success("Participante eliminado.")
