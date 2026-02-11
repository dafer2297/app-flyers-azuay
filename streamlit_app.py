import streamlit as st
import base64
import os
import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Generador Azuay", layout="wide")

# --- 2. FUNCIONES Y ESTILOS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design():
    # A. Fondo
    bg_style = "background-color: #1E88E5;" 
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

    # D. INYECCIÓN CSS
    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        {font_css}
        
        /* TÍTULOS */
        h1, h2, h3 {{
            font-family: 'Canaro', sans-serif !important;
            color: white !important;
            text-transform: uppercase;
        }}
        
        /* BOTONES */
        .stButton > button {{
            background-color: transparent;
            color: white;
            border: 2px solid white;
            border-radius: 15px;
            padding: 10px 20px;
            font-weight: bold;
        }}
        .stButton > button:hover {{
            background-color: #D81B60;
            border-color: #D81B60;
        }}
        
        /* INPUTS (Cajas Blancas) */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input,
        .stTimeInput > div > div > input {{
            background-color: white !important;
            color: black !important;
            border-radius: 8px;
            border: none;
        }}
        
        /* Ocultar etiquetas por defecto */
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{
            display: none;
        }}

        /* ETIQUETAS PERSONALIZADAS */
        .label-negro {{
            font-family: 'Canaro', sans-serif;
            font-weight: bold;
            font-size: 16px;
            color: black !important;
            margin-bottom: 2px;
            margin-top: 10px; 
            text-shadow: none !important;
        }}
        .label-blanco {{
            font-family: 'Canaro', sans-serif;
            font-weight: normal;
            font-size: 12px;
            color: white !important;
            margin-left: 5px;
        }}
        
        /* Zoom Iconos Inicio */
        .zoom-img {{ transition: transform 0.3s; }}
        .zoom-img:hover {{ transform: scale(1.1); }}
        
        /* Ocultar menús */
        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
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
    
    st.markdown("<h2 style='text-align: center;'>SELECCIONA EL DEPARTAMENTO:</h2>", unsafe_allow_html=True)
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
                        <div style="font-family: 'Canaro'; font-size: 20px; color:white; margin-top: 10px;">CULTURA</div>
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
                        <div style="font-family: 'Canaro'; font-size: 20px; color:white; margin-top: 10px;">RECREACIÓN</div>
                    </div>
                </a>
                """, unsafe_allow_html=True
            )
            
    # FIRMA EN EL PIE DE PÁGINA (PÁGINA 1) - TAMAÑO AUMENTADO
    st.write("")
    st.write("")
    c_f1, c_f2, c_f3 = st.columns([1, 1, 1])
    with c_f1:
         if os.path.exists("firma_jota.png"):
            # AQUI CAMBIAMOS EL TAMAÑO A 300
            st.image("firma_jota.png", width=300)

# =================================================
# 📝 PÁGINA 2: FORMULARIO
# =================================================
elif area_seleccionada in ["Cultura", "Recreación"]:
    
    if st.button("⬅️ VOLVER AL INICIO"):
        st.query_params.clear()
        st.rerun()

    col_izq, col_der = st.columns([1, 2], gap="large")
    
    # --- IZQUIERDA: ICONO + FIRMA ---
    with col_izq:
        st.write("")
        st.write("")
        # 1. EL ICONO
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono):
            st.image(icono, width=350) 
        
        # 2. ESPACIO
        st.write("") 
        st.write("")
        
        # 3. LA FIRMA
        if os.path.exists("firma_jota.png"):
            st.image("firma_jota.png", width=200)

    # --- DERECHA: FORMULARIO ---
    with col_der:
        
        # A. DESCRIPCIÓN 1 (Cuadro Grande)
        st.markdown('<div class="label-negro">DESCRIPCIÓN</div>', unsafe_allow_html=True)
        st.text_area("lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
        
        # B. DESCRIPCIÓN 2 (Cuadro Mediano)
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        st.text_area("lbl_desc2", label_visibility="collapsed", placeholder="Información extra...", height=100)
        
        # C. FECHAS (Formato Día/Mes/Año)
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown('<div class="label-negro">FECHA INICIO</div>', unsafe_allow_html=True)
            st.date_input("lbl_fecha1", label_visibility="collapsed", format="DD/MM/YYYY")
        with c_f2:
            st.markdown('<div class="label-negro">FECHA FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            st.date_input("lbl_fecha2", label_visibility="collapsed", value=None, format="DD/MM/YYYY")
            
        # D. HORARIOS
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown('<div class="label-negro">HORARIO INICIO</div>', unsafe_allow_html=True)
            st.time_input("lbl_hora1", label_visibility="collapsed", value=datetime.time(9, 00))
        with c_h2:
            st.markdown('<div class="label-negro">HORARIO FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            st.time_input("lbl_hora2", label_visibility="collapsed", value=None)
            
        # E. DIRECCIÓN
        st.markdown('<div class="label-negro">DIRECCIÓN</div>', unsafe_allow_html=True)
        st.text_input("lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")
        
        # F. ARCHIVOS
        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        st.file_uploader("lbl_img", type=['jpg', 'png'], label_visibility="collapsed")
        
        st.markdown('<div class="label-negro">LOGOS COLABORADORES <span class="label-blanco">(MÁX 2)</span></div>', unsafe_allow_html=True)
        st.file_uploader("lbl_logos", accept_multiple_files=True, label_visibility="collapsed")
        
        st.write("")
        st.write("")
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
             st.query_params["area"] = "Final"
             st.rerun()

# =================================================
# 📥 PÁGINA 3: RESULTADO FINAL
# =================================================
elif area_seleccionada == "Final":
    
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    col_arte, col_flyer, col_descarga = st.columns([1.3, 1.5, 0.8])
    
    # --- IZQUIERDA: CHOLA GRANDE + FIRMA ---
    with col_arte:
        st.write("") 
        if os.path.exists("mascota_pincel.png"):
            st.image("mascota_pincel.png", use_container_width=True)
            
        # Firma GRANDE debajo de la chola
        st.write("")
        if os.path.exists("firma_jota.png"):
            # AQUI CAMBIAMOS EL TAMAÑO A 280
            st.image("firma_jota.png", width=280)

    # --- CENTRO: FLYER ---
    with col_flyer:
        st.image("https://via.placeholder.com/600x800.png?text=FLYER+GENERADO", caption="Diseño Final", use_container_width=True)

    # --- DERECHA: CHOLA PEQUEÑA + OPCIONES ---
    with col_descarga:
        st.markdown("<h3 style='text-align: center; font-size: 20px;'>OTRAS OPCIONES</h3>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op2", use_container_width=True)
        with c2: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op3", use_container_width=True)
        
        st.write("---")
        
        # CHOLA PEQUEÑA
        if os.path.exists("mascota_final.png"):
            st.image("mascota_final.png", width=220) 
        
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
