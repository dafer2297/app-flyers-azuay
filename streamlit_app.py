import streamlit as st
import base64
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Generador Azuay", layout="wide")

# --- 2. FUNCIONES DE CARGA DE ESTILOS Y ASSETS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design():
    # A. Cargar Fondo
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        '''
        st.markdown(bg_img, unsafe_allow_html=True)
    else:
        st.markdown('<style>.stApp {background-color: #1E88E5;}</style>', unsafe_allow_html=True)

    # B. Cargar Fuente Canaro (Si existe)
    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css = f"""
        @font-face {{
            font-family: 'Canaro';
            src: url('data:font/ttf;base64,{font_b64}') format('truetype');
        }}
        """

    # C. Cargar Firma Jota (HTML Puro para que no falle)
    firma_html = ""
    if os.path.exists("firma_jota.png"):
        firma_b64 = get_base64_of_bin_file("firma_jota.png")
        firma_html = f"""
        <div class="firma-jota">
            <img src="data:image/png;base64,{firma_b64}">
        </div>
        """

    # D. INYECCIÓN CSS (ESTILOS GLOBALES)
    st.markdown(
        f"""
        <style>
        {font_css}
        
        /* Aplicar fuente Canaro a títulos */
        h1, h2, h3, .titulo-custom {{
            font-family: 'Canaro', sans-serif !important;
            color: white !important;
            text-shadow: 0px 2px 5px rgba(0,0,0,0.3);
            text-transform: uppercase;
        }}
        
        /* Textos generales blancos */
        p, label, span, div {{
            color: white !important;
        }}
        
        /* FIRMA FLOTANTE */
        .firma-jota {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 200px;
            z-index: 999;
            pointer-events: none;
        }}
        @media (max-width: 640px) {{
            .firma-jota {{ width: 120px; bottom: 10px; left: 10px; }}
        }}

        /* EFECTO ZOOM EN LOS ICONOS */
        .zoom-img {{
            transition: transform 0.3s ease; /* Suavidad */
            cursor: pointer;
            filter: drop-shadow(0px 5px 5px rgba(0,0,0,0.5));
        }}
        .zoom-img:hover {{
            transform: scale(1.1); /* Crece un 10% */
        }}
        
        /* TEXTO DEBAJO DE ICONOS */
        .label-icono {{
            font-family: 'Canaro', sans-serif;
            font-size: 24px;
            text-align: center;
            margin-top: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        
        /* Ocultar elementos extra de Streamlit */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Inputs transparentes bonitos */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
            background-color: rgba(255, 255, 255, 0.9);
            color: #333 !important;
            border-radius: 10px;
        }}
        </style>
        {firma_html}
        """, unsafe_allow_html=True
    )

set_design()

# --- 3. LOGO SUPERIOR ---
if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

# --- 4. NAVEGACIÓN (Lógica por URL para clic en imagen) ---
# Leemos los parámetros de la URL para saber dónde estamos
query_params = st.query_params
area_seleccionada = query_params.get("area", None)

# =================================================
# 🏠 PÁGINA 1: INICIO (ICONOS CLICABLES)
# =================================================
if not area_seleccionada:
    
    st.markdown("<h2 style='text-align: center; font-size: 30px;'>Selecciona el departamento:</h2>", unsafe_allow_html=True)
    st.write("---")

    # Usamos HTML para hacer las imágenes clicables y con zoom
    col1, col_cultura, col_recreacion, col4 = st.columns([1, 2, 2, 1])

    with col_cultura:
        if os.path.exists("btn_cultura.png"):
            img_b64 = get_base64_of_bin_file("btn_cultura.png")
            # Esto crea una imagen que al darle clic recarga la página con ?area=Cultura
            st.markdown(
                f"""
                <a href="?area=Cultura" target="_self" style="text-decoration: none;">
                    <div style="text-align: center;">
                        <img src="data:image/png;base64,{img_b64}" class="zoom-img" width="100%">
                        <div class="label-icono">CULTURA</div>
                    </div>
                </a>
                """, unsafe_allow_html=True
            )

    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            img_b64 = get_base64_of_bin_file("btn_recreacion.png")
            st.markdown(
                f"""
                <a href="?area=Recreación" target="_self" style="text-decoration: none;">
                    <div style="text-align: center;">
                        <img src="data:image/png;base64,{img_b64}" class="zoom-img" width="100%">
                        <div class="label-icono">RECREACIÓN</div>
                    </div>
                </a>
                """, unsafe_allow_html=True
            )

# =================================================
# 📝 PÁGINA 2: FORMULARIO
# =================================================
elif area_seleccionada in ["Cultura", "Recreación"]:
    
    # Botón para limpiar la URL y volver al inicio
    if st.button("⬅️ VOLVER AL INICIO"):
        st.query_params.clear()
        st.rerun()

    st.markdown(f"<h1 style='text-align: center; font-size: 50px;'>DATOS DE {area_seleccionada.upper()}</h1>", unsafe_allow_html=True)
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, use_container_width=True)
    
    with col_der:
        st.text_input("TÍTULO DEL EVENTO:", "TE INVITA")
        st.text_area("DESCRIPCIÓN:")
        
        c1, c2 = st.columns(2)
        with c1: st.text_input("FECHA:")
        with c2: st.text_input("HORA:")
        
        st.text_input("LUGAR:")
        uploaded_file = st.file_uploader("SUBIR IMAGEN DE FONDO:", type=['png', 'jpg', 'jpeg'])
        
        st.write("")
        # Usamos un botón normal de Streamlit para la acción final
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
             # Cambiamos el parametro de la URL para ir a la pag final
             st.query_params["area"] = "Final"
             st.rerun()

# =================================================
# 📥 PÁGINA 3: RESULTADO FINAL
# =================================================
elif area_seleccionada == "Final":
    
    st.markdown("<h1 style='text-align: center;'>¡FLYER LISTO!</h1>", unsafe_allow_html=True)
    
    col_arte, col_flyer, col_descarga = st.columns([1, 2, 1])
    
    with col_arte:
        st.markdown("### ARTE")
        if os.path.exists("mascota_pincel.png"):
            st.image("mascota_pincel.png", use_container_width=True)

    with col_flyer:
        # Aquí iría la lógica de generación real. Por ahora el placeholder.
        st.image("https://via.placeholder.com/600x800.png?text=FLYER+GENERADO", caption="Diseño Final", use_container_width=True)

    with col_descarga:
        st.markdown("### OPCIONES")
        c1, c2 = st.columns(2)
        with c1: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op2")
        with c2: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op3")
        
        st.write("---")
        
        # Chola y botón de descarga
        if os.path.exists("mascota_final.png"):
            st.image("mascota_final.png", use_container_width=True)
        
        with open("streamlit_app.py", "rb") as file:
            st.download_button(
                label="⬇️ DESCARGAR",
                data=file,
                file_name="flyer_azuay.png",
                mime="image/png",
                use_container_width=True
            )
            
    st.write("---")
    if st.button("🔄 CREAR NUEVO"):
        st.query_params.clear()
        st.rerun()
