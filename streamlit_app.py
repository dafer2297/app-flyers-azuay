import streamlit as st
import base64
import os
import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper

# ==============================================================================
# 1. CONFIGURACIÓN E IMPORTACIÓN DE ESTILOS
# ==============================================================================
st.set_page_config(page_title="Generador Flyers Azuay", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design():
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"""
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """

    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css += f"""@font-face {{ font-family: 'Canaro'; src: url('data:font/ttf;base64,{font_b64}') format('truetype'); }}"""

    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        {font_css}
        h1, h2, h3 {{ font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }}
        .stButton > button {{ background-color: transparent; color: white; border: 2px solid white; border-radius: 15px; padding: 10px 20px; font-weight: bold; }}
        .stButton > button:hover {{ background-color: #D81B60; border-color: #D81B60; }}
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, 
        .stDateInput > div > div > input, .stTimeInput > div > div > input, .stSelectbox > div > div > div {{
            background-color: white !important; color: black !important; border-radius: 8px; border: none;
        }}
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label, .stSelectbox label {{ display: none; }}
        .label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; }}
        .label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}
        .contador-ok {{ color: #C6FF00 !important; font-weight: bold; font-size: 14px; }}
        .contador-mal {{ color: #FF5252 !important; font-weight: bold; font-size: 14px; }}
        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
        """, unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. HERRAMIENTAS GRÁFICAS (UTILS)
# ==============================================================================

def dibujar_texto_sombra(draw, texto, x, y, fuente, color="white", sombra="black", offset=(12,12), anchor="mm"):
    draw.text((x+offset[0], y+offset[1]), texto, font=fuente, fill=sombra, anchor=anchor)
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)

def ruta_abs(nombre_archivo):
    return os.path.join(os.getcwd(), nombre_archivo)

def obtener_mes_abbr(numero_mes):
    meses = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}
    return meses.get(numero_mes, "")

def obtener_mes_nombre(numero_mes):
    meses = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    return meses.get(numero_mes, "")

def obtener_dia_semana(fecha):
    dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    return dias[fecha.weekday()]

def resize_por_alto(img, alto_objetivo):
    ratio = alto_objetivo / img.height
    ancho_nuevo = int(img.width * ratio)
    return img.resize((ancho_nuevo, alto_objetivo), Image.Resampling.LANCZOS)

# ==============================================================================
# 3. GENERADORES DE FLYERS (TIPO 1)
# ==============================================================================

# --- VARIANTE 1: CLÁSICA (Esquinas) ---
def generar_tipo1_v1(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 1. Sombra
    if os.path.exists("flyer_sombra.png"):
        sombra = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra, (0,0), sombra)
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

    # 2. Fuentes
    try:
        f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220)
        f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 350)
        f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 200)
        f_extra = ImageFont.truetype(ruta_abs("Canaro-ExtraBold.ttf"), 110) if os.path.exists("Canaro-ExtraBold.ttf") else ImageFont.load_default()
        f_desc = ImageFont.truetype(ruta_abs("Canaro-SemiBold.ttf"), 100) if os.path.exists("Canaro-SemiBold.ttf") else ImageFont.load_default()
        f_med = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), 75) if os.path.exists("Canaro-Medium.ttf") else ImageFont.load_default()
    except:
        f_invita = f_dia_box = f_mes_box = f_extra = f_desc = f_med = ImageFont.load_default()

    # 3. Logos Superiores
    y_logos = 150
    margin_logos = 200
    if os.path.exists("flyer_logo.png"): # Prefectura
        logo = Image.open("flyer_logo.png").convert("RGBA")
        logo = resize_por_alto(logo, 378)
        for _ in range(2): img.paste(logo, (margin_logos, y_logos), logo)
    if os.path.exists("flyer_firma.png"): # Jota
        firma = Image.open("flyer_firma.png").convert("RGBA")
        firma = resize_por_alto(firma, 378)
        img.paste(firma, (W - firma.width - margin_logos, y_logos + 20), firma)

    # 4. Texto Central
    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))
    
    desc_txt = datos['desc1']
    s_desc = 110 if len(desc_txt) <= 75 else (90 if len(desc_txt) <= 150 else 75)
    try: f_desc_uso = ImageFont.truetype(ruta_abs("Canaro-SemiBold.ttf"), s_desc)
    except: f_desc_uso = f_desc
    
    wrap_w = 35 if s_desc == 110 else (45 if s_desc == 90 else 55)
    lines = textwrap.wrap(desc_txt, width=wrap_w)
    y_desc = 1030
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc_uso, offset=(8,8))
        y_desc += int(s_desc * 1.1)

    # 5. Caja Fecha (Izq)
    MARGIN_UNIV = 180
    h_caja = 645
    y_baseline = H - 150
    y_box = y_baseline - 170 - h_caja
    
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (MARGIN_UNIV, y_box), caja)
    else:
        draw.rectangle([MARGIN_UNIV, y_box, MARGIN_UNIV+645, y_box+645], fill="white")
    
    cx, cy = MARGIN_UNIV + 322, y_box + 322
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill="black", anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="black", anchor="mm")
    
    # Dia/Hora
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    s_hora = 80 if datos['hora2'] else 110
    try: f_hora_uso = ImageFont.truetype(ruta_abs("Canaro-ExtraBold.ttf"), s_hora)
    except: f_hora_uso = f_extra
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_baseline - 100, f_extra, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_baseline, f_hora_uso, offset=(8,8), anchor="mm")

    # 6. Ubicación (Der)
    lug_txt = datos['lugar']
    s_lug = 75 if len(lug_txt) < 45 else 60
    try: f_lug_uso = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lug_uso = f_med
    
    wrap_lug = 22 if s_lug == 75 else 28
    lines_lug = textwrap.wrap(lug_txt, width=wrap_lug)
    
    h_icon = 260
    w_icon = 100
    # Calculo posición
    line_h = int(s_lug * 1.1)
    tot_h = len(lines_lug) * line_h
    y_base_txt = y_baseline
    x_anchor = W - MARGIN_UNIV
    
    # Ancho maximo
    max_w = 0
    try: max_w = max([f_lug_uso.getlength(l) for l in lines_lug])
    except: max_w = 300
    
    x_start = x_anchor - max_w
    
    # Icono
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA")
        icon = resize_por_alto(icon, h_icon)
        w_icon = icon.width
        y_mid = y_base_txt - (tot_h/2)
        img.paste(icon, (int(x_start - w_icon - 30), int(y_mid - h_icon/2)), icon)
    
    # Texto
    curr_y = y_base_txt - tot_h + line_h
    for l in lines_lug:
        dibujar_texto_sombra(draw, l, x_start, curr_y, f_lug_uso, anchor="ls", offset=(4,4))
        curr_y += line_h

    return img.convert("RGB")

# --- VARIANTE 2: MODERNA (Apilada Izq) ---
def generar_tipo1_v2(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 1. Sombra
    if os.path.exists("flyer_sombra.png"):
        sombra = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra, (0,0), sombra)
    
    # 2. Fuentes (Mismas)
    try:
        f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220)
        f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 350)
        f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 200)
        f_extra = ImageFont.truetype(ruta_abs("Canaro-ExtraBold.ttf"), 110) if os.path.exists("Canaro-ExtraBold.ttf") else ImageFont.load_default()
        f_med = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), 75) if os.path.exists("Canaro-Medium.ttf") else ImageFont.load_default()
    except:
        f_invita = f_dia_box = f_mes_box = f_extra = f_med = ImageFont.load_default()

    # 3. Logo Prefectura (Centro Arriba)
    if os.path.exists("flyer_logo.png"): 
        logo = Image.open("flyer_logo.png").convert("RGBA")
        logo = resize_por_alto(logo, 378)
        x_logo = (W - logo.width) // 2
        for _ in range(2): img.paste(logo, (x_logo, 150), logo)

    # 4. Texto Central
    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))
    
    desc_txt = datos['desc1']
    s_desc = 110 if len(desc_txt) <= 75 else (90 if len(desc_txt) <= 150 else 75)
    try: f_desc_uso = ImageFont.truetype(ruta_abs("Canaro-SemiBold.ttf"), s_desc)
    except: f_desc_uso = ImageFont.load_default()
    
    wrap_w = 35 if s_desc == 110 else (45 if s_desc == 90 else 55)
    lines = textwrap.wrap(desc_txt, width=wrap_w)
    y_desc = 1030
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc_uso, offset=(8,8))
        y_desc += int(s_desc * 1.1)

    # CONSTANTES BASE
    SIDE_MARGIN = 180
    Y_BOTTOM_BASELINE = H - 150

    # 5. Logo Jota (Abajo Derecha)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA")
        firma = resize_por_alto(firma, 378)
        # Ajuste visual base (+50px)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    # 6. Ubicación (Abajo Izquierda)
    lug_txt = datos['lugar']
    s_lug = 75 if len(lug_txt) < 45 else 60
    try: f_lug_uso = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lug_uso = f_med
    
    wrap_lug = 22 if s_lug == 75 else 28
    lines_lug = textwrap.wrap(lug_txt, width=wrap_lug)
    
    h_icon = 260
    w_icon = 100
    line_h = int(s_lug * 1.1)
    tot_h = len(lines_lug) * line_h
    
    y_base_txt = Y_BOTTOM_BASELINE
    # El texto empieza a la derecha del icono
    x_txt_start = SIDE_MARGIN + 130 
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA")
        icon = resize_por_alto(icon, h_icon)
        w_icon = icon.width
        y_mid = y_base_txt - (tot_h/2)
        # Icono pegado al margen izquierdo
        img.paste(icon, (SIDE_MARGIN, int(y_mid - h_icon/2)), icon)
        x_txt_start = SIDE_MARGIN + w_icon + 30

    curr_y = y_base_txt - tot_h + line_h
    for l in lines_lug:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lug_uso, anchor="ls", offset=(4,4))
        curr_y += line_h

    # 7. Caja Fecha (Encima Ubicación)
    # Calculamos Y base de la hora para que no choque con la ubicación
    # Asumimos que el bloque ubicación ocupa espacio, subimos ~250px
    y_linea_hora = y_base_txt - tot_h - 150
    h_caja = 645
    y_box = y_linea_hora - 170 - h_caja
    x_box = SIDE_MARGIN

    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
    else:
        draw.rectangle([x_box, y_box, x_box+645, y_box+645], fill="white")
    
    cx, cy = x_box + 322, y_box + 322
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill="black", anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="black", anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    s_hora = 80 if datos['hora2'] else 110
    try: f_hora_uso = ImageFont.truetype(ruta_abs("Canaro-ExtraBold.ttf"), s_hora)
    except: f_hora_uso = f_extra

    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_linea_hora - 100, f_extra, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_linea_hora, f_hora_uso, offset=(8,8), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 4. INTERFAZ DE USUARIO (LÓGICA PRINCIPAL)
# ==============================================================================

if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

query_params = st.query_params
area_seleccionada = query_params.get("area", None)

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

elif area_seleccionada in ["Cultura", "Recreación"]:
    if st.button("⬅️ VOLVER AL INICIO"):
        st.query_params.clear()
        st.rerun()

    # --- SELECTOR DE TIPO DE FLYER ---
    # Aquí irán los 12 tipos. Por ahora solo el 1 es funcional.
    tipos_opciones = {
        1: "Tipo 1: 1 Párrafo, 1 Fecha, 0 Colab",
        2: "Tipo 2: 2 Párrafos, 1 Fecha, 0 Colab",
        3: "Tipo 3: 1 Párrafo, 2 Fechas, 0 Colab",
        # ... hasta el 12 ...
    }
    
    st.markdown('<div class="label-negro">SELECCIONA EL TIPO DE FLYER:</div>', unsafe_allow_html=True)
    tipo_sel = st.selectbox("tipo_flyer", options=list(tipos_opciones.keys()), format_func=lambda x: tipos_opciones[x], label_visibility="collapsed")

    st.write("---")

    col_izq, col_der = st.columns([1, 2], gap="large")
    with col_izq:
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=200)

    with col_der:
        # --- CAMPOS DINÁMICOS SEGÚN TIPO ---
        
        if tipo_sel == 1: # LOGICA TIPO 1
            st.markdown('<div class="label-negro">DESCRIPCIÓN</div>', unsafe_allow_html=True)
            desc1 = st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
            
            c_f1, c_h = st.columns(2)
            with c_f1:
                st.markdown('<div class="label-negro">FECHA INICIO</div>', unsafe_allow_html=True)
                fecha1 = st.date_input("lbl_fecha1", key="lbl_fecha1", label_visibility="collapsed", format="DD/MM/YYYY", value=None)
            
            c_h1, c_h2 = st.columns(2)
            with c_h1:
                st.markdown('<div class="label-negro">HORA INICIO</div>', unsafe_allow_html=True)
                hora1 = st.time_input("lbl_hora1", key="lbl_hora1", label_visibility="collapsed", value=datetime.time(9, 00))
            with c_h2:
                st.markdown('<div class="label-negro">HORA FIN (Opcional)</div>', unsafe_allow_html=True)
                hora2 = st.time_input("lbl_hora2", key="lbl_hora2", label_visibility="collapsed", value=None)
                
            st.markdown('<div class="label-negro">DIRECCIÓN</div>', unsafe_allow_html=True)
            lugar = st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")

        # --- SECCIÓN DE IMAGEN ---
        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("lbl_img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte.")
            img_crop = st_cropper(img_orig, realtime_update=True, box_color='#FF0000', aspect_ratio=(4, 5), should_resize_image=False)
            st.session_state['imagen_lista'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Imagen lista.")

        st.write("")
        
        if st.button("✨ GENERAR FLYERS ✨", type="primary", use_container_width=True):
            if tipo_sel == 1:
                errores = []
                if not st.session_state.lbl_desc: errores.append("Falta Descripción")
                if not st.session_state.lbl_fecha1: errores.append("Falta Fecha")
                if 'imagen_lista' not in st.session_state: errores.append("Falta Imagen")
                
                if errores:
                    st.error(f"⚠️ {', '.join(errores)}")
                else:
                    # Guardamos datos limpios para el generador
                    st.session_state['datos_finales'] = {
                        'tipo': 1,
                        'fondo': st.session_state['imagen_lista'],
                        'desc1': st.session_state.lbl_desc,
                        'fecha1': st.session_state.lbl_fecha1,
                        'fecha2': None, # Tipo 1 no tiene fecha 2
                        'hora1': st.session_state.lbl_hora1,
                        'hora2': st.session_state.lbl_hora2,
                        'lugar': st.session_state.lbl_dir,
                        'logos': [] # Tipo 1 no tiene colab
                    }
                    st.query_params["area"] = "Final"
                    st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡RESULTADOS!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    if 'datos_finales' not in st.session_state:
        st.warning("No hay datos.")
        if st.button("Volver"):
            st.query_params.clear()
            st.rerun()
    else:
        datos = st.session_state['datos_finales']
        tipo = datos['tipo']
        
        # COLUMNAS PARA MOSTRAR LAS OPCIONES
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.markdown("<h3 style='text-align: center;'>Opción 1 (Clásica)</h3>", unsafe_allow_html=True)
            if tipo == 1:
                img_v1 = generar_tipo1_v1(datos)
                st.image(img_v1, use_container_width=True)
                buf1 = io.BytesIO()
                img_v1.save(buf1, format="PNG")
                st.download_button("⬇️ Descargar Opción 1", data=buf1.getvalue(), file_name="flyer_tipo1_v1.png", mime="image/png", use_container_width=True)

        with col_v2:
            st.markdown("<h3 style='text-align: center;'>Opción 2 (Moderna)</h3>", unsafe_allow_html=True)
            if tipo == 1:
                img_v2 = generar_tipo1_v2(datos)
                st.image(img_v2, use_container_width=True)
                buf2 = io.BytesIO()
                img_v2.save(buf2, format="PNG")
                st.download_button("⬇️ Descargar Opción 2", data=buf2.getvalue(), file_name="flyer_tipo1_v2.png", mime="image/png", use_container_width=True)

    st.write("---")
    if st.button("🔄 CREAR NUEVO"):
        st.query_params.clear()
        keys = ['imagen_lista', 'datos_finales', 'lbl_desc', 'lbl_dir']
        for k in keys:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
