import streamlit as st
import base64
import os
import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Generador Azuay", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design():
    # Fondo General de la App
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"""
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """

    # Fuente Canaro
    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css = f"""
        @font-face {{ font-family: 'Canaro'; src: url('data:font/ttf;base64,{font_b64}') format('truetype'); }}
        """

    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        {font_css}
        
        /* Tipografías */
        h1, h2, h3 {{ font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }}
        
        /* Botones */
        .stButton > button {{ background-color: transparent; color: white; border: 2px solid white; border-radius: 15px; padding: 10px 20px; font-weight: bold; }}
        .stButton > button:hover {{ background-color: #D81B60; border-color: #D81B60; }}
        
        /* Inputs */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, 
        .stDateInput > div > div > input, .stTimeInput > div > div > input {{
            background-color: white !important; color: black !important; border-radius: 8px; border: none;
        }}
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{ display: none; }}

        /* Etiquetas */
        .label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; text-shadow: none !important; }}
        .label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}
        
        /* Efectos */
        .zoom-img {{ transition: transform 0.3s; }}
        .zoom-img:hover {{ transform: scale(1.1); }}
        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
        """, unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. MOTOR GRÁFICO (LAS 12 PLANTILLAS)
# ==============================================================================

# Herramienta auxiliar para sombras en texto
def dibujar_texto_sombra(draw, texto, x, y, fuente, color="white", sombra="black", offset=(5,5), anchor="mm"):
    draw.text((x+offset[0], y+offset[1]), texto, font=fuente, fill=sombra, anchor=anchor)
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)

# --- PLANTILLA TIPO 1 (YA PROGRAMADA) ---
def generar_tipo_1(fondo, titulo, desc1, fecha1, hora1, lugar, area):
    # 1. Base
    W, H = 2400, 3000
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    
    # 2. Sombra inferior (Oscurecer para leer)
    overlay = Image.new('RGBA', (W, H), (0,0,0,0))
    d_over = ImageDraw.Draw(overlay)
    for y in range(int(H*0.4), H):
        alpha = int(255 * ((y - H*0.4)/(H*0.6)))
        d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.8)))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 3. Fuentes
    try:
        f_tit = ImageFont.truetype("Canaro-Black.ttf", 250)
        f_desc = ImageFont.truetype("Canaro-Medium.ttf", 110)
        f_dato = ImageFont.truetype("Canaro-Bold.ttf", 90)
    except:
        f_tit = f_desc = f_dato = ImageFont.load_default()

    # 4. Elementos
    # Logo Superior
    if os.path.exists("logo_superior.png"):
        logo = Image.open("logo_superior.png").convert("RGBA")
        ratio = 1000 / logo.width
        logo = logo.resize((1000, int(logo.height*ratio)), Image.Resampling.LANCZOS)
        img.paste(logo, (int((W-1000)/2), 150), logo)

    # Título
    dibujar_texto_sombra(draw, titulo, W/2, 900, f_tit)

    # Descripción 1
    lines = textwrap.wrap(desc1, width=30)
    y_txt = 1350
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_txt, f_desc)
        y_txt += 130
        
    # Fecha y Hora (Caja Rosa)
    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    txt_fecha = f"📅 {fecha1.day} de {meses[fecha1.month]}   |   🕒 {hora1.strftime('%H:%M')}"
    
    y_info = y_txt + 200
    bbox = draw.textbbox((0,0), txt_fecha, font=f_dato)
    w_bx = bbox[2]-bbox[0]
    draw.rounded_rectangle([(W-w_bx)/2 - 40, y_info-60, (W+w_bx)/2 + 40, y_info+60], radius=30, fill="#D81B60")
    draw.text((W/2, y_info), txt_fecha, font=f_dato, fill="white", anchor="mm")
    
    # Lugar
    dibujar_texto_sombra(draw, f"📍 {lugar}", W/2, y_info + 200, f_dato)

    # Firma Jota
    if os.path.exists("firma_jota.png"):
        firma = Image.open("firma_jota.png").convert("RGBA")
        ratio = 600 / firma.width
        firma = firma.resize((600, int(firma.height*ratio)), Image.Resampling.LANCZOS)
        img.paste(firma, (100, H - firma.height - 100), firma)

    return img

# --- RESTO DE PLANTILLAS (PLACEHOLDERS) ---
# Aquí iremos pegando el código de cada una cuando las diseñemos

def generar_tipo_2(fondo, titulo, desc1, desc2, fecha1, hora1, lugar, area):
    # Lógica: 2 Párrafos, 1 Fecha, 0 Colab
    return fondo # Retorna fondo limpio por ahora

def generar_tipo_3(fondo, titulo, desc1, fecha1, fecha2, hora1, hora2, lugar, area):
    # Lógica: 1 Párrafo, 2 Fechas, 0 Colab
    return fondo

def generar_tipo_4(fondo, titulo, desc1, desc2, fecha1, fecha2, hora1, hora2, lugar, area):
    # Lógica: 2 Párrafos, 2 Fechas, 0 Colab
    return fondo

def generar_tipo_5(fondo, titulo, desc1, fecha1, hora1, lugar, collab1, area):
    # Lógica: 1 Párrafo, 1 Fecha, 1 Colab
    return fondo

def generar_tipo_6(fondo, titulo, desc1, desc2, fecha1, hora1, lugar, collab1, area):
    # Lógica: 2 Párrafos, 1 Fecha, 1 Colab
    return fondo

def generar_tipo_7(fondo, titulo, desc1, fecha1, fecha2, hora1, hora2, lugar, collab1, area):
    # Lógica: 1 Párrafo, 2 Fechas, 1 Colab
    return fondo

def generar_tipo_8(fondo, titulo, desc1, desc2, fecha1, fecha2, hora1, hora2, lugar, collab1, area):
    # Lógica: 2 Párrafos, 2 Fechas, 1 Colab
    return fondo

def generar_tipo_9(fondo, titulo, desc1, fecha1, hora1, lugar, collab1, collab2, area):
    # Lógica: 1 Párrafo, 1 Fecha, 2 Colab
    return fondo

def generar_tipo_10(fondo, titulo, desc1, desc2, fecha1, hora1, lugar, collab1, collab2, area):
    # Lógica: 2 Párrafos, 1 Fecha, 2 Colab
    return fondo

def generar_tipo_11(fondo, titulo, desc1, fecha1, fecha2, hora1, hora2, lugar, collab1, collab2, area):
    # Lógica: 1 Párrafo, 2 Fechas, 2 Colab
    return fondo

def generar_tipo_12(fondo, titulo, desc1, desc2, fecha1, fecha2, hora1, hora2, lugar, collab1, collab2, area):
    # Lógica: 2 Párrafos, 2 Fechas, 2 Colab
    return fondo


# ==============================================================================
# 3. CONTROLADOR MAESTRO (EL CEREBRO QUE ELIGE)
# ==============================================================================
def generar_flyer_automatico(datos):
    """
    Analiza los datos y decide cuál de las 12 funciones llamar.
    """
    # 1. Analizar Variables
    tiene_desc2 = bool(datos['desc2'])
    tiene_fecha2 = bool(datos['fecha2'])
    num_colabs = len(datos['logos']) if datos['logos'] else 0
    
    fondo = datos['fondo'] # Ya viene en 2400x3000
    tit = "TE INVITA" # O datos['desc1'] si lo usas de titulo
    
    # 2. ÁRBOL DE DECISIÓN (MATRIX DE 12 TIPOS)
    
    # --- GRUPO: SIN COLABORADORES ---
    if num_colabs == 0:
        if not tiene_desc2 and not tiene_fecha2:
            return generar_tipo_1(fondo, tit, datos['desc1'], datos['fecha1'], datos['hora1'], datos['lugar'], datos['area'])
        
        elif tiene_desc2 and not tiene_fecha2:
            return generar_tipo_2(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['hora1'], datos['lugar'], datos['area'])
            
        elif not tiene_desc2 and tiene_fecha2:
            return generar_tipo_3(fondo, tit, datos['desc1'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], datos['area'])
            
        elif tiene_desc2 and tiene_fecha2:
            return generar_tipo_4(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], datos['area'])

    # --- GRUPO: 1 COLABORADOR ---
    elif num_colabs == 1:
        c1 = datos['logos'][0]
        if not tiene_desc2 and not tiene_fecha2:
            return generar_tipo_5(fondo, tit, datos['desc1'], datos['fecha1'], datos['hora1'], datos['lugar'], c1, datos['area'])
            
        elif tiene_desc2 and not tiene_fecha2:
            return generar_tipo_6(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['hora1'], datos['lugar'], c1, datos['area'])
            
        elif not tiene_desc2 and tiene_fecha2:
            return generar_tipo_7(fondo, tit, datos['desc1'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], c1, datos['area'])
            
        elif tiene_desc2 and tiene_fecha2:
            return generar_tipo_8(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], c1, datos['area'])

    # --- GRUPO: 2 COLABORADORES ---
    elif num_colabs >= 2:
        c1 = datos['logos'][0]
        c2 = datos['logos'][1]
        if not tiene_desc2 and not tiene_fecha2:
            return generar_tipo_9(fondo, tit, datos['desc1'], datos['fecha1'], datos['hora1'], datos['lugar'], c1, c2, datos['area'])
            
        elif tiene_desc2 and not tiene_fecha2:
            return generar_tipo_10(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['hora1'], datos['lugar'], c1, c2, datos['area'])
            
        elif not tiene_desc2 and tiene_fecha2:
            return generar_tipo_11(fondo, tit, datos['desc1'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], c1, c2, datos['area'])
            
        elif tiene_desc2 and tiene_fecha2:
            return generar_tipo_12(fondo, tit, datos['desc1'], datos['desc2'], datos['fecha1'], datos['fecha2'], datos['hora1'], datos['hora2'], datos['lugar'], c1, c2, datos['area'])

    return fondo # Fallback


# ==============================================================================
# 4. INTERFAZ DE USUARIO (NAVEGACIÓN)
# ==============================================================================

# Logos superiores
if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

query_params = st.query_params
area_seleccionada = query_params.get("area", None)

# --- PÁGINA 1: INICIO ---
if not area_seleccionada:
    st.markdown("<h2 style='text-align: center;'>SELECCIONA EL DEPARTAMENTO:</h2>", unsafe_allow_html=True)
    st.write("---")
    col1, col_cultura, col_recreacion, col4 = st.columns([1, 2, 2, 1])

    with col_cultura:
        if os.path.exists("btn_cultura.png"):
            img_b64 = get_base64_of_bin_file("btn_cultura.png")
            st.markdown(f"""<a href="?area=Cultura" target="_self"><div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" class="zoom-img" width="100%"><div class="label-negro" style="color:white !important;">CULTURA</div></div></a>""", unsafe_allow_html=True)

    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            img_b64 = get_base64_of_bin_file("btn_recreacion.png")
            st.markdown(f"""<a href="?area=Recreación" target="_self"><div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" class="zoom-img" width="100%"><div class="label-negro" style="color:white !important;">RECREACIÓN</div></div></a>""", unsafe_allow_html=True)
            
    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
         if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=300)

# --- PÁGINA 2: FORMULARIO ---
elif area_seleccionada in ["Cultura", "Recreación"]:
    if st.button("⬅️ VOLVER AL INICIO"):
        st.query_params.clear()
        st.rerun()

    col_izq, col_der = st.columns([1, 2], gap="large")
    
    with col_izq:
        st.write("")
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=200)

    with col_der:
        st.markdown('<div class="label-negro">DESCRIPCIÓN</div>', unsafe_allow_html=True)
        st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
        
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        st.text_area("lbl_desc2", key="lbl_desc2", label_visibility="collapsed", placeholder="Información extra...", height=100)
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown('<div class="label-negro">FECHA INICIO</div>', unsafe_allow_html=True)
            st.date_input("lbl_fecha1", key="lbl_fecha1", label_visibility="collapsed", format="DD/MM/YYYY", value=None)
        with c_f2:
            st.markdown('<div class="label-negro">FECHA FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            st.date_input("lbl_fecha2", key="lbl_fecha2", label_visibility="collapsed", value=None, format="DD/MM/YYYY")
            
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown('<div class="label-negro">HORARIO INICIO</div>', unsafe_allow_html=True)
            st.time_input("lbl_hora1", key="lbl_hora1", label_visibility="collapsed", value=datetime.time(9, 00))
        with c_h2:
            st.markdown('<div class="label-negro">HORARIO FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            st.time_input("lbl_hora2", key="lbl_hora2", label_visibility="collapsed", value=None)
            
        st.markdown('<div class="label-negro">DIRECCIÓN</div>', unsafe_allow_html=True)
        st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")
        
        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR Y RECORTAR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("lbl_img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            st.info("✂️ Ajusta el recuadro rojo para que encaje en el flyer.")
            img_orig = Image.open(archivo_subido)
            img_crop = st_cropper(img_orig, realtime_update=True, box_color='#FF0000', aspect_ratio=(4, 5))
            # FORZAR HD
            img_hd = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.session_state['imagen_lista_para_flyer'] = img_hd
            st.write("✅ Imagen lista.")

        st.markdown('<div class="label-negro">LOGOS COLABORADORES <span class="label-blanco">(MÁX 2)</span></div>', unsafe_allow_html=True)
        st.file_uploader("lbl_logos", key="lbl_logos", accept_multiple_files=True, label_visibility="collapsed")
        
        st.write("")
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
            errores = []
            if not st.session_state.lbl_desc: errores.append("Falta la Descripción")
            if not st.session_state.lbl_fecha1: errores.append("Falta la Fecha de Inicio")
            if 'imagen_lista_para_flyer' not in st.session_state: errores.append("Falta recortar la Imagen")
            
            if errores:
                st.error(f"⚠️ {', '.join(errores)}")
            else:
                st.query_params["area"] = "Final"
                st.rerun()

# --- PÁGINA 3: RESULTADO ---
elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    col_arte, col_flyer, col_descarga = st.columns([1.3, 1.5, 0.8])
    
    with col_arte:
        st.write("") 
        if os.path.exists("mascota_pincel.png"): st.image("mascota_pincel.png", use_container_width=True)
        st.write("")
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=280)

    with col_flyer:
        # AQUÍ OCURRE LA MAGIA AUTOMÁTICA
        if 'imagen_lista_para_flyer' in st.session_state:
            
            # 1. Empaquetar datos para el Cerebro
            paquete_datos = {
                'fondo': st.session_state.imagen_lista_para_flyer,
                'desc1': st.session_state.lbl_desc,
                'desc2': st.session_state.lbl_desc2,
                'fecha1': st.session_state.lbl_fecha1,
                'fecha2': st.session_state.lbl_fecha2,
                'hora1': st.session_state.lbl_hora1,
                'hora2': st.session_state.lbl_hora2,
                'lugar': st.session_state.lbl_dir,
                'logos': st.session_state.get('lbl_logos', []),
                'area': area_seleccionada
            }
            
            # 2. El Cerebro elige el Tipo (1 al 12) y lo genera
            flyer_final = generar_flyer_automatico(paquete_datos)
            
            # 3. Mostrar y preparar descarga
            st.image(flyer_final, caption="Diseño Generado", use_container_width=True)
            
            buf = io.BytesIO()
            flyer_final.save(buf, format="PNG")
            byte_im = buf.getvalue()
        else:
            st.error("Error: Datos perdidos. Vuelve al inicio.")

    with col_descarga:
        st.markdown("<h3 style='text-align: center; font-size: 20px;'>OTRAS OPCIONES</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op2", use_container_width=True)
        with c2: st.image("https://via.placeholder.com/100/CCCCCC/FFFFFF?text=Op3", use_container_width=True)
        st.write("---")
        
        if os.path.exists("mascota_final.png"): st.image("mascota_final.png", width=220) 
        
        if 'byte_im' in locals():
            st.download_button(label="⬇️ DESCARGAR", data=byte_im, file_name="flyer_azuay.png", mime="image/png", use_container_width=True)
            
    st.write("---")
    if st.button("🔄 CREAR NUEVO"):
        st.query_params.clear()
        if 'imagen_lista_para_flyer' in st.session_state: del st.session_state['imagen_lista_para_flyer']
        st.rerun()
