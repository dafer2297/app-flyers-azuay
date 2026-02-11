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
    # A. Fondo
    bg_style = "background-color: #1E88E5;" # Azul por defecto
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"""
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """

    # B. Fuente Canaro
    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css = f"""
        @font-face {{
            font-family: 'Canaro';
            src: url('data:font/ttf;base64,{font_b64}') format('truetype');
        }}
        """

    # C. Firma Jota (HTML Puro)
    firma_html = ""
    if os.path.exists("firma_jota.png"):
        firma_b64 = get_base64_of_bin_file("firma_jota.png")
        firma_html = f"""
        <div class="firma-jota">
            <img src="data:image/png;base64,{firma_b64}">
        </div>
        """

    # D. INYECCIÓN CSS (CORREGIDO PARA FORMULARIO Y BOTONES)
    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        {font_css}
        
        /* Títulos */
        h1, h2, h3, .titulo-custom {{
            font-family: 'Canaro', sans-serif !important;
            color: white !important;
            text-transform: uppercase;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
        }}
        
        /* Textos generales */
        p, label, span, div {{
            color: white !important;
            font-family: sans-serif;
        }}
        
        /* FIRMA FIJA (Asegurada en la esquina) */
        .firma-jota {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 180px; 
            z-index: 9999; /* Por encima de todo */
            pointer-events: none; /* Click traspasa */
        }}
        
        /* Espacio extra abajo para que la firma no tape contenido al hacer scroll */
        .block-container {{
            padding-bottom: 150px;
        }}

        /* BOTONES (Incluido el "Volver") */
        .stButton > button {{
            background-color: transparent;
            color: white;
            border: 2px solid white;
            border-radius: 15px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .stButton > button:hover {{
            background-color: #D81B60; /* Rosa al pasar mouse */
            border-color: #D81B60;
            color: white;
        }}
        
        /* INPUTS (Cajas de texto blancas) */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
            background-color: white;
            color: #000 !important; /* Texto negro al escribir */
            border-radius: 8px;
            border: none;
        }}
        
        /* ETIQUETAS DE INPUTS (Labels) */
        .stTextInput label, .stTextArea label, .stFileUploader label {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        
        /* EFECTO ZOOM ICONOS INICIO */
        .zoom-img {{ transition: transform 0.3s ease; cursor: pointer; }}
        .zoom-img:hover {{ transform: scale(1.1); }}
        
        /* Ocultar elementos de Streamlit */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        </style>
        {firma_html}
        """, unsafe_allow_html=True
    )

set_design()

# --- 3. LOGO SUPERIOR ---
if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

# --- 4. NAVEGACIÓN ---
query_params = st.query_params
area_seleccionada = query_params.get("area", None)

# =================================================
# 🏠 PÁGINA 1: INICIO
# =================================================
if not area_seleccionada:
    
    st.markdown("<h2 style='text-align: center; font-size: 30px;'>SELECCIONA EL DEPARTAMENTO:</h2>", unsafe_allow_html=True)
    st.write("---")

    col1, col_cultura, col_recreacion, col4 = st.columns([1, 2, 2, 1])

    with col_cultura:
        if os.path.exists("btn_cultura.png"):
            img_b64 = get_base64_of_bin_file("btn_cultura.png")
            st.markdown(
                f"""
                <a href="?area=Cultura" target="_self" style="text-decoration: none;">
                    <div style="text-align: center;">
                        <img src="data:image/png;base64,{img_b64}" class="zoom-img" width="100%">
                        <div style="font-family: 'Canaro'; font-size: 20px; margin-top: 10px; font-weight: bold;">CULTURA</div>
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
                        <div style="font-family: 'Canaro'; font-size: 20px; margin-top: 10px; font-weight: bold;">RECREACIÓN</div>
                    </div>
                </a>
                """, unsafe_allow_html=True
            )

# =================================================
# 📝 PÁGINA 2: FORMULARIO (CORREGIDO)
# =================================================
elif area_seleccionada in ["Cultura", "Recreación"]:
    
    # 1. Botón Volver con estilo mejorado
    if st.button("⬅️ VOLVER AL INICIO"):
        st.query_params.clear()
        st.rerun()

    # 2. Título de la sección
    # st.markdown(f"<h1 style='text-align: center;'>DATOS DE {area_seleccionada.upper()}</h1>", unsafe_allow_html=True)
    
    # 3. Estructura de Columnas (Icono Izquierda - Formulario Derecha)
    col_izq, col_der = st.columns([1, 2], gap="large")
    
    # --- COLUMNA IZQUIERDA (ICONO) ---
    with col_izq:
        st.write("") # Espacio para bajar un poco la imagen
        st.write("")
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        
        if os.path.exists(icono):
            # TRUCO: Usamos width=350 para que NO salga gigante
            st.image(icono, width=350) 
        else:
            st.warning(f"Falta {icono}")

    # --- COLUMNA DERECHA (INPUTS EXACTOS A TU DISEÑO) ---
    with col_der:
        
        # A. Descripción Principal
        st.text_input("DESCRIPCIÓN", placeholder="Escribe aquí...")
        
        # B. Descripción 2 (Opcional)
        st.text_input("DESCRIPCIÓN 2 (OPCIONAL)", placeholder="Información extra...")
        
        # C. Fechas (Lado a Lado)
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.text_input("FECHA INICIO", placeholder="Ej: Lunes 12 de Enero")
        with c_f2:
            st.text_input("FECHA FINAL (OPCIONAL)", placeholder="Ej: Viernes 16 de Enero")
            
        # D. Horarios (Lado a Lado)
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.text_input("HORARIO INICIO", placeholder="Ej: 09:00 AM")
        with c_h2:
            st.text_input("HORARIO FINAL (OPCIONAL)", placeholder="Ej: 14:00 PM")
            
        # E. Dirección
        st.text_input("DIRECCIÓN", placeholder="Ubicación del evento")
        
        # F. Subida de Archivos
        st.markdown("---")
        st.file_uploader("SUBIR IMAGEN DE FONDO", type=['jpg', 'png'])
        st.file_uploader("SUBIR LOGO/S COLABORADOR/ES (OPCIONAL MÁXIMO 2)", accept_multiple_files=True)
        
        st.write("")
        # Botón Generar (Color Primario)
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
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
        st.image("https://via.placeholder.com/600x800.png?text=FLYER+GENERADO", caption="Diseño Final", use_container_width=True)

    with col_descarga:
        st.markdown("### OPCIONES")
        c1, c2 = st.columns(2)
        with c1: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op2")
        with c2: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op3")
        
        st.write("---")
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
