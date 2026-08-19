import pandas as pd
import pymysql
import streamlit as st


# Función de conexión directa a MySQL
def get_connection():
  secrets = st.secrets

  if "mysql_telemetria" not in secrets:
    st.error(
        "🚨 Error crítico: No se encontró la sección [mysql_telemetria] en los"
        f" secretos. Secciones detectadas: {list(secrets.keys())}"
    )
    st.stop()

  db_config = secrets["mysql_telemetria"]

  return pymysql.connect(
      host=db_config["host"],
      user=db_config["user"],
      password=db_config["password"],
      database=db_config["database"],
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
      # Asumiendo que tu tabla tiene un campo 'estatus' o 'activo' (si no lo tienes, puedes agregarlo o adaptarlo)
      cursor.execute(
          "SELECT id, usuario, tipo_usuario, departamento FROM usuarios"
      )
      resultado = cursor.fetchall()
    connection.close()

    if resultado:
      for row in resultado:
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
            # Interruptor de estado visual por fila
            st.toggle(
                "Activo",
                value=True,
                key=f"status_{row['id']}",
                label_visibility="collapsed",
            )

          with cols[4]:
            # Botón de eliminar individual por registro
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

          st.success(f"¡Usuario **{nuevo_usuario}** registrado exitosamente!")
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar el usuario en la base de datos: {e}")
