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

def img_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

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
        
        div[data-testid="stButton"] button[kind="secondary"] {{
            background-color: white;
            color: #1E88E5;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: auto;
        }}
        div[data-testid="stButton"] button[kind="secondary"]:hover {{
            background-color: #f0f0f0;
            transform: scale(1.1);
            color: #1565C0;
        }}
        
        div[data-testid="stButton"] button[kind="primary"] {{
            background-color: transparent;
            color: white;
            border: 2px solid white;
            border-radius: 15px;
            width: 100%;
            height: auto;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 16px;
            box-shadow: none;
        }}
        div[data-testid="stButton"] button[kind="primary"]:hover {{
            background-color: #D81B60;
            border-color: #D81B60;
            transform: none;
        }}

        .stTextInput > div > div > input, .stTextArea > div > div > textarea, 
        .stDateInput > div > div > input, .stTimeInput > div > div > input {{
            background-color: white !important; color: black !important; border-radius: 8px; border: none;
        }}
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{ display: none; }}
        
        .label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; }}
        .label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}
        
        .label-menu {{ 
            font-family: 'Canaro', sans-serif; 
            font-weight: bold; 
            font-size: 20px; 
            color: white !important; 
            margin-top: 10px; 
            text-transform: uppercase;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.5);
            text-decoration: none !important;
        }}
        
        a {{ text-decoration: none !important; }}
        a img {{ border: none !important; outline: none !important; box-shadow: none !important; }}
        
        .zoom-hover {{ transition: transform 0.2s; cursor: pointer; }}
        .zoom-hover:hover {{ transform: scale(1.05); }}

        #MainMenu, footer, header {{ visibility: hidden; }}
        </style>
        """, unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. MOTOR GRÁFICO
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
# 3. GENERADORES DE PLANTILLAS TIPO 1
# ==============================================================================

def generar_tipo_1(datos):
    # --- TIPO 1 VARIANTE 1 (CLÁSICA) ---
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

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

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    size_desc_val = 110 if chars_desc <= 75 else (90 if chars_desc <= 150 else 75)
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    
    wrap_width = 35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55)
    
    for line in textwrap.wrap(desc1, width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    # FECHA IZQUIERDA ABAJO (FIJA)
    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
        
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, Y_BOTTOM_BASELINE - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, Y_BOTTOM_BASELINE, f_hora, offset=(8,8), anchor="mm")

    # UBICACIÓN DERECHA ABAJO (FIJA)
    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    y_base_txt = Y_BOTTOM_BASELINE
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([f_lugar.getlength(l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 30), int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    # LOGOS ARRIBA
    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) # IZQUIERDA
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) # DERECHA

    return img.convert("RGB")

def generar_tipo_1_v2(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)

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

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    size_desc_val = 110 if chars_desc <= 75 else (90 if chars_desc <= 150 else 75)
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=(35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55))):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height = int(s_lug * 1.1); total_text_height = len(lines_loc) * line_height
    x_txt_start = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 300 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_linea_hora - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_linea_hora, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")

def generar_tipo_1_v3(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

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

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 115:
        s_desc = 110; wrap_w = 18
    else:
        s_desc = 90; wrap_w = 22
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1150 
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls"); y_desc += int(s_desc * 1.1)

    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
        
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, Y_BOTTOM_BASELINE - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, Y_BOTTOM_BASELINE, f_hora, offset=(8,8), anchor="mm")

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    y_base_txt = Y_BOTTOM_BASELINE
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([f_lugar.getlength(l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 30), int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) # IZQUIERDA
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) # DERECHA

    return img.convert("RGB")

def generar_tipo_1_v4(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

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

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # TITULO IZQUIERDA
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    
    # --- 4 NIVELES DE TEXTO (V4) ---
    if chars_desc < 50:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 90:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 90; wrap_w = 22
    else:
        s_desc = 75; wrap_w = 25
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    
    # Y_DESC 1070
    y_desc = 1070 
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls"); y_desc += int(s_desc * 1.1)

    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height = int(s_lug * 1.1); total_text_height = len(lines_loc) * line_height
    x_txt_start = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    # FECHA BAJADA (-210)
    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 210 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_linea_hora - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_linea_hora, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 4. GENERADORES DE PLANTILLAS TIPO 2
# ==============================================================================

# --- TIPO 2: PLANTILLA 1 (T2_V1) ---
def generar_tipo_2_v1(datos):
    # COPIA EXACTA DE T1_V1 + DESC 2
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 1. Fondo Oscuro
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
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

    # 3. Logo Superior (Igual a T1_V1 - Prefectura IZQ, Firma DER)
    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) # IZQUIERDA
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) # DERECHA

    # 4. Título "INVITA" (Centrado - T1 Base)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 5. Descripción 1 (Centrada - T1 Base)
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    size_desc_val = 110 if chars_desc <= 75 else (90 if chars_desc <= 150 else 75)
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=(35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55))):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    # 6. Bloque Inferior (Fecha Izq + Ubicación Der)
    
    # FECHA IZQUIERDA ABAJO (FIJA)
    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_hora = 110
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
    
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, Y_BOTTOM_BASELINE - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, Y_BOTTOM_BASELINE, f_hora, offset=(8,8), anchor="mm")

    # UBICACIÓN DERECHA ABAJO (FIJA)
    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    y_base_txt = Y_BOTTOM_BASELINE
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([f_lugar.getlength(l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 30), int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    # 7. DESCRIPCIÓN 2 (ENCIMA DEL BLOQUE FECHA - ALINEADA A LA IZQUIERDA - CANARO MEDIUM)
    # APPLIED WRAPPING 18 FOR DESC 2
    desc2 = datos['desc2']
    if desc2:
        y_desc2_bottom = y_box - 40 
        s_desc2 = 80 
        
        # USO DE CANARO MEDIUM PARA DESC 2
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        
        # Ajustamos el ancho para que no choque con nada
        lines_d2 = textwrap.wrap(desc2, width=18)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_desc2_bottom - total_h_d2 + h_line_d2
        
        for line in lines_d2:
            # Alineado a la izquierda (misma X que la caja de fecha)
            dibujar_texto_sombra(draw, line, x_box, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls") 
            y_cursor_d2 += h_line_d2

    return img.convert("RGB")

# --- TIPO 2: PLANTILLA 2 (T2_V2) ---
def generar_tipo_2_v2(datos):
    # COPIA EXACTA DE T1_V2 + DESC 2 ENCIMA DE FIRMA
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)

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

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    size_desc_val = 110 if chars_desc <= 75 else (90 if chars_desc <= 150 else 75)
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=(35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55))):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    # FIRMA JOTA LLORET (ABAJO DERECHA)
    y_firma = 0
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        y_firma = int(Y_BOTTOM_BASELINE - firma.height + 50)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, y_firma), firma)

    # --- DESCRIPCIÓN 2 (ENCIMA DE FIRMA - CENTRADA - CANARO MEDIUM) ---
    desc2 = datos['desc2']
    if desc2 and os.path.exists("flyer_firma.png"):
        s_desc2 = 80
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()

        # REDUCIDO EL WRAPPING PARA QUE NO SE SALGA
        lines_d2 = textwrap.wrap(desc2, width=22) # Ajustado de 30 a 22
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2

        # Centro horizontal de la firma
        cx_firma = W - SIDE_MARGIN - (firma.width // 2)
        # Posición Y inicial (encima de la firma con MÁS margen)
        # AUMENTADO EL MARGEN VERTICAL (de 40 a 100)
        y_cursor_d2 = y_firma - 100 - total_h_d2 + (h_line_d2 / 2)

        for line in lines_d2:
            dibujar_texto_sombra(draw, line, cx_firma, y_cursor_d2, f_desc2, offset=(5,5), anchor="mm")
            y_cursor_d2 += h_line_d2

    # COLUMNA IZQUIERDA (UBICACIÓN + FECHA)
    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height = int(s_lug * 1.1); total_text_height = len(lines_loc) * line_height
    x_txt_start = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 300 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"
    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_linea_hora - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_linea_hora, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")

# --- TIPO 2: PLANTILLA 3 (T2_V3) ---
def generar_tipo_2_v3(datos):
    # BASE: COPIA EXACTA DE T1_V3 + DESC 2 ENTRE DESC 1 Y FECHA
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 1. Fondo Oscuro / Sombra
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
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
        path_medium = ruta_abs("Canaro-Medium.ttf") # Added for Desc 2
    except:
        f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default()
        path_desc = path_medium = None

    # 3. Título "INVITA" (Izquierda - T1_V3 Base)
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    # 4. Descripción 1 (Izquierda - T1_V3 Base)
    desc1 = datos['desc1']
    chars_desc = len(desc1)

    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 115:
        s_desc = 110; wrap_w = 18
    else:
        s_desc = 90; wrap_w = 22

    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1150

    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)
    
    # At this point, y_desc is the y-coordinate for the *next* line after Desc 1.

    # 5. FECHA IZQUIERDA ABAJO (FIJA - T1_V3 Base)
    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    str_hora = datos['hora1'].strftime('%H:%M %p')
    if datos['hora2']: str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
    size_hora = 110 if not datos['hora2'] else 80
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    w_caja = 645
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA").resize((645, 645), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja); color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white"); color_fecha = "black"

    cx = x_box + (w_caja / 2); cy = int(y_box + (h_caja / 2))
    draw.text((cx, cy - 50), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 170), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, Y_BOTTOM_BASELINE - 100, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, Y_BOTTOM_BASELINE, f_hora, offset=(8,8), anchor="mm")

    # --- INSERT DESCRIPCIÓN 2 HERE ---
    # It must be below Desc 1 (y_desc) and above the Date Box (y_box).
    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()

        # Wrap width. The date box is 645 wide. Let's try to keep it within that.
        # A width of ~25 characters should fit.
        lines_d2 = textwrap.wrap(desc2, width=25)
        h_line_d2 = int(s_desc2 * 1.1)

        # Calculate starting Y. Let's put it a bit below Desc 1.
        y_cursor_d2 = y_desc + 60 # Add some margin

        for line in lines_d2:
            # Check if we are overlapping the date box
            if y_cursor_d2 > y_box - 20: # Leave a small gap above the box
                 # Stop drawing if we run out of space.
                 pass # Or break/warn

            # Left-aligned at SIDE_MARGIN
            dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls")
            y_cursor_d2 += h_line_d2

    # 6. UBICACIÓN DERECHA ABAJO (FIJA - T1_V3 Base)
    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    y_base_txt = Y_BOTTOM_BASELINE
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([f_lugar.getlength(l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 30), int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    # 7. LOGOS ARRIBA (T1_V3 Base)
    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) # IZQUIERDA
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) # DERECHA

    return img.convert("RGB")


# ==============================================================================
# 5. INTERFAZ DE USUARIO
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
            st.markdown(f"""<a href="?area=Cultura" target="_self" style="text-decoration:none;"><div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" class="zoom-hover" width="100%"><div class="label-menu">CULTURA</div></div></a>""", unsafe_allow_html=True)
    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            img_b64 = get_base64_of_bin_file("btn_recreacion.png")
            st.markdown(f"""<a href="?area=Recreación" target="_self" style="text-decoration:none;"><div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" class="zoom-hover" width="100%"><div class="label-menu">RECREACIÓN</div></div></a>""", unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
         if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=300)

elif area_seleccionada in ["Cultura", "Recreación"]:
    if st.button("⬅️ VOLVER AL INICIO", type="primary", key="back_btn"):
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
        desc1 = st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150, max_chars=175)
        
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        desc2 = st.text_area("lbl_desc2", key="lbl_desc2", label_visibility="collapsed", placeholder="", height=100, max_chars=175)
        
        total_chars = len(desc1) + len(desc2)
        color_c = "red" if total_chars > 175 else "black"
        st.markdown(f"<p style='text-align:right; color:{color_c}; font-size:12px; margin-top:-10px;'>Total caracteres: {total_chars} / 175</p>", unsafe_allow_html=True)

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown('<div class="label-negro">FECHA INICIO</div>', unsafe_allow_html=True)
            fecha1 = st.date_input("lbl_fecha1", key="lbl_fecha1", label_visibility="collapsed", format="DD/MM/YYYY", value=None)
        with c_f2:
            st.markdown('<div class="label-negro">FECHA FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            fecha2 = st.date_input("lbl_fecha2", key="lbl_fecha2", label_visibility="collapsed", value=None, format="DD/MM/YYYY")
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown('<div class="label-negro">HORARIO INICIO</div>', unsafe_allow_html=True)
            hora1 = st.time_input("lbl_hora1", key="lbl_hora1", label_visibility="collapsed", value=datetime.time(9, 00))
        with c_h2:
            st.markdown('<div class="label-negro">HORARIO FINAL <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
            hora2 = st.time_input("lbl_hora2", key="lbl_hora2", label_visibility="collapsed", value=None)
        
        st.markdown('<div class="label-negro">DIRECCIÓN</div>', unsafe_allow_html=True)
        dir_texto = st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento", max_chars=80)
        st.markdown(f"<p style='text-align:right; color:black; font-size:12px; margin-top:-5px;'>Caracteres: {len(dir_texto)} / 80</p>", unsafe_allow_html=True)
        
        st.markdown('<div class="label-negro">LOGOS COLABORADORES <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        logos = st.file_uploader("lbl_logos", key="lbl_logos", accept_multiple_files=True, label_visibility="collapsed")
        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR Y RECORTAR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("lbl_img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte. Recuerda usar imágenes de buena calidad.")
            if 'imagen_lista_para_flyer' not in st.session_state:
                st.session_state['imagen_lista_para_flyer'] = None
            img_crop = st_cropper(img_orig, realtime_update=True, box_color='#FF0000', aspect_ratio=(4, 5), should_resize_image=False)
            st.session_state['imagen_lista_para_flyer'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Imagen lista.")

        st.write("")
        if st.button("✨ GENERAR FLYERS ✨", type="primary", use_container_width=True):
            errores = []
            if not st.session_state.lbl_desc: errores.append("Falta Descripción 1")
            if not st.session_state.lbl_fecha1: errores.append("Falta Fecha Inicio")
            if st.session_state.get('imagen_lista_para_flyer') is None: errores.append("Falta recortar la Imagen de Fondo")
            
            if (len(st.session_state.lbl_desc) + len(st.session_state.lbl_desc2)) > 175:
                errores.append(f"¡Has excedido el límite total de texto! (Llevas {len(st.session_state.lbl_desc) + len(st.session_state.lbl_desc2)}/175)")

            if errores:
                for e in errores: st.error(f"⚠️ {e}")
            else:
                has_desc2 = bool(st.session_state.lbl_desc2.strip())
                has_fecha2 = st.session_state.lbl_fecha2 is not None
                
                datos = {
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
                
                generated_images = {}
                
                # --- LOGICA DE SELECCIÓN ESTRICTA ---
                if has_desc2:
                    # SOLO TIPO 2 (DESCRIPCIÓN 2)
                    generated_images['t2_v1'] = generar_tipo_2_v1(datos)
                    generated_images['t2_v2'] = generar_tipo_2_v2(datos)
                    generated_images['t2_v3'] = generar_tipo_2_v3(datos) # AÑADIDA T2_V3
                    st.session_state['variant_selected'] = 't2_v1'
                    st.session_state['tipo_id'] = 2 
                else:
                    # SOLO TIPO 1 (SIN DESCRIPCIÓN 2)
                    generated_images['v1'] = generar_tipo_1(datos)
                    generated_images['v2'] = generar_tipo_1_v2(datos)
                    generated_images['v3'] = generar_tipo_1_v3(datos)
                    generated_images['v4'] = generar_tipo_1_v4(datos)
                    st.session_state['variant_selected'] = 'v1'
                    st.session_state['tipo_id'] = 1 
                
                st.session_state['datos_finales'] = datos
                st.session_state['generated_images'] = generated_images
                st.query_params["area"] = "Final"
                st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    if 'datos_finales' not in st.session_state:
        st.warning("⚠️ No hay datos. Vuelve al inicio.")
        if st.button("Volver al Inicio", type="primary"):
            st.query_params.clear()
            st.rerun()
    else:
        tipo = st.session_state['tipo_id']
        generated = st.session_state.get('generated_images', {})
        sel = st.session_state.get('variant_selected', '')
        
        c_left, c_center, c_right = st.columns([1.5, 3, 1.5])
        
        with c_left:
            st.write("")
            if os.path.exists("mascota_pincel.png"): st.image("mascota_pincel.png", width=350)
            st.write("")
            if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=280)

        with c_center:
            if generated:
                # Validar selección
                if sel not in generated: sel = list(generated.keys())[0]
                
                img_show = generated[sel]
                fname = f"flyer_azuay_{sel}.png"
                st.image(img_show, use_container_width=True)
                
                st.write("")
                c_prev, c_down, c_next = st.columns([1, 2, 1])
                
                # Definir orden según el tipo
                if tipo == 2:
                    order = ['t2_v1', 't2_v2', 't2_v3'] # Tres variantes para Tipo 2
                else:
                    order = ['v1', 'v2', 'v3', 'v4']
                
                try: curr_idx = order.index(sel)
                except: curr_idx = 0
                prev_var = order[(curr_idx - 1) % len(order)]
                next_var = order[(curr_idx + 1) % len(order)]

                with c_prev:
                    if len(order) > 1: # Solo mostrar flechas si hay opciones
                        if st.button("⬅️", key="prev_btn", type="secondary"):
                            st.session_state['variant_selected'] = prev_var
                            st.rerun()
                
                with c_down:
                    buf = io.BytesIO()
                    img_show.save(buf, format="PNG")
                    img_b64_dl = base64.b64encode(buf.getvalue()).decode()
                    if os.path.exists("mascota_final.png"):
                        with open("mascota_final.png", "rb") as f:
                            chola_b64 = base64.b64encode(f.read()).decode()
                        html_chola = f"""
                        <div style="text-align: center;">
                            <a href="data:image/png;base64,{img_b64_dl}" download="{fname}" style="text-decoration: none; border: none !important; outline: none !important;">
                                <img src="data:image/png;base64,{chola_b64}" width="220" class="zoom-hover" style="border: none !important; outline: none !important; display: block; margin: auto;">
                                <div style="font-family: 'Canaro'; font-weight: bold; font-size: 18px; color: white; margin-top: 5px; text-decoration: none;">DESCARGUE AQUÍ</div>
                            </a>
                        </div>
                        """
                        st.markdown(html_chola, unsafe_allow_html=True)
                    else:
                        st.download_button("⬇️ DESCARGAR", data=buf.getvalue(), file_name=fname, mime="image/png", use_container_width=True)

                with c_next:
                    if len(order) > 1:
                        if st.button("➡️", key="next_btn", type="secondary"):
                            st.session_state['variant_selected'] = next_var
                            st.rerun()
            else:
                st.info("No se generaron imágenes.")

        with c_right:
            st.empty()

    st.write("---")
    if st.button("🔄 CREAR NUEVO", type="primary"):
        st.query_params.clear()
        keys_borrar = ['imagen_lista_para_flyer', 'datos_finales', 'lbl_desc', 'lbl_desc2', 'lbl_dir', 'variant_selected', 'generated_images', 'tipo_id']
        for k in keys_borrar:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
