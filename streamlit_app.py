import streamlit as st
import base64
import os
import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper

# ==============================================================================
# 1. CONFIGURACIÓN
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
        .stDateInput > div > div > input, .stTimeInput > div > div > input {{
            background-color: white !important; color: black !important; border-radius: 8px; border: none;
        }}
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{ display: none; }}
        .label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; text-shadow: none !important; }}
        .label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}
        .contador-ok {{ color: #C6FF00 !important; font-weight: bold; font-size: 14px; }}
        .contador-mal {{ color: #FF5252 !important; font-weight: bold; font-size: 14px; }}
        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
        """, unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. MOTOR GRÁFICO (LÓGICA DE PRECISIÓN)
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

# --- GENERADOR PLANTILLA TIPO 1 (Clásica / Variante 1) ---
def generar_tipo_1_v1(datos):
    fondo = datos['fondo'].copy()
    desc1 = datos['desc1']
    fecha1 = datos['fecha1']
    hora1 = datos['hora1']
    hora2 = datos['hora2']
    lugar = datos['lugar']
    
    W, H = 2400, 3000
    SIDE_MARGIN = 180 
    Y_BOTTOM_BASELINE = H - 150

    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 1. Sombra
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA")
        if sombra_img.size != (W, H):
            sombra_img = sombra_img.resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
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
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        f_dia_semana = ImageFont.truetype(path_extra, 110)
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default()
        path_desc = None

    # 3. Cabecera
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    y_desc = y_titulo + 180 
    chars_desc = len(desc1)
    if chars_desc <= 75: size_desc_val = 110 
    elif chars_desc <= 150: size_desc_val = 90 
    else: size_desc_val = 75
    
    if path_desc and os.path.exists(path_desc): f_desc = ImageFont.truetype(path_desc, size_desc_val)
    else: f_desc = ImageFont.load_default()
    
    width_wrap = 35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55)
    lines = textwrap.wrap(desc1, width=width_wrap)
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.1)

    # 4. Caja Fecha
    h_caja = 645
    x_box = SIDE_MARGIN 
    y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    
    str_hora = hora1.strftime('%H:%M %p')
    if hora2: str_hora += f" a {hora2.strftime('%H:%M %p')}"
    size_hora = 110
    if hora2: size_hora = 80 
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA")
        caja = resize_por_alto(caja, h_caja)
        img.paste(caja, (x_box, y_box), caja)
        w_caja = caja.width
        color_fecha = "white"
    else:
        w_caja = 645
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"
        
    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia_num = str(fecha1.day)
    mes_txt = obtener_mes_abbr(fecha1.month)
    dia_sem = obtener_dia_semana(fecha1)
    
    draw.text((cx, cy - 50), dia_num, font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), mes_txt, font=f_mes_box, fill=color_fecha, anchor="mm")
    
    y_info_dia = Y_BOTTOM_BASELINE
    dibujar_texto_sombra(draw, dia_sem, cx, y_info_dia - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_info_dia, f_hora, offset=(8,8), anchor="mm")

    # 5. Ubicación
    len_lug = len(lugar)
    if len_lug < 45: s_lug = 75
    else: s_lug = 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()

    wrap_width = 22 if s_lug == 75 else 28
    lines_loc = textwrap.wrap(lugar, width=wrap_width)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    y_base_txt = Y_BOTTOM_BASELINE
    x_txt_anchor = W - SIDE_MARGIN
    
    max_line_width = 0
    try:
        if lines_loc: max_line_width = max([f_lugar.getlength(line) for line in lines_loc])
    except: max_line_width = 300

    x_text_start = x_txt_anchor - max_line_width
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA")
        icon = resize_por_alto(icon, h_icon)
        w_icon = icon.width
        y_text_center = y_base_txt - (total_text_height / 2)
        y_icon = y_text_center - (h_icon / 2)
        x_icon = x_text_start - w_icon - 30 
        img.paste(icon, (int(x_icon), int(y_icon)), icon)
    else:
        y_text_center = y_base_txt - (total_text_height / 2)
        y_icon = y_text_center - (h_icon / 2)
        x_icon = x_text_start - 100 - 30 
        dibujar_texto_sombra(draw, "📍", x_icon + 50, y_icon + h_icon/2, f_lugar, anchor="mm")

    current_y_txt = y_base_txt - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, current_y_txt, f_lugar, anchor="ls", offset=(4,4))
        current_y_txt += line_height

    # 6. Logos
    y_logos = 150
    margin_logos = 200 
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA")
        logo = resize_por_alto(logo, 378)
        for _ in range(2): img.paste(logo, (margin_logos, y_logos), logo)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA")
        firma = resize_por_alto(firma, 378)
        img.paste(firma, (W - firma.width - margin_logos, y_logos + 20), firma)

    return img.convert("RGB")

# ==============================================================================
# 4. INTERFAZ DE USUARIO
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

    col_izq, col_der = st.columns([1, 2], gap="large")
    with col_izq:
        st.write("")
        icono = "icono_cultura.png" if area_seleccionada == "Cultura" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=200)

    with col_der:
        st.markdown('<div class="label-negro">DESCRIPCIÓN 1</div>', unsafe_allow_html=True)
        desc1 = st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
        
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 (OPCIONAL)</div>', unsafe_allow_html=True)
        desc2 = st.text_area("lbl_desc2", key="lbl_desc2", label_visibility="collapsed", placeholder="", height=100)
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown('<div class="label-negro">FECHA INICIO</div>', unsafe_allow_html=True)
            fecha1 = st.date_input("lbl_fecha1", key="lbl_fecha1", label_visibility="collapsed", format="DD/MM/YYYY", value=None)
        with c_f2:
            st.markdown('<div class="label-negro">FECHA FINAL (Opcional)</div>', unsafe_allow_html=True)
            fecha2 = st.date_input("lbl_fecha2", key="lbl_fecha2", label_visibility="collapsed", value=None, format="DD/MM/YYYY")
            
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown('<div class="label-negro">HORARIO INICIO</div>', unsafe_allow_html=True)
            hora1 = st.time_input("lbl_hora1", key="lbl_hora1", label_visibility="collapsed", value=datetime.time(9, 00))
        with c_h2:
            st.markdown('<div class="label-negro">HORARIO FINAL (Opcional)</div>', unsafe_allow_html=True)
            hora2 = st.time_input("lbl_hora2", key="lbl_hora2", label_visibility="collapsed", value=None)
            
        st.markdown('<div class="label-negro">DIRECCIÓN</div>', unsafe_allow_html=True)
        lugar = st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")

        st.markdown('<div class="label-negro">LOGOS COLABORADORES (Opcional)</div>', unsafe_allow_html=True)
        logos = st.file_uploader("lbl_logos", key="lbl_logos", accept_multiple_files=True, label_visibility="collapsed")

        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("lbl_img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte.")
            img_crop = st_cropper(
                img_orig, 
                realtime_update=True, 
                box_color='#FF0000', 
                aspect_ratio=(4, 5),
                should_resize_image=False 
            )
            st.session_state['imagen_lista_para_flyer'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Imagen lista.")

        st.write("")
        
        if st.button("✨ GENERAR FLYERS ✨", type="primary", use_container_width=True):
            errores = []
            if not st.session_state.lbl_desc: errores.append("Falta Descripción 1")
            if not st.session_state.lbl_fecha1: errores.append("Falta Fecha Inicio")
            if 'imagen_lista_para_flyer' not in st.session_state: errores.append("Falta Imagen de Fondo")
            
            if errores:
                st.error(f"⚠️ {', '.join(errores)}")
            else:
                # DETECCIÓN AUTOMÁTICA DE TIPO (1-12)
                has_desc2 = bool(st.session_state.lbl_desc2.strip())
                has_fecha2 = st.session_state.lbl_fecha2 is not None
                num_colabs = len(st.session_state.get('lbl_logos', []))
                
                tipo_id = 0
                
                # Reglas exactas:
                if num_colabs == 0:
                    if not has_desc2 and not has_fecha2: tipo_id = 1
                    elif has_desc2 and not has_fecha2: tipo_id = 2
                    elif not has_desc2 and has_fecha2: tipo_id = 3
                    elif has_desc2 and has_fecha2: tipo_id = 4
                elif num_colabs == 1:
                    if not has_desc2 and not has_fecha2: tipo_id = 5
                    elif has_desc2 and not has_fecha2: tipo_id = 6
                    elif not has_desc2 and has_fecha2: tipo_id = 7
                    elif has_desc2 and has_fecha2: tipo_id = 8
                elif num_colabs >= 2:
                    if not has_desc2 and not has_fecha2: tipo_id = 9
                    elif has_desc2 and not has_fecha2: tipo_id = 10
                    elif not has_desc2 and has_fecha2: tipo_id = 11
                    elif has_desc2 and has_fecha2: tipo_id = 12

                st.session_state['datos_finales'] = {
                    'tipo_id': tipo_id,
                    'fondo': st.session_state['imagen_lista_para_flyer'],
                    'desc1': st.session_state.lbl_desc,
                    'desc2': st.session_state.lbl_desc2,
                    'fecha1': st.session_state.lbl_fecha1,
                    'fecha2': st.session_state.lbl_fecha2,
                    'hora1': st.session_state.lbl_hora1,
                    'hora2': st.session_state.lbl_hora2,
                    'lugar': st.session_state.lbl_dir,
                    'logos': st.session_state.get('lbl_logos', [])
                }
                st.query_params["area"] = "Final"
                st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    if 'datos_finales' not in st.session_state:
        st.warning("⚠️ No hay datos. Vuelve al inicio.")
        if st.button("Volver al Inicio"):
            st.query_params.clear()
            st.rerun()
    else:
        datos = st.session_state['datos_finales']
        tipo = datos['tipo_id']
        
        st.success(f"✅ Se ha detectado automáticamente el TIPO {tipo}")
        
        # Muestra resultados según el tipo detectado
        col_v1, col_v2 = st.columns(2)
        
        if tipo == 1:
            with col_v1:
                st.markdown("<h3 style='text-align: center;'>Diseño Generado</h3>", unsafe_allow_html=True)
                img_v1 = generar_tipo_1_v1(datos)
                st.image(img_v1, use_container_width=True)
                buf1 = io.BytesIO()
                img_v1.save(buf1, format="PNG")
                st.download_button("⬇️ DESCARGAR FLYER", data=buf1.getvalue(), file_name="flyer_azuay_tipo1.png", mime="image/png", use_container_width=True)
        else:
            st.info(f"🚧 La plantilla para el TIPO {tipo} (ej. con Colaboradores o 2 Fechas) está en construcción. Por favor prueba ingresando datos de TIPO 1 (1 Descripción, 1 Fecha, 0 Logos).")

    st.write("---")
    if st.button("🔄 CREAR NUEVO"):
        st.query_params.clear()
        keys_borrar = ['imagen_lista_para_flyer', 'datos_finales', 'lbl_desc', 'lbl_desc2', 'lbl_dir']
        for k in keys_borrar:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
