import streamlit as st
import base64
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Generador Azuay", layout="wide")

# --- 2. DISEÑO, FONDO Y FIRMA ---
def set_design():
    # A. Fondo Azul
    bg_style = ""
    if os.path.exists("fondo_app.png"):
        with open("fondo_app.png", "rb") as f:
            encoded_bg = base64.b64encode(f.read()).decode()
        bg_style = f"""
            background-image: url(data:image/png;base64,{encoded_bg});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        bg_style = "background-color: #1E88E5;"

    # B. Firma Jota (Fija abajo izquierda)
    firma_div = ""
    if os.path.exists("firma_jota.png"):
        with open("firma_jota.png", "rb") as f:
            encoded_firma = base64.b64encode(f.read()).decode()
        firma_div = f"""
            <div class="firma-jota">
                <img src="data:image/png;base64,{encoded_firma}">
            </div>
        """

    # C. Estilos CSS
    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        
        /* Textos Blancos */
        h1, h2, h3, p, label, span, div {{
            color: white !important;
            text-shadow: 0px 1px 3px rgba(0,0,0,0.5);
        }}
        
        /* Firma Fija */
        .firma-jota {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 200px;
            z-index: 100;
            pointer-events: none;
        }}
        @media (max-width: 640px) {{
            .firma-jota {{ width: 120px; bottom: 10px; left: 10px; }}
        }}
        
        /* Botones Estilizados */
        .stButton > button {{
            border-radius: 20px;
            font-weight: bold;
            border: 2px solid white;
            background-color: #D81B60;
            color: white;
        }}
        .stButton > button:hover {{
            background-color: #AD1457;
            transform: scale(1.02);
        }}
        </style>
        {firma_div}
        """, unsafe_allow_html=True
    )

set_design()

# --- 3. LOGO SUPERIOR ---
if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

# --- 4. NAVEGACIÓN ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'inicio'
if 'area' not in st.session_state: st.session_state.area = None

def ir_a(pagina, area=None):
    st.session_state.pagina = pagina
    if area: st.session_state.area = area
    st.rerun()

# =================================================
# 🏠 PÁGINA 1: INICIO
# =================================================
if st.session_state.pagina == 'inicio':
    st.markdown("<h2 style='text-align: center;'>Selecciona el departamento:</h2>", unsafe_allow_html=True)
    st.write("---")

    c1, col_cultura, col_recreacion, c4 = st.columns([1, 2, 2, 1])

    with col_cultura:
        if os.path.exists("btn_cultura.png"):
            st.image("btn_cultura.png", use_container_width=True)
            if st.button("🎭 IR A CULTURA", use_container_width=True):
                ir_a('formulario', 'Cultura')
        else:
            st.warning("Falta btn_cultura.png")

    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            st.image("btn_recreacion.png", use_container_width=True)
            if st.button("⚽ IR A RECREACIÓN", use_container_width=True):
                ir_a('formulario', 'Recreación')
        else:
            st.warning("Falta btn_recreacion.png")

# =================================================
# 📝 PÁGINA 2: FORMULARIO
# =================================================
elif st.session_state.pagina == 'formulario':
    if st.button("⬅️ Volver"): ir_a('inicio')
    
    st.markdown(f"<h1 style='text-align: center;'>Datos de {st.session_state.area.upper()}</h1>", unsafe_allow_html=True)
    
    col_izq, col_der = st.columns([1, 2])
    with col_izq:
        icono = "icono_cultura.png" if st.session_state.area == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, use_container_width=True)
    
    with col_der:
        st.text_input("Título del Evento:", "TE INVITA")
        st.text_area("Descripción:")
        c1, c2 = st.columns(2)
        with c1: st.text_input("Fecha:")
        with c2: st.text_input("Hora:")
        st.text_input("Lugar:")
        st.file_uploader("Subir Imagen:")
        st.write("")
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
            ir_a('final')

# =================================================
# 📥 PÁGINA 3: RESULTADO FINAL (3 Columnas)
# =================================================
elif st.session_state.pagina == 'final':
    
    st.title("¡Tu Flyer está listo!")
    
    # 3 Columnas: Arte | Flyer | Descarga
    col_arte, col_flyer, col_descarga = st.columns([1, 2, 1])
    
    # 1. IZQUIERDA: CHOLA PINCEL
    with col_arte:
        st.markdown("### ARTE")
        if os.path.exists("mascota_pincel.png"):
            st.image("mascota_pincel.png", use_container_width=True)
        else:
            st.info("Falta mascota_pincel.png")

    # 2. CENTRO: EL FLYER (Simulado por ahora)
    with col_flyer:
        # Aquí cargamos una imagen gris de prueba
        st.image("https://via.placeholder.com/600x800.png?text=TU+FLYER+AQUI", caption="Diseño Final", use_container_width=True)

    # 3. DERECHA: DESCARGA Y MASCOTA FINAL
    with col_descarga:
        st.markdown("### OPCIONES")
        
        # Opciones extra simuladas
        c1, c2 = st.columns(2)
        with c1: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op+2", caption="Opción 2")
        with c2: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op+3", caption="Opción 3")
        
        st.write("---")
        
        # CHOLA DESCARGA
        if os.path.exists("mascota_final.png"):
            st.image("mascota_final.png", use_container_width=True)
        
        # BOTÓN DESCARGA (Descarga el propio código como prueba)
        with open("streamlit_app.py", "rb") as file:
            st.download_button(
                label="⬇️ DESCARGAR FLYER",
                data=file,
                file_name="flyer_azuay.png",
                mime="image/png",
                use_container_width=True
            )
            
    st.write("---")
    if st.button("🔄 Crear Nuevo"): ir_a('inicio')
