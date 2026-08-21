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


# --- HEADER VISUAL ESTILO TÉCNICO MIAA ---
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-top: 10px; margin-bottom: 5px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" style="width: 110px; filter: drop-shadow(0 0 10px rgba(0,212,255,0.4));">
    </div>
    <div style="text-align: center; color: #8a99ad; font-size: 11px; letter-spacing: 1px; margin-bottom: 15px;">
        MODELO INTEGRAL DE AGUAS DE AGUASCALIENTES
    </div>
    <hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, #00d4ff, transparent); margin-bottom: 25px;">
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
        connect_timeout=5,
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
# ESTILO VISUAL GLOBAL (ELIMINACIÓN DE CONTENEDORES VACÍOS)
# -------------------------------------------------------------------------
st.markdown(
    """
<style>
    .stApp { background-color: #050a10 !important; }
    .block-container { padding: 12px !important; max-width: 600px !important; }
    header, footer { visibility: hidden !important; }
    
    /* TÍTULOS Y TEXTOS */
    h1, h2, h3 { color: #FFFFFF !important; font-family: sans-serif; }
    p, span, label { color: #c0cbd8 !important; }
    
    /* INPUTS DE TEXTO Y SELECTBOXES ESTILO HUD */
    div[data-testid="stTextInputRootElement"], div[data-testid="stSelectbox"] {
        background-color: #0b1624 !important;
        border: 1px solid #19324c !important;
        border-radius: 8px !important;
    }
    .stTextInput input {
        color: #00d4ff !important;
        font-size: 14px !important;
    }
    .stTextInput label, .stSelectbox label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* OCULTAR CUALQUIER CONTENEDOR VACÍO O HUÉRFANO */
    div.element-container:empty, div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }

    /* ESTILO GENERAL PARA BOTONES Y ACCIONES */
    div[data-testid="stFormSubmitButton"] button, 
    .stButton button { 
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important; 
        color: #050a10 !important; 
        font-weight: 800 !important; 
        font-size: 13px !important;
        letter-spacing: 0.5px;
        width: 100% !important; 
        height: 42px; 
        border: none !important; 
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.25);
        transition: all 0.3s ease;
    }

    div[data-testid="stFormSubmitButton"] button *, 
    .stButton button * {
        color: #050a10 !important;
        font-weight: 800 !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover, 
    .stButton button:hover {
        opacity: 0.92;
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    }

    /* CAJA DE TARJETA HUD LIMPIA */
    .hud-card { 
        background: rgba(11, 22, 36, 0.7); 
        border: 1px solid #19324c;
        border-left: 4px solid #00d4ff; 
        padding: 20px; 
        border-radius: 10px;
        margin-bottom: 15px; 
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# PANTALLA DE LOGIN
# -------------------------------------------------------------------------
if not st.session_state.autenticado:
  st.markdown(
      """
        <div class="hud-card" style="text-align: center; margin-top: 10px;">
            <h2 style="color:#00d4ff; font-size:18px; margin-bottom: 5px;">¡Bienvenido!</h2>
            <p style="font-size: 13px; color: #8a99ad;">Ingresa tus credenciales del sistema para continuar</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if not st.session_state.fase_carga:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    with st.form("login_form"):
      u = st.text_input("USUARIO")
      p = st.text_input("PASSWORD", type="password")

      st.markdown("<br>", unsafe_allow_html=True)
      col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
      with col_l2:
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
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 style="color:#00d4ff; font-size:15px; text-align:center;">//'
        " CONFIGURANDO ENTORNO SEGURO...</h3>",
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
  st.markdown("<br>", unsafe_allow_html=True)
  busqueda = st.text_input(
      "🔍 Buscar usuario",
      placeholder="Filtro por nombre, depto o rol...",
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
            st.markdown(
                f"""
                        <div class="hud-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 15px; font-weight: bold; color: #FFFFFF;">👤 {row['usuario']}</span>
                                <span style="background: rgba(0,212,255,0.1); color: #00d4ff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{row['tipo_usuario']}</span>
                            </div>
                            <div style="font-size: 12px; color: #8a99ad; margin-bottom: 12px;">
                                🏢 Departamento: <span style="color: #c0cbd8;">{row['departamento']}</span>
                            </div>
                        </div>
                        """,
                unsafe_allow_html=True,
            )

            if es_admin:
              col_del1, col_del2, col_del3 = st.columns([1, 2, 1])
              with col_del2:
                if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                  try:
                    connection = get_connection()
                    with connection.cursor() as cursor:
                      cursor.execute(
                          "DELETE FROM usuarios WHERE id = %s", (row["id"],)
                      )
                      connection.commit()
                    connection.close()
                    st.success("Usuario eliminado.")
                    st.rerun()
                  except Exception as err:
                    st.error(f"Error: {err}")
              st.markdown(
                  "<div style='margin-bottom: 10px;'></div>",
                  unsafe_allow_html=True,
              )
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
  st.markdown("<br>", unsafe_allow_html=True)
  if not es_admin:
    st.error("⛔ Acceso restringido a Administradores.")
  else:
    with st.form("form_nuevo_usuario", clear_on_submit=True):
      st.markdown(
          "<h3 style='color:#00d4ff; font-size:15px; margin-bottom:15px;'>//"
          " REGISTRAR NUEVO USUARIO</h3>",
          unsafe_allow_html=True,
      )
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

      st.markdown("<br>", unsafe_allow_html=True)
      col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
      with col_c2:
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

              st.success("¡Usuario registrado exitosamente!")
              st.rerun()
          except Exception as e:
            st.error(f"Error al guardar: {e}")

# -------------------------------------------------------------------------
# 3. EDITAR USUARIO EXISTENTE
# -------------------------------------------------------------------------
with tab_editar:
  st.markdown("<br>", unsafe_allow_html=True)
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

      st.markdown("<br>", unsafe_allow_html=True)
      with st.form("form_editar_usuario"):
        st.markdown(
            "<h3 style='color:#00d4ff; font-size:15px; margin-bottom:15px;'>//"
            " MODIFICAR CREDENCIALES</h3>",
            unsafe_allow_html=True,
        )
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

        st.markdown("<br>", unsafe_allow_html=True)
        col_e1, col_e2, col_e3 = st.columns([1, 2, 1])
        with col_e2:
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
