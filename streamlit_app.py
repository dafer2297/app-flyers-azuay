import streamlit as st
import base64
import os
import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper

# ==============================================================================
# 1. CONFIGURACION Y ESTILOS
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
        bg_style = f"background-image: url('data:image/png;base64,{bin_str}'); background-size: cover; background-position: center; background-attachment: fixed;"

    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css += f"@font-face {{ font-family: 'Canaro'; src: url('data:font/ttf;base64,{font_b64}') format('truetype'); }}"

    st.markdown(
        f"<style>"
        f".stApp {{ {bg_style} }}"
        f"{font_css}"
        f"h1, h2, h3 {{ font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }}"
        f"div[data-testid='stButton'] button[kind='secondary'] {{"
        f"    background-color: white; color: #1E88E5; border: none; border-radius: 50%;"
        f"    width: 60px; height: 60px; font-size: 24px; box-shadow: 0px 4px 6px rgba(0,0,0,0.2);"
        f"    transition: all 0.2s; display: flex; align-items: center; justify-content: center; margin: auto;"
        f"}}"
        f"div[data-testid='stButton'] button[kind='secondary']:hover {{"
        f"    background-color: #f0f0f0; transform: scale(1.1); color: #1565C0;"
        f"}}"
        f"div[data-testid='stButton'] button[kind='primary'] {{"
        f"    background-color: transparent; color: white; border: 2px solid white; border-radius: 15px;"
        f"    width: 100%; height: auto; padding: 10px 20px; font-weight: bold; font-size: 16px; box-shadow: none;"
        f"}}"
        f"div[data-testid='stButton'] button[kind='primary']:hover {{"
        f"    background-color: #D81B60; border-color: #D81B60; transform: none;"
        f"}}"
        f".stTextInput > div > div > input, .stTextArea > div > div > textarea,"
        f".stDateInput > div > div > input, .stTimeInput > div > div > input {{"
        f"    background-color: white !important; color: black !important; border-radius: 8px; border: none;"
        f"}}"
        f".stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{ display: none; }}"
        f".label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; }}"
        f".label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}"
        f".label-menu {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 20px; color: white !important; margin-top: 10px; text-transform: uppercase; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); text-decoration: none !important; }}"
        f"a {{ text-decoration: none !important; }}"
        f"a img {{ border: none !important; outline: none !important; box-shadow: none !important; }}"
        f".zoom-hover {{ transition: transform 0.2s; cursor: pointer; }}"
        f".zoom-hover:hover {{ transform: scale(1.05); }}"
        f"#MainMenu, footer, header {{ visibility: hidden; }}"
        f"</style>", unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. MOTOR GRAFICO
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
    dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
    return dias[fecha.weekday()]

def resize_por_alto(img, alto_objetivo):
    ratio = alto_objetivo / img.height
    ancho_nuevo = int(img.width * ratio)
    return img.resize((ancho_nuevo, alto_objetivo), Image.Resampling.LANCZOS)

def redimensionar_logo_colaborador(img):
    w, h = img.size
    if w == h:
        return resize_por_alto(img, 400)
    
    ratio = 400 / h
    new_w = int(w * ratio)
    
    if new_w <= 700:
        return img.resize((new_w, 400), Image.Resampling.LANCZOS)
    else:
        ratio = 700 / w
        new_h = int(h * ratio)
        return img.resize((700, new_h), Image.Resampling.LANCZOS)

# ==============================================================================
# 3. GENERADORES DE PLANTILLAS TIPO 1
# ==============================================================================

def generar_tipo_1(datos):
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

    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

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
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

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
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

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
    
    y_desc = y_titulo + 70 + s_desc
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls"); y_desc += int(s_desc * 1.1)

    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

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
        for _ in range(2): img.paste(logo, (margin_logos, 150), logo)
    
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

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
    
    if chars_desc < 50: s_desc = 130; wrap_w = 15
    elif chars_desc < 90: s_desc = 110; wrap_w = 18
    elif chars_desc < 140: s_desc = 90; wrap_w = 22
    else: s_desc = 75; wrap_w = 25
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    
    y_desc = y_titulo + 70 + s_desc 
    
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
    x_pos_texto = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_pos_texto = SIDE_MARGIN + icon.width + 30
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_pos_texto, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height

    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 130 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 4. GENERADORES DE PLANTILLAS TIPO 2
# ==============================================================================

def generar_tipo_2_v1(datos):
    # TIPO 2 - V1
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

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # REGLA DE TEXTO DINAMICO AJUSTADA PARA EVITAR CHOQUES
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc <= 75:
        size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120:
        size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150:
        size_desc_val = 75; wrap_w = 55
    else:
        size_desc_val = 65; wrap_w = 65
        
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

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

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80 
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=18)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_box - 40 - total_h_d2 + h_line_d2
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, x_box, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls") 
            y_cursor_d2 += h_line_d2

    return img.convert("RGB")

def generar_tipo_2_v2(datos):
    # TIPO 2 - V2
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
    if chars_desc <= 75:
        size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120:
        size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150:
        size_desc_val = 75; wrap_w = 55
    else:
        size_desc_val = 65; wrap_w = 65
        
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    y_firma = 0
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        y_firma = int(Y_BOTTOM_BASELINE - firma.height + 50)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, y_firma), firma)

    desc2 = datos['desc2']
    if desc2 and firma:
        s_desc2 = 80
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=26)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        cx_firma = W - SIDE_MARGIN - (firma.width // 2) - 60
        y_cursor_d2 = y_firma - 100 - total_h_d2 + (h_line_d2 / 2)
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, cx_firma, y_cursor_d2, f_desc2, offset=(5,5), anchor="mm")
            y_cursor_d2 += h_line_d2

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height_loc = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height_loc
    x_txt_start = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height_loc

    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 300 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")

def generar_tipo_2_v3(datos):
    # TIPO 2 - V3
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
        path_medium = ruta_abs("Canaro-Medium.ttf")
    except:
        f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default()
        path_desc = path_medium = None

    y_titulo = 750
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    # REGLA DE TEXTO DINAMICO PARA EVITAR CHOQUES CON CAJA IZQUIERDA
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 100:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 85; wrap_w = 24
    else:
        s_desc = 70; wrap_w = 28

    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = y_titulo + 70 + s_desc
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)
    
    h_caja = 645; x_box = SIDE_MARGIN; y_box = Y_BOTTOM_BASELINE - 170 - h_caja
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=25)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_box - 50 - total_h_d2 + h_line_d2 
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls")
            y_cursor_d2 += h_line_d2

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
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
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    return img.convert("RGB")

def generar_tipo_2_v4(datos):
    # TIPO 2 - V4
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

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 100:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 85; wrap_w = 24
    else:
        s_desc = 70; wrap_w = 28
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = y_titulo + 70 + s_desc 
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls"); y_desc += int(s_desc * 1.1)

    y_firma = 0
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        y_firma = int(Y_BOTTOM_BASELINE - firma.height + 50)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, y_firma), firma)

    desc2 = datos['desc2']
    if desc2 and firma:
        s_desc2 = 80
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=26) 
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        cx_firma = W - SIDE_MARGIN - (firma.width // 2) - 60
        y_cursor_d2 = y_firma - 100 - total_h_d2 + (h_line_d2 / 2)
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, cx_firma, y_cursor_d2, f_desc2, offset=(5,5), anchor="mm")
            y_cursor_d2 += h_line_d2

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height_loc = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height_loc
    
    x_pos_texto = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (h_icon/2))), icon)
        x_pos_texto = SIDE_MARGIN + icon.width + 30
        
    curr_y = Y_BOTTOM_BASELINE - total_text_height + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_pos_texto, curr_y, f_lugar, anchor="ls", offset=(4,4)); curr_y += line_height_loc

    y_linea_hora = Y_BOTTOM_BASELINE - total_text_height - 130 
    h_caja = 645; y_box = y_linea_hora - 170 - h_caja; x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora = ImageFont.truetype(path_extra, size_h)
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
    
    y_box_bottom = y_box + h_caja
    y_dia_txt = y_box_bottom + 85
    y_hora_txt = y_dia_txt + 85
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(8,8), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(8,8), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 5. GENERADORES DE PLANTILLAS TIPO 3 (1 Parrafo, 2 Fechas, 0 Logos)
# ==============================================================================

def generar_tipo_3_v1(datos):
    # TIPO 3 - V1
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160) 
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)  
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
        f_desc = ImageFont.truetype(path_desc, 110) if os.path.exists(path_desc) else ImageFont.load_default()
    except:
        f_invita = f_dias_largo = f_mes_largo = f_desc = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))

    desc1 = datos['desc1']
    size_desc_val = 110 if len(desc1) <= 75 else (90 if len(desc1) <= 150 else 75)
    f_desc = ImageFont.truetype(ruta_abs("Canaro-SemiBold.ttf"), size_desc_val)
    wrap_width = 35 if size_desc_val >= 110 else (45 if size_desc_val >= 90 else 55)
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    h_caja = 352
    w_caja = 780 
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - h_caja - 45 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()

    y_hora = y_box + h_caja + 45
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
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

    return img.convert("RGB")

def generar_tipo_3_v2(datos):
    # TIPO 3 - V2
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
        f_desc = ImageFont.truetype(path_desc, 110) if os.path.exists(path_desc) else ImageFont.load_default()
    except:
        f_invita = f_dias_largo = f_mes_largo = f_desc = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc <= 75:
        size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120:
        size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150:
        size_desc_val = 75; wrap_w = 55
    else:
        size_desc_val = 65; wrap_w = 65
        
    f_desc = ImageFont.truetype(ruta_abs("Canaro-SemiBold.ttf"), size_desc_val)
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height_loc = int(s_lug * 1.1)
    total_h_loc = len(lines_loc) * line_height_loc
    
    x_txt_start = SIDE_MARGIN + 130
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(4,4))
        curr_y_loc += line_height_loc

    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - total_h_loc - 280 - h_caja 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()
    
    y_hora = y_box + h_caja + 45 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    return img.convert("RGB")
def generar_tipo_3_v3(datos):
    # TIPO 3 - V3
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf") 
        path_desc = None

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo)
    
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # TEXTO DINAMICO ALINEADO IZQUIERDA
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 100:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 85; wrap_w = 24
    else:
        s_desc = 70; wrap_w = 28
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    
    y_desc = y_titulo + 70 + s_desc
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls"); y_desc += int(s_desc * 1.1)

    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - 45 - h_caja 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()

    y_hora = y_box + h_caja + 45
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    
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

    return img.convert("RGB")

def generar_tipo_3_v4(datos):
    # TIPO 3 - V4
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = None

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 100:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 85; wrap_w = 24
    else:
        s_desc = 70; wrap_w = 28
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    
    y_desc = y_titulo + 70 + s_desc 
    
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
    line_height_loc = int(s_lug * 1.1)
    total_h_loc = len(lines_loc) * line_height_loc
    
    x_txt_start = SIDE_MARGIN + 130
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(4,4))
        curr_y_loc += line_height_loc

    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - total_h_loc - 280 - h_caja 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()
    
    y_hora = y_box + h_caja + 45 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    return img.convert("RGB")

def generar_tipo_4_v1(datos):
    # TIPO 4 - V1
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = None

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # REGLA TEXTO CENTRADO
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc <= 75:
        size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120:
        size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150:
        size_desc_val = 75; wrap_w = 55
    else:
        size_desc_val = 65; wrap_w = 65
        
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    h_caja = 352
    w_caja = 780 
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - h_caja - 45
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()

    y_hora = y_box + h_caja + 45
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
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

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80 
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=22)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_box - 50 - total_h_d2 + h_line_d2
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, x_box, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls") 
            y_cursor_d2 += h_line_d2

    return img.convert("RGB")

def generar_tipo_4_v2(datos):
    # TIPO 4 - V2
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = None

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    dibujar_texto_sombra(draw, "INVITA", W/2, 850, f_invita, offset=(10,10))
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc <= 75:
        size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120:
        size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150:
        size_desc_val = 75; wrap_w = 55
    else:
        size_desc_val = 65; wrap_w = 65
        
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = 1030
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8)); y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    lines_loc = textwrap.wrap(lugar, width=(20 if s_lug == 72 else 24))
    line_height_loc = int(s_lug * 1.1)
    total_h_loc = len(lines_loc) * line_height_loc
    
    x_txt_start = SIDE_MARGIN + 130 
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(4,4))
        curr_y_loc += line_height_loc

    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - total_h_loc - 280 - h_caja 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()
    
    y_hora = y_box + h_caja + 45 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        
        lines_d2 = textwrap.wrap(desc2, width=22) 
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_box - 50 - total_h_d2 + h_line_d2
        
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, x_box, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls")
            y_cursor_d2 += h_line_d2

    return img.convert("RGB")

def generar_tipo_4_v3(datos):
    # TIPO 4 - V3
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
        path_medium = ruta_abs("Canaro-Medium.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = path_medium = None

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60:
        s_desc = 130; wrap_w = 15
    elif chars_desc < 100:
        s_desc = 110; wrap_w = 18
    elif chars_desc < 140:
        s_desc = 85; wrap_w = 24
    else:
        s_desc = 70; wrap_w = 28

    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = y_titulo + 70 + s_desc
    
    for line in textwrap.wrap(desc1, width=wrap_w):
        dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)
    
    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - 45 - h_caja

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()
    
    y_hora = y_box + h_caja + 45
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=22)
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        
        y_cursor_d2 = y_box - 50 - total_h_d2 + h_line_d2 
        
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls")
            y_cursor_d2 += h_line_d2

    lugar = datos['lugar']
    s_lug = 72 if len(lugar) < 45 else 60
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()
    wrap_chars = 20 if s_lug == 72 else 24
    lines_loc = textwrap.wrap(lugar, width=wrap_chars)
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
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
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA"); firma = resize_por_alto(firma, 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    return img.convert("RGB")
def generar_tipo_4_v4(datos):
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
        f_dias_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 160)
        f_mes_largo = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 130)
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except:
        f_invita = f_dias_largo = f_mes_largo = ImageFont.load_default()
        path_extra = ruta_abs("Canaro-Black.ttf")
        path_desc = None

    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA"); logo = resize_por_alto(logo, 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    desc1 = datos['desc1']
    chars_desc = len(desc1)
    if chars_desc < 60: s_desc = 130; wrap_w = 15
    elif chars_desc < 100: s_desc = 110; wrap_w = 18
    elif chars_desc < 140: s_desc = 85; wrap_w = 24
    else: s_desc = 70; wrap_w = 28
        
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc and os.path.exists(path_desc) else ImageFont.load_default()
    y_desc = y_titulo + 70 + s_desc 
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
    line_height_loc = int(s_lug * 1.1)
    total_h_loc = len(lines_loc) * line_height_loc
    
    x_txt_start = SIDE_MARGIN + 130
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA"); icon = resize_por_alto(icon, h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 30
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + line_height_loc
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(4,4))
        curr_y_loc += line_height_loc

    h_caja = 352
    w_caja = 780
    x_box = SIDE_MARGIN
    y_box = Y_BOTTOM_BASELINE - total_h_loc - 280 - h_caja 
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    draw.text((cx, cy - 45), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 95), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 110 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 80 
    try: f_hora_dyn = ImageFont.truetype(path_extra, size_h)
    except: f_hora_dyn = ImageFont.load_default()
    y_hora = y_box + h_caja + 45 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(8,8), anchor="mm")

    desc2 = datos['desc2']
    if desc2:
        s_desc2 = 80
        path_medium = ruta_abs("Canaro-Medium.ttf")
        try: f_desc2 = ImageFont.truetype(path_medium, s_desc2)
        except: f_desc2 = ImageFont.load_default()
        lines_d2 = textwrap.wrap(desc2, width=22) 
        h_line_d2 = int(s_desc2 * 1.1)
        total_h_d2 = len(lines_d2) * h_line_d2
        y_cursor_d2 = y_box - 50 - total_h_d2 + h_line_d2
        for line in lines_d2:
            dibujar_texto_sombra(draw, line, x_box, y_cursor_d2, f_desc2, offset=(5,5), anchor="ls")
            y_cursor_d2 += h_line_d2

    return img.convert("RGB")

# ==============================================================================
# 7. GENERADORES DE PLANTILLAS TIPO 5 (1 Parrafo, 1 Fecha, 1 Colaborador)
# ==============================================================================

def generar_tipo_5_v1(datos):
    fondo = datos['fondo'].copy(); W, H = 2400, 3000; SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150; img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA"); draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"): sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS); img.paste(sombra_img, (0, 0), sombra_img)
    else: overlay = Image.new('RGBA', (W, H), (0,0,0,0)); d_over = ImageDraw.Draw(overlay); [d_over.line([(0,y), (W,y)], fill=(0,0,0, int(255*((y-H*0.3)/(H*0.7))*0.9))) for y in range(int(H*0.3), H)]; img = Image.alpha_composite(img, overlay); draw = ImageDraw.Draw(img)
    try: f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220); path_desc = ruta_abs("Canaro-SemiBold.ttf"); f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 297); f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 170); path_extra = ruta_abs("Canaro-ExtraBold.ttf"); f_dia_semana = ImageFont.truetype(path_extra, 93)
    except: f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default(); path_desc = None
    margin_logos = 200; img.paste(resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378), (margin_logos, 150)) if os.path.exists("flyer_logo.png") else None; img.paste(resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325), (W - int(Image.open("flyer_firma.png").width * (325/Image.open("flyer_firma.png").height)) - margin_logos, 170)) if os.path.exists("flyer_firma.png") else None
    dibujar_texto_sombra(draw, "INVITAN", W/2, 780, f_invita, offset=(10,10)); desc1 = datos['desc1']; chars_desc = len(desc1)
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150: size_desc_val = 75; wrap_w = 55
    else: size_desc_val = 65; wrap_w = 65
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc else ImageFont.load_default(); [dibujar_texto_sombra(draw, l, W/2, 960 + i*int(size_desc_val*1.1), f_desc, offset=(8,8)) for i,l in enumerate(textwrap.wrap(desc1, width=wrap_w))]
    collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA")) if datos.get('logos') else None
    y_logo = Y_BOTTOM_BASELINE - (collab_img.height if collab_img else 0); img.paste(collab_img, (SIDE_MARGIN + 274 - (collab_img.width//2), int(y_logo)), collab_img) if collab_img else None
    y_box = y_logo - 90 - 72 - 72 - 548; img.paste(Image.open("flyer_caja_fecha.png").convert("RGBA").resize((548, 548), Image.Resampling.LANCZOS), (SIDE_MARGIN, int(y_box))) if os.path.exists("flyer_caja_fecha.png") else draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+548, y_box+548], fill="white")
    cx = SIDE_MARGIN + 274; cy = int(y_box + 274); draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill="white", anchor="mm"); draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="white", anchor="mm"); str_hora = datos['hora1'].strftime('%H:%M %p') + (f" a {datos['hora2'].strftime('%H:%M %p')}" if datos['hora2'] else ""); f_hora = ImageFont.truetype(path_extra, 68 if datos['hora2'] else 93)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_logo-90-72, f_dia_semana, offset=(6,6), anchor="mm"); dibujar_texto_sombra(draw, str_hora, cx, y_logo-90, f_hora, offset=(6,6), anchor="mm")
    lugar = datos['lugar']; s_lug = 61 if len(lugar) < 45 else 51; f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug); lines_loc = textwrap.wrap(lugar, width=(24 if s_lug == 61 else 28)); x_text_start = W - SIDE_MARGIN - max([f_lugar.getlength(l) for l in lines_loc] or [200]); icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), 221) if os.path.exists("flyer_icono_lugar.png") else None
    img.paste(icon, (int(x_text_start - icon.width - 25), int(Y_BOTTOM_BASELINE - (len(lines_loc)*int(s_lug*1.1)/2) - (221/2))), icon) if icon else None; [dibujar_texto_sombra(draw, l, x_text_start, Y_BOTTOM_BASELINE - len(lines_loc)*int(s_lug*1.1) + (i+1)*int(s_lug*1.1), f_lugar, anchor="ls", offset=(3,3)) for i,l in enumerate(lines_loc)]
    return img.convert("RGB")

def generar_tipo_5_v2(datos):
    fondo = datos['fondo'].copy(); W, H = 2400, 3000; SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150; img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA"); draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"): sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS); img.paste(sombra_img, (0, 0), sombra_img)
    else: overlay = Image.new('RGBA', (W, H), (0,0,0,0)); d_over = ImageDraw.Draw(overlay); [d_over.line([(0,y), (W,y)], fill=(0,0,0, int(255*((y-H*0.3)/(H*0.7))*0.9))) for y in range(int(H*0.3), H)]; img = Image.alpha_composite(img, overlay); draw = ImageDraw.Draw(img)
    try: f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220); f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 297); f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 170); path_extra = ruta_abs("Canaro-ExtraBold.ttf"); f_dia_semana = ImageFont.truetype(path_extra, 93); path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except: f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default(); path_desc = None
    margin_logos_top = 300; img.paste(resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378), (margin_logos_top, 150)) if os.path.exists("flyer_logo.png") else None
    if datos.get('logos'): collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA")); img.paste(collab_img, (int(W - margin_logos_top - collab_img.width), int(150 + (378 - collab_img.height) // 2)), collab_img)
    dibujar_texto_sombra(draw, "INVITAN", W/2, 850, f_invita, offset=(10,10)); desc1 = datos['desc1']; chars_desc = len(desc1)
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 35
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 45
    elif chars_desc <= 150: size_desc_val = 75; wrap_w = 55
    else: size_desc_val = 65; wrap_w = 65
    f_desc = ImageFont.truetype(path_desc, size_desc_val) if path_desc else ImageFont.load_default(); [dibujar_texto_sombra(draw, l, W/2, 1030 + i*int(size_desc_val*1.1), f_desc, offset=(8,8)) for i,l in enumerate(textwrap.wrap(desc1, width=wrap_w))]
    img.paste(resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325), (W - int(Image.open("flyer_firma.png").width * (325/Image.open("flyer_firma.png").height)) - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - 325 + 50))) if os.path.exists("flyer_firma.png") else None
    lugar = datos['lugar']; s_lug = 61 if len(lugar) < 45 else 51; f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug); lines_loc = textwrap.wrap(lugar, width=(24 if s_lug == 61 else 28)); total_text_height = len(lines_loc) * int(s_lug*1.1); x_txt_start = SIDE_MARGIN + 110; icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), 221) if os.path.exists("flyer_icono_lugar.png") else None
    img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_text_height/2) - (221/2))), icon) if icon else None; [dibujar_texto_sombra(draw, l, SIDE_MARGIN + (icon.width+25 if icon else 0), Y_BOTTOM_BASELINE - total_text_height + (i+1)*int(s_lug*1.1), f_lugar, anchor="ls", offset=(4,4)) for i,l in enumerate(lines_loc)]
    y_box = Y_BOTTOM_BASELINE - total_text_height - 130 - 548; img.paste(Image.open("flyer_caja_fecha.png").convert("RGBA").resize((548, 548), Image.Resampling.LANCZOS), (SIDE_MARGIN, int(y_box))) if os.path.exists("flyer_caja_fecha.png") else draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+548, y_box+548], fill="white"); cx = SIDE_MARGIN + 274; cy = int(y_box + 274); draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill="white", anchor="mm"); draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="white", anchor="mm"); str_hora = datos['hora1'].strftime('%H:%M %p') + (f" a {datos['hora2'].strftime('%H:%M %p')}" if datos['hora2'] else ""); f_hora = ImageFont.truetype(path_extra, 68 if datos['hora2'] else 93); dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_box+548+72, f_dia_semana, offset=(6,6), anchor="mm"); dibujar_texto_sombra(draw, str_hora, cx, y_box+548+144, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_5_v3(datos):
    fondo = datos['fondo'].copy(); W, H = 2400, 3000; SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150; img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA"); draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"): sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS); img.paste(sombra_img, (0, 0), sombra_img)
    else: overlay = Image.new('RGBA', (W, H), (0,0,0,0)); d_over = ImageDraw.Draw(overlay); [d_over.line([(0,y), (W,y)], fill=(0,0,0, int(255*((y-H*0.3)/(H*0.7))*0.9))) for y in range(int(H*0.3), H)]; img = Image.alpha_composite(img, overlay); draw = ImageDraw.Draw(img)
    try: f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220); path_desc = ruta_abs("Canaro-SemiBold.ttf"); f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 297); f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 170); path_extra = ruta_abs("Canaro-ExtraBold.ttf"); f_dia_semana = ImageFont.truetype(path_extra, 93)
    except: f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default(); path_desc = None
    margin_logos = 200; img.paste(resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378), (margin_logos, 150)) if os.path.exists("flyer_logo.png") else None; img.paste(resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325), (W - int(Image.open("flyer_firma.png").width * (325/Image.open("flyer_firma.png").height)) - margin_logos, 170)) if os.path.exists("flyer_firma.png") else None
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, 780, f_invita, offset=(10,10), anchor="lm"); desc1 = datos['desc1']; chars_desc = len(desc1)
    if chars_desc < 60: s_desc = 130; wrap_w = 15
    elif chars_desc < 100: s_desc = 110; wrap_w = 18
    elif chars_desc < 140: s_desc = 85; wrap_w = 24
    else: s_desc = 70; wrap_w = 28
    f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc else ImageFont.load_default(); [dibujar_texto_sombra(draw, l, SIDE_MARGIN, 940 + i*int(s_desc*1.1), f_desc, offset=(8,8), anchor="ls") for i,l in enumerate(textwrap.wrap(desc1, width=wrap_w))]
    collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA")) if datos.get('logos') else None
    y_logo = Y_BOTTOM_BASELINE - (collab_img.height if collab_img else 0); img.paste(collab_img, (SIDE_MARGIN + 274 - (collab_img.width//2), int(y_logo)), collab_img) if collab_img else None
    y_box = y_logo - 90 - 72 - 72 - 548; img.paste(Image.open("flyer_caja_fecha.png").convert("RGBA").resize((548, 548), Image.Resampling.LANCZOS), (SIDE_MARGIN, int(y_box))) if os.path.exists("flyer_caja_fecha.png") else draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+548, y_box+548], fill="white")
    cx = SIDE_MARGIN + 274; cy = int(y_box + 274); draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill="white", anchor="mm"); draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="white", anchor="mm"); str_hora = datos['hora1'].strftime('%H:%M %p') + (f" a {datos['hora2'].strftime('%H:%M %p')}" if datos['hora2'] else ""); f_hora = ImageFont.truetype(path_extra, 68 if datos['hora2'] else 93)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_logo-90-72, f_dia_semana, offset=(6,6), anchor="mm"); dibujar_texto_sombra(draw, str_hora, cx, y_logo-90, f_hora, offset=(6,6), anchor="mm")
    lugar = datos['lugar']; s_lug = 61 if len(lugar) < 45 else 51; f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug); lines_loc = textwrap.wrap(lugar, width=(24 if s_lug == 61 else 28)); x_text_start = W - SIDE_MARGIN - max([f_lugar.getlength(l) for l in lines_loc] or [200]); icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), 221) if os.path.exists("flyer_icono_lugar.png") else None
    img.paste(icon, (int(x_text_start - icon.width - 25), int(Y_BOTTOM_BASELINE - (len(lines_loc)*int(s_lug*1.1)/2) - (221/2))), icon) if icon else None; [dibujar_texto_sombra(draw, l, x_text_start, Y_BOTTOM_BASELINE - len(lines_loc)*int(s_lug*1.1) + (i+1)*int(s_lug*1.1), f_lugar, anchor="ls", offset=(3,3)) for i,l in enumerate(lines_loc)]
    return img.convert("RGB")

def generar_tipo_5_v4(datos):
    fondo = datos['fondo'].copy(); W, H = 2400, 3000; SIDE_MARGIN = 180; Y_BOTTOM_BASELINE = H - 150; img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA"); draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"): sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS); img.paste(sombra_img, (0, 0), sombra_img)
    else: overlay = Image.new('RGBA', (W, H), (0,0,0,0)); d_over = ImageDraw.Draw(overlay); [d_over.line([(0,y), (W,y)], fill=(0,0,0, int(255*((y-H*0.3)/(H*0.7))*0.9))) for y in range(int(H*0.3), H)]; img = Image.alpha_composite(img, overlay); draw = ImageDraw.Draw(img)
    try: f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 220); f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 297); f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 170); path_extra = ruta_abs("Canaro-ExtraBold.ttf"); f_dia_semana = ImageFont.truetype(path_extra, 93); path_desc = ruta_abs("Canaro-SemiBold.ttf")
    except: f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default(); path_desc = None
    margin_logos_top = 300; img.paste(resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378), (margin_logos_top, 150)) if os.path.exists("flyer_logo.png") else None
    if datos.get('logos'): collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA")); img.paste(collab_img, (int(W - margin_logos_top - collab_img.width), int(150 + (378 - collab_img.height)//2)), collab_img)
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, 800, f_invita, offset=(10,10), anchor="lm"); desc1 = datos['desc1']; chars_desc = len(desc1); s_desc = 130 if chars_desc < 60 else (110 if chars_desc < 100 else (85 if chars_desc < 140 else 70)); wrap_w = 15 if chars_desc < 60 else (18 if chars_desc < 100 else (24 if chars_desc < 140 else 28)); f_desc = ImageFont.truetype(path_desc, s_desc) if path_desc else ImageFont.load_default(); [dibujar_texto_sombra(draw, l, SIDE_MARGIN, 800+70+s_desc + i*int(s_desc*1.1), f_desc, offset=(8,8), anchor="ls") for i,l in enumerate(textwrap.wrap(desc1, width=wrap_w))]
    img.paste(resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325), (W - int(Image.open("flyer_firma.png").width * (325/Image.open("flyer_firma.png").height)) - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - 325 + 50))) if os.path.exists("flyer_firma.png") else None
    lugar = datos['lugar']; s_lug = 61 if len(lugar) < 45 else 51; f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug); lines_loc = textwrap.wrap(lugar, width=(24 if s_lug == 61 else 28)); total_h_loc = len(lines_loc)*int(s_lug*1.1); x_txt_start = SIDE_MARGIN + 110; icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), 221) if os.path.exists("flyer_icono_lugar.png") else None; img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (221/2))), icon) if icon else None; [dibujar_texto_sombra(draw, l, SIDE_MARGIN + (icon.width+25 if icon else 0), Y_BOTTOM_BASELINE - total_h_loc + (i+1)*int(s_lug*1.1), f_lugar, anchor="ls", offset=(3,3)) for i,l in enumerate(lines_loc)]
    y_box = Y_BOTTOM_BASELINE - total_h_loc - 130 - 548; img.paste(Image.open("flyer_caja_fecha.png").convert("RGBA").resize((548, 548), Image.Resampling.LANCZOS), (SIDE_MARGIN, int(y_box))) if os.path.exists("flyer_caja_fecha.png") else draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+548, y_box+548], fill="white"); cx = SIDE_MARGIN + 274; cy = int(y_box + 274); draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill="white", anchor="mm"); draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill="white", anchor="mm"); str_hora = datos['hora1'].strftime('%H:%M %p') + (f" a {datos['hora2'].strftime('%H:%M %p')}" if datos['hora2'] else ""); f_hora = ImageFont.truetype(path_extra, 68 if datos['hora2'] else 93); dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_box+548+72, f_dia_semana, offset=(6,6), anchor="mm"); dibujar_texto_sombra(draw, str_hora, cx, y_box+548+144, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

# ==============================================================================
# 8. INTERFAZ DE USUARIO
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
            st.markdown(f"<a href='?area=Culturas' target='_self'><div style='text-align: center;'><img src='data:image/png;base64,{img_b64}' class='zoom-hover' width='100%'><div class='label-menu'>CULTURAS</div></div></a>", unsafe_allow_html=True)
    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            img_b64 = get_base64_of_bin_file("btn_recreacion.png")
            st.markdown(f"<a href='?area=Recreación' target='_self'><div style='text-align: center;'><img src='data:image/png;base64,{img_b64}' class='zoom-hover' width='100%'><div class='label-menu'>RECREACION</div></div></a>", unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
         if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=300)

elif area_seleccionada in ["Culturas", "Recreación"]:
    st.session_state['v_area'] = area_seleccionada
    if st.button("⬅️ VOLVER AL INICIO", type="primary"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()

    col_izq, col_der = st.columns([1, 2], gap="large")
    with col_izq:
        st.write("")
        icono = "icono_cultura.png" if area_seleccionada == "Culturas" else "icono_recreacion.png"
        if os.path.exists(icono): st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=200)

    with col_der:
        st.markdown("<div class='label-negro'>DESCRIPCION 1</div>", unsafe_allow_html=True)
        desc1 = st.text_area("d1", key="d1", placeholder="Escribe aqui...", height=150, max_chars=175, value=st.session_state.get('v_d1', ""))
        
        st.markdown("<div class='label-negro'>DESCRIPCION 2 (OPCIONAL)</div>", unsafe_allow_html=True)
        desc2 = st.text_area("d2", key="d2", placeholder="", height=100, max_chars=175, value=st.session_state.get('v_d2', ""))
        
        color_c = "red" if (len(desc1)+len(desc2)) > 175 else "black"
        st.markdown(f"<p style='text-align:right; color:{color_c}; font-size:12px; margin-top:-10px;'>{len(desc1)+len(desc2)} / 175</p>", unsafe_allow_html=True)

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown("<div class='label-negro'>FECHA INICIO</div>", unsafe_allow_html=True)
            fecha1 = st.date_input("f1", key="f1", format="DD/MM/YYYY", value=st.session_state.get('v_f1', None))
        with c_f2:
            st.markdown("<div class='label-negro'>FECHA FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            fecha2 = st.date_input("f2", key="f2", value=st.session_state.get('v_f2', None), format="DD/MM/YYYY")
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown("<div class='label-negro'>HORARIO INICIO</div>", unsafe_allow_html=True)
            hora1 = st.time_input("h1", key="h1", value=st.session_state.get('v_h1', datetime.time(9, 0)))
        with c_h2:
            st.markdown("<div class='label-negro'>HORARIO FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            hora2 = st.time_input("h2", key="h2", value=st.session_state.get('v_h2', None))
        
        st.markdown("<div class='label-negro'>DIRECCION</div>", unsafe_allow_html=True)
        dir_texto = st.text_input("dir", key="dir", placeholder="Ubicacion", max_chars=80, value=st.session_state.get('v_dir', ""))
        
        st.markdown("<div class='label-negro'>LOGOS COLABORADORES</div>", unsafe_allow_html=True)
        logos = st.file_uploader("lg", key="lg", accept_multiple_files=True)
        
        st.markdown("<div class='label-negro' style='margin-top: 15px;'>SUBIR Y RECORTAR IMAGEN DE FONDO</div>", unsafe_allow_html=True)
        if 'v_fondo' in st.session_state:
            st.success("IMAGEN YA RECORTADA Y GUARDADA. Si subes una nueva, reemplazara a la anterior.")
        
        archivo_subido = st.file_uploader("img", type=['jpg', 'png', 'jpeg'])
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte. Recuerda usar imagenes de buena calidad.")
            img_crop = st_cropper(img_orig, realtime_update=True, aspect_ratio=(4, 5), should_resize_image=False)
            st.session_state['v_fondo'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("Nueva imagen lista.")

        st.write("")
        if st.button("✨ GENERAR FLYERS ✨", type="primary", use_container_width=True):
            errores = []
            if not desc1: errores.append("Falta Descripcion 1")
            if not fecha1: errores.append("Falta Fecha Inicio")
            if 'v_fondo' not in st.session_state: errores.append("Falta recortar la Imagen de Fondo")
            if (len(desc1) + len(desc2)) > 175: errores.append("Excediste el limite de 175 caracteres")

            if errores:
                for e in errores: st.error(f" {e}")
            else:
                rutas_logos = []
                if logos:
                    for i, l in enumerate(logos):
                        with open(f"temp_{i}.png", "wb") as f: f.write(l.getvalue())
                        rutas_logos.append(f"temp_{i}.png")
                
                st.session_state.update({'v_d1':desc1,'v_d2':desc2,'v_f1':fecha1,'v_f2':fecha2,'v_h1':hora1,'v_h2':hora2,'v_dir':dir_texto})
                datos = {'fondo':st.session_state.v_fondo,'desc1':desc1,'desc2':desc2,'fecha1':fecha1,'fecha2':fecha2,'hora1':hora1,'hora2':hora2,'lugar':dir_texto,'logos':rutas_logos}
                
                generated = {}
                num_lg = len(rutas_logos)
                
                if num_lg >= 1 and not fecha2 and not desc2:
                    generated = {'t5_v1':generar_tipo_5_v1(datos),'t5_v2':generar_tipo_5_v2(datos),'t5_v3':generar_tipo_5_v3(datos),'t5_v4':generar_tipo_5_v4(datos)}; tid=5
                elif fecha2 and desc2 and num_lg == 0:
                    generated = {'t4_v1':generar_tipo_4_v1(datos),'t4_v2':generar_tipo_4_v2(datos),'t4_v3':generar_tipo_4_v3(datos),'t4_v4':generar_tipo_4_v4(datos)}; tid=4
                elif fecha2 and not desc2 and num_lg == 0:
                    generated = {'t3_v1':generar_tipo_3_v1(datos),'t3_v2':generar_tipo_3_v2(datos),'t3_v3':generar_tipo_3_v3(datos),'t3_v4':generar_tipo_3_v4(datos)}; tid=3
                elif desc2 and not fecha2 and num_lg == 0:
                    generated = {'t2_v1':generar_tipo_2_v1(datos),'t2_v2':generar_tipo_2_v2(datos),'t2_v3':generar_tipo_2_v3(datos),'t2_v4':generar_tipo_2_v4(datos)}; tid=2
                elif num_lg == 0:
                    generated = {'v1':generar_tipo_1(datos),'v2':generar_tipo_1_v2(datos),'v3':generar_tipo_1_v3(datos),'v4':generar_tipo_1_v4(datos)}; tid=1
                
                st.session_state.update({'gen_imgs':generated, 'tid':tid, 'sel_var':list(generated.keys())[0]})
                st.query_params['area'] = 'Final'; st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    if 'gen_imgs' not in st.session_state:
        st.warning("No hay datos cargados.")
        if st.button("Volver al Inicio", type="primary"):
            st.session_state.clear(); st.query_params.clear(); st.rerun()
    else:
        imgs = st.session_state.gen_imgs
        sel = st.session_state.sel_var
        
        c_l, c_c, c_r = st.columns([1.5, 3, 1.5])
        
        with c_l:
            st.write("")
            if os.path.exists("mascota_pincel.png"): st.image("mascota_pincel.png", width=350)
            st.write("")
            if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=280)

        with c_c:
            st.image(imgs[sel], use_container_width=True)
            st.write("")
            c_p, c_d, c_n = st.columns([1, 2, 1])
            
            vars_list = list(imgs.keys())
            idx = vars_list.index(sel)

            with c_p:
                if len(vars_list) > 1: 
                    if st.button("⬅️", key="prev_btn", type="secondary"):
                        st.session_state.sel_var = vars_list[(idx-1)%len(vars_list)]; st.rerun()
            
            with c_d:
                buf = io.BytesIO()
                imgs[sel].save(buf, format="PNG")
                b64_dl = base64.b64encode(buf.getvalue()).decode()
                if os.path.exists("mascota_final.png"):
                    with open("mascota_final.png", "rb") as f: m_b64 = base64.b64encode(f.read()).decode()
                    html_btn = f"<div style='text-align: center;'><a href='data:image/png;base64,{b64_dl}' download='flyer_azuay.png' style='text-decoration: none;'><img src='data:image/png;base64,{m_b64}' width='220' class='zoom-hover'><div style='font-family: \"Canaro\"; font-weight: bold; font-size: 18px; color: white; margin-top: 5px;'>DESCARGUE AQUI</div></a></div>"
                    st.markdown(html_btn, unsafe_allow_html=True)
                else:
                    st.download_button("⬇️ DESCARGAR", buf.getvalue(), "flyer_azuay.png", "image/png", use_container_width=True)

            with c_n:
                if len(vars_list) > 1:
                    if st.button("➡️", key="next_btn", type="secondary"):
                        st.session_state.sel_var = vars_list[(idx+1)%len(vars_list)]; st.rerun()

        with c_r:
            st.empty()

    st.write("---")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("✏️ MODIFICAR DATOS", type="primary", use_container_width=True):
            st.query_params['area'] = st.session_state.get('v_area', 'Culturas')
            st.rerun()
    with cc2:
        if st.button("🔄 CREAR NUEVO", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            for item in os.listdir(os.getcwd()):
                if item.startswith("temp_") and item.endswith(".png"): os.remove(item)
            st.rerun()
