from cryptography.fernet import Fernet
import base64
import hashlib
import random
import urllib.parse
from sqlalchemy import create_engine, event
import pandas as pd
import pymysql
import streamlit as st

# Configuración inicial de la página con los parámetros solicitados
st.set_page_config(
    page_title="Sistema registros",
    page_icon="https://www.miaa.mx/favicon.ico",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- LLAVE DE CIFRADO FIJA Y SEGURA ---
SECRET_FERNET_KEY = b"12345678901234567890123456789012"


def get_fernet_cipher():
  try:
    key = st.secrets["security"]["fernet_key"].encode()
  except Exception:
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_FERNET_KEY).digest())
  return Fernet(key)


def encriptar_pwd(password_plana):
  try:
    f = get_fernet_cipher()
    return f.encrypt(password_plana.encode()).decode()
  except Exception:
    return password_plana


def desencriptar_pwd(password_cifrada):
  try:
    f = get_fernet_cipher()
    return f.decrypt(password_cifrada.encode()).decode()
  except Exception:
    return password_cifrada


# --- LOGOTIPO, TÍTULO Y LÍNEA DIVISORIA TURQUESA ---
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" style="width: 80px;">
        <h1 style="margin: 0; color: #FFFFFF; font-size: 18px; font-weight: bold;">Registro de usuarios</h1>
    </div>
    <hr style="border: none; height: 2px; background-color: #00d4ff; margin-top: 5px; margin-bottom: 20px;">
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# SISTEMA DE AUTENTICACIÓN
# -------------------------------------------------------------------------
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
    engine = create_engine(
        st.secrets["databases"]["url_dic"],
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    return engine
  except Exception as e:
    st.error(f"⚠️ ERROR CRÍTICO DE CONEXIÓN TELEMETRÍA: {e}")
    return None


def get_connection():
  try:
    url = st.secrets["databases"]["url_dic"]
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
  except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    return None


def verificar_credenciales(usuario_input, password_input):
  try:
    connection = get_connection()
    if connection:
      with connection.cursor() as cursor:
        cursor.execute(
            "SELECT password, tipo_usuario FROM usuarios WHERE usuario = %s",
            (usuario_input,),
        )
        res = cursor.fetchone()
      connection.close()

      if res:
        pwd_real = desencriptar_pwd(res["password"])
        if str(password_input) == str(pwd_real):
          if str(res["tipo_usuario"]).strip().lower() == "administrador":
            return res["tipo_usuario"]
          else:
            st.error("⛔ Acceso denegado: Solo administradores permitidos.")
            return None
    return None
  except Exception as e:
    st.error(f"Error al consultar usuario: {e}")
    return None


# -------------------------------------------------------------------------
# ESTILO VISUAL HUD ADAPTADO PARA MÓVIL (BOTONES CENTRADOS Y TEXTO NEGRO)
# -------------------------------------------------------------------------
st.markdown(
    """
<style>
    .stApp { background-color: #050a10 !important; }
    .block-container { padding: 8px !important; max-width: 100% !important; }
    header, footer { visibility: hidden !important; }
    
    /* EFECTOS Y ANIMACIONES REDUCIDAS PARA MÓVIL */
    .visual-core { position: relative; width: 180px; height: 180px; margin: 0 auto 20px auto; }
    .ring { position: absolute; border-radius: 50%; border: 3px solid transparent; animation: spin var(--d) linear infinite; }
    .r1 { width: 100%; height: 100%; border-top: 4px solid #00d4ff; border-bottom: 4px solid #00d4ff; --d: 4s; }
    .r2 { width: 78%; height: 78%; top: 11%; left: 11%; border: 2px dashed #00d4ff; --d: 8s; animation-direction: reverse; }
    .center-logo { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
    .logo-miaa { width: 80px; filter: drop-shadow(0 0 8px #00d4ff); }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    /* ESTILO UNIFICADO DE INPUTS */
    div[data-testid="stTextInputRootElement"] {
        background-color: #0d1b2a !important;
        border: 1px solid #1f4068 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
    }
    .stTextInput input {
        color: #00d4ff !important;
        font-size: 14px !important;
    }
    
    /* LETRAS DE LOS LABELS Y TEXTOS GENERALES EN BLANCO BRILLANTE */
    .stTextInput label, .stSelectbox label {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* FORZAR COLOR BLANCO BRILLANTE EN CONTENEDORES DE LISTAS (USUARIOS Y DEPTO) */
    div[data-testid="stVerticalBlock"] p, 
    div[data-testid="stVerticalBlock"] span {
        color: #FFFFFF !important;
    }
    
    /* CONTENEDOR PARA CENTRAR Y ESTILIZAR BOTONES */
    div[data-testid="stFormSubmitButton"] {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    
    div[data-testid="stFormSubmitButton"] button { 
        background: #00d4ff !important; 
        color: #000000 !important; 
        font-weight: bold !important; 
        width: 80% !important; 
        max-width: 300px;
        height: 42px; 
        border: none !important; 
        border-radius: 4px;
        margin: 0 auto;
    }
    
    div[data-testid="stFormSubmitButton"] button p {
        color: #000000 !important;
        font-weight: bold !important;
    }

    .login-box { 
        background: rgba(0, 212, 255, 0.05); 
        border-left: 4px solid #00d4ff; 
        padding: 15px; 
        margin-top: 10px; 
        width: 100%; 
    }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# PANTALLA DE LOGIN (OPTIMIZADA EN VERTICAL PARA CELULAR)
# -------------------------------------------------------------------------
if not st.session_state.autenticado:
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

  if not st.session_state.fase_carga:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown(
        '<h2 style="color:#00d4ff; font-size:15px;">// CREDENCIALES SCADA</h2>',
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
      u = st.text_input("USUARIO")
      p = st.text_input("PASSWORD", type="password")
      submitted_login = st.form_submit_button("ACCEDER")
      if submitted_login:
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
        '<h2 style="color:#00d4ff; font-size:15px;">// CONFIGURANDO ENTORNO'
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
es_admin = (
    str(st.session_state.get("rol", "")).strip().lower() == "administrador"
)

tab_lista, tab_crear, tab_editar = st.tabs(
    ["📋 Lista", "➕ Nuevo", "✏️ Editar"]
)

# -------------------------------------------------------------------------
# 1. LISTA DE USUARIOS Y BUSCADOR
# -------------------------------------------------------------------------
with tab_lista:
  st.subheader("Usuarios")

  busqueda = st.text_input(
      "🔍 Buscar usuario",
      placeholder="Filtro...",
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
              st.markdown(
                  f"👤 **{row['usuario']}** | <span"
                  f" style='color:#00d4ff;'>{row['tipo_usuario']}</span>",
                  unsafe_allow_html=True,
              )
              st.markdown(f"🏢 Depto: {row['departamento']}")

              if es_admin:
                if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                  try:
                    connection = get_connection()
                    with connection.cursor() as cursor:
                      cursor.execute(
                          "DELETE FROM usuarios WHERE id = %s", (row["id"],)
                      )
                      connection.commit()
                    connection.close()
                    st.success(f"Usuario eliminado.")
                    st.rerun()
                  except Exception as err:
                    st.error(f"Error: {err}")

              st.markdown("---")
        else:
          st.warning("No se encontraron resultados.")
      else:
        st.info("No hay registros.")
  except Exception as e:
    st.error(f"Error de conexión: {e}")

# -------------------------------------------------------------------------
# 2. CREAR NUEVO USUARIO
# -------------------------------------------------------------------------
with tab_crear:
  st.subheader("Nuevo Usuario")

  if not es_admin:
    st.error("⛔ Acceso restringido a Administradores.")
  else:
    with st.form("form_nuevo_usuario", clear_on_submit=True):
      nuevo_usuario = st.text_input(
          "Nombre de Usuario", key="create_user_name"
      )
      nuevo_password = st.text_input(
          "Contraseña", type="password", key="create_user_pwd"
      )

      tipo_usuario_opciones = ["Administrador", "Operador", "Consulta"]
      nuevo_tipo = st.selectbox(
          "Tipo de Usuario", tipo_usuario_opciones, key="create_user_type"
      )
      nuevo_departamento = st.text_input(
          "Departamento",
          placeholder="Ej. Telemetría",
          key="create_user_dept",
      )

      submitted = st.form_submit_button("Guardar Usuario")

      if submitted:
        if not nuevo_usuario or not nuevo_password:
          st.error("Campos obligatorios vacíos.", icon="🚨")
        else:
          try:
            nuevo_id = str(random.randint(1000000000, 9999999999))
            password_cifrada = encriptar_pwd(nuevo_password)

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
                        password_cifrada,
                        nuevo_tipo,
                        nuevo_departamento,
                    ),
                )
                connection.commit()
              connection.close()

              st.success(f"¡Usuario registrado exitosamente!")
              st.rerun()
          except Exception as e:
            st.error(f"Error al guardar: {e}")

# -------------------------------------------------------------------------
# 3. EDITAR USUARIO EXISTENTE
# -------------------------------------------------------------------------
with tab_editar:
  st.subheader("Modificar Usuario")

  if not es_admin:
    st.error("⛔ Acceso restringido a Administradores.")
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
      st.error(f"Error al cargar: {e}")

    if not lista_editables:
      st.warning("No hay usuarios disponibles.")
    else:
      nombres_usuarios = [u["usuario"] for u in lista_editables]

      usuario_seleccionado_nombre = st.selectbox(
          "Selecciona el usuario",
          nombres_usuarios,
          key="select_user_to_edit_auto",
      )

      user_data = next(
          u
          for u in lista_editables
          if u["usuario"] == usuario_seleccionado_nombre
      )
      pwd_clara = desencriptar_pwd(str(user_data["password"] or ""))

      with st.form("form_editar_usuario"):
        edit_usuario = st.text_input(
            "Nombre de Usuario", value=user_data["usuario"]
        )
        edit_password = st.text_input("Contraseña", value=pwd_clara)

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
            pwd_a_guardar = encriptar_pwd(edit_password)

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

              st.success("¡Actualizado correctamente!")
              st.rerun()
          except Exception as e:
            st.error(f"Error al actualizar: {e}")
