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

def set_design():
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = "background-image: url('data:image/png;base64," + bin_str + "'); background-size: cover; background-position: center; background-attachment: fixed;"

    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css += "@font-face { font-family: 'Canaro'; src: url('data:font/ttf;base64," + font_b64 + "') format('truetype'); }\n"

    css_str = (
        "<style>\n"
        + ".stApp { " + bg_style + " }\n"
        + font_css +
        "h1, h2, h3 { font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }\n"
        "div[data-testid='stButton'] button[kind='primary'] { background-color: transparent; color: white; border: 2px solid white; border-radius: 15px; width: 100%; height: auto; padding: 10px 20px; font-weight: bold; font-size: 16px; box-shadow: none; }\n"
        "div[data-testid='stButton'] button[kind='primary']:hover { background-color: #D81B60; border-color: #D81B60; transform: none; }\n"
        ".stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label, .stFileUploader label { display: none !important; }\n"
        ".label-negro { font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; }\n"
        ".label-blanco { font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }\n"
        ".label-menu { font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 20px; color: white !important; margin-top: 10px; text-transform: uppercase; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); text-decoration: none !important; }\n"
        "a { text-decoration: none !important; }\n"
        "a img { border: none !important; outline: none !important; box-shadow: none !important; }\n"
        ".zoom-hover { transition: transform 0.2s; cursor: pointer; }\n"
        ".zoom-hover:hover { transform: scale(1.05); }\n"
        "#MainMenu, footer, header { visibility: hidden; }\n"
        "</style>"
    )
    st.markdown(css_str, unsafe_allow_html=True)

set_design()

# ==============================================================================
# 2. MOTOR MATEMATICO Y AYUDANTES
# ==============================================================================

def dibujar_texto_sombra(draw, texto, x, y, fuente, color="white", sombra="black", offset=(12,12), anchor="mm"):
    draw.text((x+offset[0], y+offset[1]), texto, font=fuente, fill=sombra, anchor=anchor)
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)

def ruta_abs(nombre_archivo):
    return os.path.join(os.getcwd(), nombre_archivo)

def get_font(path_str, size):
    try: return ImageFont.truetype(ruta_abs(path_str), size)
    except: return ImageFont.load_default()

def obtener_mes_abbr(numero_mes):
    meses = {1:"ENE", 2:"FEB", 3:"MAR", 4:"ABR", 5:"MAY", 6:"JUN", 7:"JUL", 8:"AGO", 9:"SEP", 10:"OCT", 11:"NOV", 12:"DIC"}
    return meses.get(numero_mes, "")

def obtener_mes_nombre(numero_mes):
    meses = {1:"ENERO", 2:"FEBRERO", 3:"MARZO", 4:"ABRIL", 5:"MAYO", 6:"JUNIO", 7:"JULIO", 8:"AGOSTO", 9:"SEPTIEMBRE", 10:"OCTUBRE", 11:"NOVIEMBRE", 12:"DICIEMBRE"}
    return meses.get(numero_mes, "")

def obtener_dia_semana(fecha):
    dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
    return dias[fecha.weekday()]

def resize_por_alto(img, alto_objetivo):
    ratio = alto_objetivo / img.height
    ancho_nuevo = int(img.width * ratio)
    return img.resize((ancho_nuevo, alto_objetivo), Image.Resampling.LANCZOS)

def resize_por_ancho(img, ancho_objetivo):
    ratio = ancho_objetivo / img.width
    alto_nuevo = int(img.height * ratio)
    return img.resize((ancho_objetivo, alto_nuevo), Image.Resampling.LANCZOS)

def redimensionar_logo_colaborador(img):
    w, h = img.size
    if w == h: return resize_por_alto(img, 400)
    ratio = 400 / h
    new_w = int(w * ratio)
    if new_w <= 700: return img.resize((new_w, 400), Image.Resampling.LANCZOS)
    else:
        ratio = 700 / w
        new_h = int(h * ratio)
        return img.resize((700, new_h), Image.Resampling.LANCZOS)

def redimensionar_logo_colaborador_top(img):
    w, h = img.size
    ratio = 300 / h
    new_w = int(w * ratio)
    if new_w <= 600: return img.resize((new_w, 300), Image.Resampling.LANCZOS)
    else:
        ratio = 600 / w
        new_h = int(h * ratio)
        return img.resize((600, new_h), Image.Resampling.LANCZOS)

# NUEVA REGLA: Logo colaborador TIPO 9 (Alto max 300, Ancho max 600)
def redimensionar_logo_colaborador_tipo9(img):
    w, h = img.size
    ratio = 300 / h
    new_w = int(w * ratio)
    if new_w <= 600:
        return img.resize((new_w, 300), Image.Resampling.LANCZOS)
    else:
        ratio = 600 / w
        new_h = int(h * ratio)
        return img.resize((600, new_h), Image.Resampling.LANCZOS)

def get_text_width(font, text):
    if hasattr(font, 'getbbox'): return font.getbbox(text)[2] - font.getbbox(text)[0]
    else: return font.getmask(text).getbbox()[2]

def wrap_text_pixel(texto, fuente, max_w):
    if not texto: return []
    palabras = texto.split()
    lineas, linea_actual = [], ""
    for p in palabras:
        test_linea = linea_actual + " " + p if linea_actual else p
        if get_text_width(fuente, test_linea) <= max_w: linea_actual = test_linea
        else:
            if linea_actual: lineas.append(linea_actual)
            linea_actual = p
    if linea_actual: lineas.append(linea_actual)
    return lineas

def calcular_fuente_dinamica(texto, font_file, size_start, max_w, max_h):
    s_desc = size_start
    while s_desc > 40:
        f_desc = get_font(font_file, s_desc)
        lineas = wrap_text_pixel(texto, f_desc, max_w)
        h_total = len(lineas) * int(s_desc * 1.1)
        if h_total <= max_h: return f_desc, lineas, s_desc
        s_desc -= 5
    f_desc = get_font(font_file, 40)
    return f_desc, wrap_text_pixel(texto, f_desc, max_w), 40

# ==============================================================================
# 3. GENERADORES DE PLANTILLAS TIPO 1 
# ==============================================================================

def generar_tipo_1(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180
    Y_BOTTOM_BASELINE = H - 150
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    # Titulo Centro
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    # Descripcion 1 Centro 
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_width = 35
    elif chars_desc <= 120: size_desc_val = 90; wrap_width = 45
    elif chars_desc <= 150: size_desc_val = 75; wrap_width = 55
    else: size_desc_val = 65; wrap_width = 65

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 180
    for line in textwrap.wrap(datos['desc1'], width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.1)

    # Ubicacion Derecha
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    # Caja Izquierda
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + 72
    y_hora_txt = y_dia_txt + 72
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        
    curr_y = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(3,3))
        curr_y += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_1_v2(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180
    Y_BOTTOM_BASELINE = H - 150
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # Firma Derecha
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    # 1. Calculo EXACTO de la parte superior del Bloque Ubicacion
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    y_loc_text_top = Y_BOTTOM_BASELINE - total_h_loc
    y_loc_icon_top = Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2)
    y_loc_top = min(y_loc_text_top, y_loc_icon_top)

    # 2. Calculo Caja Fecha
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Titulo
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    # Descripcion 1 Centro
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_width = 35
    elif chars_desc <= 120: size_desc_val = 90; wrap_width = 45
    elif chars_desc <= 150: size_desc_val = 75; wrap_width = 55
    else: size_desc_val = 65; wrap_width = 65

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 180
    for line in textwrap.wrap(datos['desc1'], width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + 72
    y_hora_txt = y_dia_txt + 72
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lugar, anchor="ls", offset=(3,3))
        curr_y += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_1_v3(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180
    Y_BOTTOM_BASELINE = H - 150
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 1. Calculo Exacto Ubicacion (Derecha)
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    y_loc_text_top = Y_BOTTOM_BASELINE - total_h_loc
    y_loc_icon_top = Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2)
    y_loc_top = min(y_loc_text_top, y_loc_icon_top)

    # 2. Caja Fecha (Izquierda, No Apilada)
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    # Titulo (Izquierda)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda) - BAJADO 30PX
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + 72
    y_hora_txt = y_dia_txt + 72
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        
    curr_y = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y, f_lugar, anchor="ls", offset=(3,3))
        curr_y += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_1_v4(datos):
    fondo = datos['fondo'].copy()
    W, H = 2400, 3000
    SIDE_MARGIN = 180
    Y_BOTTOM_BASELINE = H - 150
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # Firma (Derecha)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    # 1. Calculo Exacto Ubicacion (Izquierda)
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    y_loc_text_top = Y_BOTTOM_BASELINE - total_h_loc
    y_loc_icon_top = Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2)
    y_loc_top = min(y_loc_text_top, y_loc_icon_top)

    # 2. Calculo Caja (Apilada)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda) - BAJADO 30PX
    limit_y = y_box_top - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y, f_lugar, anchor="ls", offset=(3,3))
        curr_y += int(s_lug * 1.1)

    # Dibujar Caja
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + 72
    y_hora_txt = y_dia_txt + 72
    
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

    return img.convert("RGB")
