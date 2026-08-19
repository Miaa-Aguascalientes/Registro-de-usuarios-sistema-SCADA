import hashlib
import pandas as pd
import streamlit as st

# Conexión a la base de datos MySQL mediante los secretos de Streamlit
conn = st.connection("mysql", type="sql")

st.title("👥 Gestión de Usuarios del Sistema")
st.markdown(
    "Administra las credenciales, tipos de usuario y departamentos de la base"
    " de datos `miaamx_telemetria2`."
)

# Pestañas principales
tab_lista, tab_crear, tab_editar_eliminar = st.tabs([
    "📋 Lista de Usuarios",
    "➕ Nuevo Usuario",
    "✏️ Editar / Eliminar",
])

# -------------------------------------------------------------------------
# 1. LISTA DE USUARIOS
# -------------------------------------------------------------------------
with tab_lista:
  st.subheader("Usuarios Registrados")
  df_usuarios = conn.query(
      "SELECT id, usuario, tipo_usuario, departamento FROM usuarios",
      ttl=0,
  )

  if not df_usuarios.empty:
    st.dataframe(df_usuarios, use_container_width=True)
  else:
    st.info("No hay usuarios registrados en la base de datos.")

# -------------------------------------------------------------------------
# 2. CREAR NUEVO USUARIO
# -------------------------------------------------------------------------
with tab_crear:
  st.subheader("Registrar Nuevo Usuario")

  with st.form("form_nuevo_usuario", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      nuevo_id = st.text_input(
          "ID (Clave única)", key="create_user_id"
      )
      nuevo_usuario = st.text_input(
          "Nombre de Usuario", key="create_user_name"
      )
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
          query = """
                        INSERT INTO usuarios (id, usuario, password, tipo_usuario, departamento) 
                        VALUES (:id, :usuario, :password, :tipo_usuario, :departamento)
                    """
          with conn.session as s:
            s.execute(
                query,
                {
                    "id": nuevo_id,
                    "usuario": nuevo_usuario,
                    "password": nuevo_password,
                    "tipo_usuario": nuevo_tipo,
                    "departamento": nuevo_departamento,
                },
            )
            s.commit()

          st.success(
              f"¡Usuario **{nuevo_usuario}** registrado exitosamente!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar el usuario en la base de datos: {e}")

# -------------------------------------------------------------------------
# 3. EDITAR O ELIMINAR USUARIO
# -------------------------------------------------------------------------
with tab_editar_eliminar:
  st.subheader("Modificar o Eliminar Usuarios Existentes")

  df_existentes = conn.query(
      "SELECT id, usuario, password, tipo_usuario, departamento FROM usuarios",
      ttl=0,
  )

  if df_existentes.empty:
    st.warning("No hay usuarios disponibles para editar.")
  else:
    usuario_seleccionado = st.selectbox(
        "Selecciona el usuario a gestionar",
        df_existentes["usuario"].tolist(),
        key="select_user_to_edit",
    )

    user_data = df_existentes[
        df_existentes["usuario"] == usuario_seleccionado
    ].iloc[0]

    with st.form("form_editar_usuario"):
      st.markdown(f"Editando al usuario: **{usuario_seleccionado}**")

      edit_id = st.text_input(
          "ID", value=str(user_data["id"]), disabled=True, key="edit_user_id"
      )
      edit_usuario = st.text_input(
          "Nombre de Usuario",
          value=str(user_data["usuario"]),
          key="edit_user_name",
      )
      edit_password = st.text_input(
          "Nueva Contraseña (dejar en blanco para no cambiar)",
          type="password",
          value="",
          key="edit_user_pwd",
      )
      edit_tipo = st.text_input(
          "Tipo de Usuario",
          value=str(user_data["tipo_usuario"]),
          key="edit_user_type",
      )
      edit_departamento = st.text_input(
          "Departamento",
          value=str(user_data["departamento"]),
          key="edit_user_dept",
      )

      col_update, col_delete = st.columns(2)
      actualizar = col_update.form_submit_button("Actualizar Cambios")
      eliminar = col_delete.form_submit_button(
          "Eliminar Usuario", type="primary"
      )

      if actualizar:
        try:
          pwd_to_save = (
              edit_password if edit_password != "" else user_data["password"]
          )

          query_update = """
                        UPDATE usuarios 
                        SET usuario = :usuario, password = :password, tipo_usuario = :tipo_usuario, departamento = :departamento 
                        WHERE id = :id
                    """
          with conn.session as s:
            s.execute(
                query_update,
                {
                    "usuario": edit_usuario,
                    "password": pwd_to_save,
                    "tipo_usuario": edit_tipo,
                    "departamento": edit_departamento,
                    "id": user_data["id"],
                },
            )
            s.commit()

          st.success("¡Usuario actualizado correctamente!")
          st.rerun()
        except Exception as e:
          st.error(f"Error al actualizar: {e}")

      if eliminar:
        try:
          query_delete = "DELETE FROM usuarios WHERE id = :id"
          with conn.session as s:
            s.execute(query_delete, {"id": user_data["id"]})
            s.commit()

          st.success(
              f"El usuario **{usuario_seleccionado}** ha sido eliminado"
              " correctamente."
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error al eliminar el usuario: {e}")
