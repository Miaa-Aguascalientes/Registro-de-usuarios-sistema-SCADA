import random
import pandas as pd
import pymysql
import streamlit as st


# Función para extraer los parámetros de la URL en los secretos y conectar con pymysql
def get_connection():
  secrets = st.secrets

  if "databases" not in secrets or "url_dic" not in secrets["databases"]:
    st.error(
        "🚨 Error crítico: No se encontró la sección [databases] o la llave"
        " 'url_dic' en los secretos de Streamlit."
    )
    st.stop()

  url = secrets["databases"]["url_dic"]

  clean_url = url.replace("mysql+pymysql://", "")
  auth, rest = clean_url.split("@")
  user, password = auth.split(":")
  host, database = rest.split("/")

  return pymysql.connect(
      host=host,
      user=user,
      password=password,
      database=database,
      port=3306,
      cursorclass=pymysql.cursors.DictCursor,
  )


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
    connection = get_connection()
    with connection.cursor() as cursor:
      cursor.execute(
          "SELECT id, usuario, tipo_usuario, departamento FROM usuarios"
      )
      resultado = cursor.fetchall()
    connection.close()

    if resultado:
      for row in resultado:
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
                connection = get_connection()
                with connection.cursor() as cursor:
                  cursor.execute(
                      "DELETE FROM usuarios WHERE id = %s", (row["id"],)
                  )
                  connection.commit()
                connection.close()
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
# 2. CREAR NUEVO USUARIO (ID generado automáticamente)
# -------------------------------------------------------------------------
with tab_crear:
  st.subheader("Registrar Nuevo Usuario")

  with st.form("form_nuevo_usuario", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
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
      if not nuevo_usuario or not nuevo_password:
        st.error(
            "Los campos Nombre de Usuario y Contraseña son obligatorios.",
            icon="🚨",
        )
      else:
        try:
          # Generación automática de un ID numérico aleatorio único de 10 dígitos (similar a tu ejemplo)
          nuevo_id = str(random.randint(1000000000, 9999999999))

          connection = get_connection()
          with connection.cursor() as cursor:
            query = """
                            INSERT INTO usuarios (id, usuario, password, tipo_usuario, departamento) 
                            VALUES (%s, %s, %s, %s, %s)
                        """
            cursor.execute(
                query,
                (
                    nuevo_id,
                    nuevo_usuario,
                    nuevo_password,
                    nuevo_tipo,
                    nuevo_departamento,
                ),
            )
            connection.commit()
          connection.close()

          st.success(
              f"¡Usuario **{nuevo_usuario}** registrado exitosamente con ID"
              f" `{nuevo_id}`!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar el usuario en la base de datos: {e}")
