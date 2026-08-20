import random
import pandas as pd
import pymysql
import streamlit as st
import urllib.parse
from sqlalchemy import create_engine, event

# Configuración inicial de la página con los parámetros solicitados
st.set_page_config(
    page_title="Sistema registros",
    page_icon="https://www.miaa.mx/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------------------
# 0. SECCIÓN ---------------------------------------- SISTEMA DE AUTENTICACIÓN HUD DEFINITIVO --------------------------------------------------------------------
if "autenticado" not in st.session_state:
  query_params = st.query_params
  if query_params.get("access") == "granted":
    st.session_state.autenticado = True
    st.session_state.rol = query_params.get("role", "usuario")
  else:
    st.session_state.autenticado = False

if "fase_carga" not in st.session_state:
  st.session_state.fase_carga = False


@st.cache_resource
def get_mysql_telemetria_engine():
  try:
    c = st.secrets["mysql_telemetria"]
    pwd = urllib.parse.quote_plus(c["password"])
    engine = create_engine(
        f"mysql+mysqlconnector://{c['user']}:{pwd}@{c['host']}/{c['database']}",
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    return engine
  except Exception as e:
    st.error(f"⚠️ ERROR CRÍTICO DE CONEXIÓN TELEMETRÍA: {e}")
    return None


def get_connection():
  """Función auxiliar para pymysql usando los secretos de telemetría"""
  try:
    c = st.secrets["mysql_telemetria"]
    return pymysql.connect(
        host=c["host"],
        user=c["user"],
        password=c["password"],
        database=c["database"],
        port=3306,
        cursorclass=pymysql.cursors.DictCursor,
    )
  except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    return None


def verificar_credenciales(usuario_input, password_input):
  try:
    engine = get_mysql_telemetria_engine()
    if engine is None:
      return None
    query = f"SELECT password, tipo_usuario FROM usuarios WHERE usuario = '{usuario_input}'"
    df_user = pd.read_sql(query, engine)
    if not df_user.empty and str(password_input) == str(
        df_user["password"].iloc[0]
    ):
      return df_user["tipo_usuario"].iloc[0]
    return None
  except Exception as e:
    st.error(f"Error al consultar usuario: {e}")
    return None


# 1. SECCIÓN -------------------------------------------------------ESTILO VISUAL HUD AJUSTADO PARA MÓVIL ----------------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Configuración base */
    .stApp { background-color: #050a10 !important; }
    .block-container { padding: 10px !important; max-width: 100% !important; }
    header, footer { visibility: hidden !important; }
    
    /* EFECTOS Y ANIMACIONES */
    .visual-core { position: relative; width: 280px; height: 280px; margin: auto; }
    .ring { position: absolute; border-radius: 50%; border: 4px solid transparent; animation: spin var(--d) linear infinite; }
    .r1 { width: 100%; height: 100%; border-top: 6px solid #00d4ff; border-bottom: 6px solid #00d4ff; --d: 4s; }
    .r2 { width: 78%; height: 78%; top: 11%; left: 11%; border: 2px dashed #00d4ff; --d: 8s; animation-direction: reverse; }
    .center-logo { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
    .logo-miaa { width: 130px; filter: drop-shadow(0 0 10px #00d4ff); }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    /* ESTILO UNIFICADO DE INPUTS */
    div[data-testid="stTextInputRootElement"] {
        background-color: #0d1b2a !important;
        border: 1px solid #1f4068 !important;
        border-radius: 0px !important;
        box-shadow: none !important;
        height: 40px !important;
    }
    div[data-testid="stTextInputRootElement"] div[data-baseweb="base-input"] {
        background-color: transparent !important;
    }
    .stTextInput input {
        background-color: transparent !important;
        color: #00d4ff !important;
        font-size: 15px !important;
    }
    div[data-testid="stTextInputRootElement"]:focus-within {
        border: 1px solid #00d4ff !important;
    }

    .stButton button { 
        background: #00d4ff !important; color: #050a10 !important; font-weight: bold !important; 
        width: 100%; height: 45px; border: none !important; 
    }
    .login-box { 
        background: rgba(0, 212, 255, 0.05); border-left: 6px solid #00d4ff; 
        padding: 20px; margin-top: 20px; width: 100%; 
    }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# PANTALLA DE LOGIN SI NO ESTÁ AUTENTICADO
# -------------------------------------------------------------------------
if not st.session_state.autenticado:
  col_vis, col_log = st.columns([1, 1])
  with col_vis:
    st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="visual-core">
            <div class="ring r1"></div><div class="ring r2"></div>
            <div class="center-logo">
                <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" class="logo-miaa">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_log:
    if not st.session_state.fase_carga:
      st.markdown('<div class="login-box">', unsafe_allow_html=True)
      st.markdown(
          '<h2 style="color:#00d4ff; font-size:16px;">// CREDENCIALES'
          " SCADA</h2>",
          unsafe_allow_html=True,
      )
      with st.form("login_form"):
        u = st.text_input("USUARIO")
        p = st.text_input("PASSWORD", type="password")
        if st.form_submit_button("ACCEDER"):
          rol = verificar_credenciales(u, p)
          if rol:
            st.session_state.temp_rol = rol
            st.session_state.fase_carga = True
            st.rerun()
          else:
            st.error("❌ ACCESO DENEGADO")
      st.markdown("</div>", unsafe_allow_html=True)
    else:
      st.markdown('<div class="login-box">', unsafe_allow_html=True)
      st.markdown(
          '<h2 style="color:#00d4ff; font-size:16px;">// CONFIGURANDO ENTORNO'
          " MÓVIL...</h2>",
          unsafe_allow_html=True,
      )
      st.session_state.autenticado = True
      st.session_state.rol = st.session_state.temp_rol
      st.session_state.fase_carga = False
      st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)
  st.stop()

# -------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL (POST-AUTENTICACIÓN)
# -------------------------------------------------------------------------
st.title("👥 Gestión de Usuarios del Sistema")
st.markdown(
    "Administra las credenciales, tipos de usuario y departamentos de la base"
    " de datos `miaamx_telemetria2` (tabla `usuarios`)."
)

# Validar si el rol actual es Administrador
es_admin = (
    str(st.session_state.get("rol", "")).strip().lower() == "administrador"
)

# Pestañas principales
tab_lista, tab_crear, tab_editar = st.tabs([
    "📋 Lista de Usuarios",
    "➕ Nuevo Usuario",
    "✏️ Editar Usuario",
])

# -------------------------------------------------------------------------
# 1. LISTA DE USUARIOS Y BUSCADOR
# -------------------------------------------------------------------------
with tab_lista:
  st.subheader("Usuarios Registrados")

  busqueda = st.text_input(
      "🔍 Buscar usuario por nombre, departamento o tipo",
      placeholder="Escribe para filtrar...",
      key="search_list_tab",
  )

  try:
    connection = get_connection()
    if connection:
      with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, usuario, tipo_usuario, departamento FROM usuarios"
        )
        resultado = cursor.fetchall()
      connection.close()

      if resultado:
        df_usuarios = pd.DataFrame(resultado)

        if busqueda:
          query_filtro = (
              df_usuarios["usuario"].str.contains(busqueda, case=False, na=False)
              | df_usuarios["departamento"].str.contains(
                  busqueda, case=False, na=False
              )
              | df_usuarios["tipo_usuario"].str.contains(
                  busqueda, case=False, na=False
              )
          )
          df_usuarios = df_usuarios[query_filtro]

        if not df_usuarios.empty:
          for _, row in df_usuarios.iterrows():
            with st.container():
              if es_admin:
                cols = st.columns([3, 2, 2, 1])
              else:
                cols = st.columns([3, 2, 2])

              with cols[0]:
                st.markdown(f"👤 **{row['usuario']}**")

              with cols[1]:
                st.markdown(f"🏢 {row['departamento']}")

              with cols[2]:
                st.markdown(f"📌 *{row['tipo_usuario']}*")

              if es_admin:
                with cols[3]:
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
          st.warning(
              "No se encontraron usuarios que coincidan con la búsqueda."
          )
      else:
        st.info("No hay usuarios registrados en la base de datos.")
  except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")

# -------------------------------------------------------------------------
# 2. CREAR NUEVO USUARIO (Restringido a Administradores)
# -------------------------------------------------------------------------
with tab_crear:
  st.subheader("Registrar Nuevo Usuario")

  if not es_admin:
    st.error(
        "⛔ Acceso restringido. Solo los usuarios con rol de **Administrador**"
        " pueden dar de alta nuevos usuarios."
    )
  else:
    with st.form("form_nuevo_usuario", clear_on_submit=True):
      col1, col2 = st.columns(2)

      with col1:
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
        if not nuevo_usuario or not nuevo_password:
          st.error(
              "Los campos Nombre de Usuario y Contraseña son obligatorios.",
              icon="🚨",
          )
        else:
          try:
            nuevo_id = str(random.randint(1000000000, 9999999999))

            connection = get_connection()
            if connection:
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
                  f"¡Usuario **{nuevo_usuario}** registrado exitosamente!"
              )
              st.rerun()
          except Exception as e:
            st.error(f"Error al guardar el usuario en la base de datos: {e}")

# -------------------------------------------------------------------------
# 3. EDITAR USUARIO EXISTENTE CON AUTOCOMPLETADO (Restringido a Administradores)
# -------------------------------------------------------------------------
with tab_editar:
  st.subheader("Modificar Datos de Usuario")

  if not es_admin:
    st.error(
        "⛔ Acceso restringido. Solo los usuarios con rol de **Administrador**"
        " pueden editar usuarios."
    )
  else:
    try:
      connection = get_connection()
      if connection:
        with connection.cursor() as cursor:
          cursor.execute(
              "SELECT id, usuario, password, tipo_usuario, departamento FROM"
              " usuarios"
          )
          lista_editables = cursor.fetchall()
        connection.close()
      else:
        lista_editables = []
    except Exception as e:
      lista_editables = []
      st.error(f"Error al cargar usuarios para edición: {e}")

    if not lista_editables:
      st.warning("No hay usuarios disponibles para editar.")
    else:
      nombres_usuarios = [u["usuario"] for u in lista_editables]

      usuario_seleccionado_nombre = st.selectbox(
          "Selecciona o escribe el nombre del usuario",
          nombres_usuarios,
          key="select_user_to_edit_auto",
      )

      user_data = next(
          u
          for u in lista_editables
          if u["usuario"] == usuario_seleccionado_nombre
      )

      with st.form("form_editar_usuario"):
        col_e1, col_e2 = st.columns(2)

        with col_e1:
          edit_usuario = st.text_input(
              "Nombre de Usuario", value=user_data["usuario"]
          )
          edit_password = st.text_input(
              "Nueva Contraseña (dejar en blanco para mantener la actual)",
              type="password",
              value="",
          )

        with col_e2:
          tipo_usuario_opciones = ["Administrador", "Operador", "Consulta"]
          try:
            index_tipo = tipo_usuario_opciones.index(user_data["tipo_usuario"])
          except ValueError:
            index_tipo = 0

          edit_tipo = st.selectbox(
              "Tipo de Usuario", tipo_usuario_opciones, index=index_tipo
          )
          edit_departamento = st.text_input(
              "Departamento", value=str(user_data["departamento"] or "")
          )

        actualizar_btn = st.form_submit_button("Guardar Cambios")

        if actualizar_btn:
          try:
            pwd_a_guardar = (
                edit_password if edit_password != "" else user_data["password"]
            )

            connection = get_connection()
            if connection:
              with connection.cursor() as cursor:
                query_update = """
                                        UPDATE usuarios 
                                        SET usuario = %s, password = %s, tipo_usuario = %s, departamento = %s 
                                        WHERE id = %s
                                    """
                cursor.execute(
                    query_update,
                    (
                        edit_usuario,
                        pwd_a_guardar,
                        edit_tipo,
                        edit_departamento,
                        user_data["id"],
                    ),
                )
                connection.commit()
              connection.close()

              st.success(
                  f"¡El usuario **{edit_usuario}** ha sido actualizado"
                  " correctamente!"
              )
              st.rerun()
          except Exception as e:
            st.error(f"Error al actualizar el usuario: {e}")
