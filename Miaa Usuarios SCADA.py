import pandas as pd
import sqlalchemy
import streamlit as st


# Función de conexión utilizando la URL directa de los secretos
def get_connection():
  secrets = st.secrets

  if "databases" not in secrets or "url_dic" not in secrets["databases"]:
    st.error(
        "🚨 Error crítico: No se encontró la sección [databases] o la llave"
        " 'url_dic' en los secretos de Streamlit."
    )
    st.stop()

  db_url = secrets["databases"]["url_dic"]
  engine = sqlalchemy.create_engine(db_url)
  return engine


st.title("👥 Gestión de Usuarios del Sistema")
st.markdown(
    "Administra las credenciales, tipos de usuario y departamentos de la base"
    " de datos `miaamx_telemetria2` (tabla `usuarios`)."
)

# Pestañas principales
tab_lista, tab_crear = st.tabs(["📋 Lista de Usuarios", "➕ Nuevo Usuario"])

# -------------------------------------------------------------------------
# 1. LISTA DE USUARIOS (Diseño personalizado por filas)
# -------------------------------------------------------------------------
with tab_lista:
  st.subheader("Usuarios Registrados")
  try:
    engine = get_connection()
    df_usuarios = pd.read_sql(
        "SELECT id, usuario, tipo_usuario, departamento FROM usuarios", engine
    )

    if not df_usuarios.empty:
      for _, row in df_usuarios.iterrows():
        # Contenedor visual para simular la tarjeta de cada usuario
        with st.container():
          cols = st.columns([2.5, 2, 2, 1, 1])

          with cols[0]:
            st.markdown(f"👤 **{row['usuario']}**")

          with cols[1]:
            st.markdown(f"💬 ID: `{row['id']}`")

          with cols[2]:
            st.markdown(f"🏢 {row['departamento']}")

          with cols[3]:
            st.toggle(
                "Activo",
                value=True,
                key=f"status_{row['id']}",
                label_visibility="collapsed",
            )

          with cols[4]:
            if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
              try:
                with engine.begin() as conn:
                  conn.execute(
                      sqlalchemy.text(
                          "DELETE FROM usuarios WHERE id = :id_val"
                      ),
                      {"id_val": row["id"]},
                  )
                st.success(f"Usuario {row['usuario']} eliminado.")
                st.rerun()
              except Exception as err:
                st.error(f"Error al eliminar: {err}")

          st.markdown("---")
    else:
      st.info("No hay usuarios registrados en la base de datos.")
  except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")

# -------------------------------------------------------------------------
# 2. CREAR NUEVO USUARIO
# -------------------------------------------------------------------------
with tab_crear:
  st.subheader("Registrar Nuevo Usuario")

  with st.form("form_nuevo_usuario", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      nuevo_id = st.text_input("ID (Clave única)", key="create_user_id")
      nuevo_usuario = st.text_input("Nombre de Usuario", key="create_user_name")
      nuevo_password = st.text_input(
          "Contraseña", type="password", key="create_user_pwd"
      )

    with col2:
      tipo_usuario_opciones = ["Administrador", "Operador", "Consulta"]
      nuevo_tipo = st.selectbox(
          "Tipo de Usuario", tipo_usuario_opciones, key="create_user_type"
      )
      nuevo_departamento = st.text_input(
          "Departamento",
          placeholder="Ej. Telemetría, Operaciones",
          key="create_user_dept",
      )

    submitted = st.form_submit_button("Guardar Usuario")

    if submitted:
      if not nuevo_id or not nuevo_usuario or not nuevo_password:
        st.error(
            "Los campos ID, Usuario y Contraseña son obligatorios.",
            icon="🚨",
        )
      else:
        try:
          engine = get_connection()
          with engine.begin() as conn:
            query = sqlalchemy.text("""
                            INSERT INTO usuarios (id, usuario, password, tipo_usuario, departamento) 
                            VALUES (:id, :usuario, :password, :tipo_usuario, :departamento)
                        """)
            conn.execute(
                query,
                {
                    "id": nuevo_id,
                    "usuario": nuevo_usuario,
                    "password": nuevo_password,
                    "tipo_usuario": nuevo_tipo,
                    "departamento": nuevo_departamento,
                },
            )

          st.success(f"¡Usuario **{nuevo_usuario}** registrado exitosamente!")
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar el usuario en la base de datos: {e}")
