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
# 1. LISTA DE USUARIOS
# -------------------------------------------------------------------------
with tab_lista:
  st.subheader("Usuarios Registrados")
  try:
    connection = get_connection()
    with connection.cursor() as cursor:
      # Asegúrate de que tu tabla tenga la columna 'estatus' (1 para activo, 0 para inactivo)
      # Si tu columna se llama diferente (ej. 'activo'), cámbiala en el SELECT y en el UPDATE
      cursor.execute(
          "SELECT id, usuario, tipo_usuario, departamento, estatus FROM usuarios"
      )
      resultado = cursor.fetchall()
    connection.close()

    if resultado:
      for row in resultado:
        with st.container():
          # Reestructuramos las columnas quitando el espacio del ID
          cols = st.columns([3, 2, 2, 1, 1])

          with cols[0]:
            st.markdown(f"👤 **{row['usuario']}**")

          with cols[1]:
            st.markdown(f"🏢 {row['departamento']}")

          with cols[2]:
            st.markdown(f"📌 *{row['tipo_usuario']}*")

          with cols[3]:
            # El estado actual viene de la base de datos (1 = True, 0 = False)
            estado_actual = True if row.get("estatus", 1) == 1 else False

            nuevo_estado = st.toggle(
                "Activo",
                value=estado_actual,
                key=f"status_{row['id']}",
                label_visibility="collapsed",
            )

            # Si el usuario cambia el interruptor, actualizamos la base de datos de inmediato
            if nuevo_estado != estado_actual:
              try:
                val_db = 1 if nuevo_estado else 0
                connection = get_connection()
                with connection.cursor() as cursor:
                  cursor.execute(
                      "UPDATE usuarios SET estatus = %s WHERE id = %s",
                      (val_db, row["id"]),
                  )
                  connection.commit()
                connection.close()
                st.toast(f"Acceso actualizado para {row['usuario']}")
                st.rerun()
              except Exception as err:
                st.error(f"Error al actualizar estado: {err}")

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
# 2. CREAR NUEVO USUARIO
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
          nuevo_id = str(random.randint(1000000000, 9999999999))

          connection = get_connection()
          with connection.cursor() as cursor:
            # Por defecto, el usuario se crea con estatus = 1 (Activo)
            query = """
                            INSERT INTO usuarios (id, usuario, password, tipo_usuario, departamento, estatus) 
                            VALUES (%s, %s, %s, %s, %s, 1)
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
              f"¡Usuario **{nuevo_usuario}** registrado exitosamente!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar el usuario en la base de datos: {e}")
