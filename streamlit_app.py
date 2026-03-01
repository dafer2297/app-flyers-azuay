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
    y_loc_top = min(y_loc_text_top, y_loc_icon_top) # PUNTO EXACTO SUPERIOR

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

    total_h_date_block = h_caja + 72 + 72 + (size_h / 2)
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
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Ancho MAX REDUCIDO A 900px)
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 150
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

    # 2. Calculo Caja (Apilada EXACTAMENTE a 100px)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho 900)
    limit_y = y_box_top - 50
    y_start_desc1 = y_titulo + 150
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

# ==============================================================================
# 4. GENERADORES DE PLANTILLAS TIPO 2
# ==============================================================================

def generar_tipo_2_v1(datos):
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

    # 1. Calculo Ubicacion (Derecha)
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    y_loc_text_top = Y_BOTTOM_BASELINE - total_h_loc
    y_loc_icon_top = Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2)
    y_loc_top = min(y_loc_text_top, y_loc_icon_top)

    # 2. Caja Fecha (Izquierda)
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    # Descripcion 2 (Izquierda, sobre la caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 34 - total_h_d2

    # Titulo (Centro)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Descripcion 2
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

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

def generar_tipo_2_v2(datos):
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

    # 2. Calculo Caja (Apilada a 100px)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # 3. Firma y Desc2 (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_firma_top - 85 - total_h_d2

    # Titulo (Centro)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    # 4. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Desc2
    if desc2 and firma:
        cx_firma = W - SIDE_MARGIN - (firma.width // 2) - 60
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1) / 2
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, cx_firma, y_cursor_d2, f_desc2, offset=(4,4), anchor="mm")
            y_cursor_d2 += int(s_desc2 * 1.1)

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

    return img.convert("RGB")

def generar_tipo_2_v3(datos):
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

    # Caja Fecha (Izquierda)
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    # Descripcion 2 (Izquierda, sobre la caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Titulo (Izquierda)
    y_titulo = 750
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    # 3. Descripcion 1 (DINAMICA, Izquierda, Ancho MAX REDUCIDO A 900)
    limit_y = min(y_desc2_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 150
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Descripcion 2
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

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
def generar_tipo_2_v4(datos):
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

    # 2. Calculo Caja Fecha (Apilada a 100px)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # 3. Firma y Desc2 (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_firma_top - 85 - total_h_d2

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # Descripcion 1 (DINAMICA, Izquierda, Max Ancho reducido a 900)
    limit_y = min(y_box_top, y_desc2_top) - 50
    y_start_desc1 = y_titulo + 150
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Desc2
    if desc2 and firma:
        cx_firma = W - SIDE_MARGIN - (firma.width // 2) - 60
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1) / 2
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, cx_firma, y_cursor_d2, f_desc2, offset=(4,4), anchor="mm")
            y_cursor_d2 += int(s_desc2 * 1.1)

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

# ==============================================================================
# 5. GENERADORES DE PLANTILLAS TIPO 3 (1 Párrafo, 2 Fechas, 0 Logos)
# ==============================================================================

def generar_tipo_3_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136) 
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

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

    # 2. Caja Larga Fecha (Izquierda, Fija)
    h_caja = 299
    w_caja = 663 
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = Y_BOTTOM_BASELINE - 50 - h_caja_block 

    # Titulo Centro
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Caja Larga
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion Derecha
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

def generar_tipo_3_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

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

    # 2. Caja Larga Fecha (Izquierda, Apilada 100px)
    GAP_LOC_BOX = 100
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # Titulo Centro
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))

    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja Larga
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_3_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

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

    # Caja Fecha Larga (Izquierda Fija)
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = Y_BOTTOM_BASELINE - 50 - h_caja_block

    # Titulo (Izquierda)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho reducido a 900)
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 150
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

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

def generar_tipo_3_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

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

    # 2. Caja Larga Fecha (Izquierda, Apilada 100px)
    GAP_LOC_BOX = 100
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho 900)
    limit_y = min(y_box_top, y_firma_top) - 50
    y_start_desc1 = y_titulo + 150
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
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    
    y_hora = y_box_top + h_caja + 38 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 6. GENERADORES DE PLANTILLAS TIPO 4
# ==============================================================================

def generar_tipo_4_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

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

    # Caja Fecha Larga (Izquierda Fija)
    h_caja = 299
    w_caja = 663 
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = Y_BOTTOM_BASELINE - 50 - h_caja_block

    # Descripcion 2 (Izquierda, arriba de Caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68 
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Titulo Centro
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Desc2
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion Derecha
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

def generar_tipo_4_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

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

    # 2. Caja Fecha Larga (Izquierda, Apilada 100px)
    GAP_LOC_BOX = 100
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # Firma y Desc2 (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_firma_top - 85 - total_h_d2

    # Titulo Centro
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Desc2
    if desc2 and firma:
        cx_firma = W - SIDE_MARGIN - (firma.width // 2) - 60
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1) / 2
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, cx_firma, y_cursor_d2, f_desc2, offset=(4,4), anchor="mm")
            y_cursor_d2 += int(s_desc2 * 1.1)

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_4_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

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

    # Caja Fecha Larga (Izquierda Fija)
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = Y_BOTTOM_BASELINE - 50 - h_caja_block

    # Descripcion 2 (Izquierda, arriba caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Titulo (Izquierda)
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho reducido a 900)
    limit_y = min(y_desc2_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 150
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Desc 2
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 38
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion Derecha
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
def generar_tipo_4_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 136)
    f_mes_largo = get_font("Canaro-Black.ttf", 110)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

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

    # 2. Caja Larga Fecha (Izquierda, Apilada 100px)
    GAP_LOC_BOX = 100
    h_caja = 299
    w_caja = 663
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    h_caja_block = h_caja + 38 + size_h
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho 900px)
    limit_y = min(y_box_top, y_firma_top) - 50
    y_start_desc1 = y_titulo + 150
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
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha_larga.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    
    draw.text((cx, cy - 38), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 80), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    
    y_hora = y_box_top + h_caja + 38 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 7. GENERADORES DE PLANTILLAS TIPO 5 (1 Parrafo, 1 Fecha, 1 Colaborador)
# ==============================================================================

def generar_tipo_5_v1(datos):
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

    # Logo Colaborador (Abajo a la Izquierda)
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA"))
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height
            # Alineado exactamente a la izquierda (SIDE_MARGIN)
            img.paste(collab_img, (SIDE_MARGIN, int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    # 2. Caja Fecha (Izquierda, Apilada 100px sobre el logo colaborador)
    GAP_COLLAB_BOX = 100
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
    y_box_top = y_logo_collab_top - GAP_COLLAB_BOX - total_h_date_block

    # Titulo Centro
    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    cx_box = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx_box, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")

    y_dia_txt = y_box_top + h_caja + 72
    y_hora_txt = y_dia_txt + 72
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx_box, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

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

def generar_tipo_5_v2(datos):
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

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA"))
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

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

    # 2. Caja Fecha (Apilada 100px arriba de Ubicacion)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo Centro
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 3. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2))), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")

def generar_tipo_5_v3(datos):
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

    # Logo Colaborador (Abajo Izquierda)
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA"))
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height
            # Alineado exactamente a la izquierda
            img.paste(collab_img, (SIDE_MARGIN, int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    # Caja Fecha (Izquierda, Apilada 100px sobre el logo colaborador)
    GAP_COLLAB_BOX = 100
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
    y_box_top = y_logo_collab_top - GAP_COLLAB_BOX - total_h_date_block

    # Titulo (Izquierda)
    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho 900px)
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 150
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

    cx_box = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx_box, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")

    y_dia_txt = y_box_top + h_caja + 72
    y_hora_txt = y_dia_txt + 72
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx_box, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

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

def generar_tipo_5_v4(datos):
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

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA"))
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

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

    # 2. Caja Fecha (Apilada 100px arriba)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 325)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 3. Descripcion 1 (DINAMICA, Izquierda, Max Ancho 900)
    limit_y = min(y_box_top, y_firma_top) - 50
    y_start_desc1 = y_titulo + 150
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
        
    curr_y_loc = Y_BOTTOM_BASELINE - total_h_loc + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")


# ==============================================================================
# NUEVO: 8. GENERADOR DE PLANTILLA TIPO 6 (3 Logos, 2 Descripciones, 1 Fecha)
# ==============================================================================

def generar_tipo_6_v1(datos):
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

    # 1. LOGICA DE DISTRIBUCION EQUITATIVA DE LOS 3 LOGOS SUPERIORES
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            collab_img = redimensionar_logo_colaborador(Image.open(datos['logos'][0]).convert("RGBA"))
        except Exception as e: pass

    prefectura_img = None
    if os.path.exists("flyer_logo.png"):
        prefectura_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    firma_img = None
    if os.path.exists("flyer_firma.png"):
        firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 600)

    w1 = collab_img.width if collab_img else 0
    w2 = prefectura_img.width if prefectura_img else 0
    w3 = firma_img.width if firma_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4 # Cuatro espacios iguales

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if collab_img: img.paste(collab_img, (int(x1), y_logos), collab_img)
    if prefectura_img: img.paste(prefectura_img, (int(x2), y_logos), prefectura_img)
    if firma_img: img.paste(firma_img, (int(x3), y_logos), firma_img)

    # 2. Calculo Ubicacion (Derecha)
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    y_loc_text_top = Y_BOTTOM_BASELINE - total_h_loc
    y_loc_icon_top = Y_BOTTOM_BASELINE - (total_h_loc/2) - (h_icon/2)
    y_loc_top = min(y_loc_text_top, y_loc_icon_top)

    # 3. Caja Fecha (Izquierda)
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    # 4. Descripcion 2 (Izquierda, sobre la caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 34 - total_h_d2

    # Titulo (Centro) (CORREGIDO A 850 PARA MANTENER LA ARMONÍA)
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 5. Descripcion 1 Centro (LOGICA ORIGINAL)
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

    # Dibujar Descripcion 2
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

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

# ==============================================================================
# 9. INTERFAZ DE USUARIO Y LOGICA PRINCIPAL
# ==============================================================================

if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: 
        st.image("logo_superior.png", use_container_width=True)

query_params = st.query_params
area_seleccionada = query_params.get("area", None)

if not area_seleccionada:
    st.markdown("<h2 style='text-align: center;'>SELECCIONA EL DEPARTAMENTO:</h2>", unsafe_allow_html=True)
    st.write("---")
    col1, col_cultura, col_recreacion, col4 = st.columns([1, 2, 2, 1])
    
    with col_cultura:
        if os.path.exists("btn_cultura.png"):
            img_b64 = get_base64_of_bin_file("btn_cultura.png")
            st.markdown(f"<a href='?area=Culturas' target='_self' style='text-decoration:none;'><div style='text-align: center;'><img src='data:image/png;base64,{img_b64}' class='zoom-hover' width='100%'><div class='label-menu'>CULTURAS</div></div></a>", unsafe_allow_html=True)
    with col_recreacion:
        if os.path.exists("btn_recreacion.png"):
            img_b64 = get_base64_of_bin_file("btn_recreacion.png")
            st.markdown(f"<a href='?area=Recreación' target='_self' style='text-decoration:none;'><div style='text-align: center;'><img src='data:image/png;base64,{img_b64}' class='zoom-hover' width='100%'><div class='label-menu'>RECREACIÓN</div></div></a>", unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
         if os.path.exists("firma_jota.png"): 
             st.image("firma_jota.png", width=300)

elif area_seleccionada in ["Culturas", "Recreación"]:
    st.session_state['v_area'] = area_seleccionada
    if st.button("⬅️ VOLVER AL INICIO", type="primary"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    col_izq, col_der = st.columns([1, 2], gap="large")
    with col_izq:
        st.write("")
        icono = "icono_cultura.png" if area_seleccionada == "Culturas" else "icono_recreacion.png"
        if os.path.exists(icono): 
            st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): 
            st.image("firma_jota.png", width=200)

    with col_der:
        st.markdown("<div class='label-negro'>DESCRIPCIÓN 1</div>", unsafe_allow_html=True)
        desc1 = st.text_area("d1", key="d1", label_visibility="collapsed", placeholder="Escribe aqui...", height=150, max_chars=175, value=st.session_state.get('v_d1', ""))
        
        st.markdown("<div class='label-negro'>DESCRIPCIÓN 2 (OPCIONAL)</div>", unsafe_allow_html=True)
        desc2 = st.text_area("d2", key="d2", label_visibility="collapsed", placeholder="", height=100, max_chars=175, value=st.session_state.get('v_d2', ""))
        
        total_chars = len(desc1) + len(desc2)
        color_c = "red" if total_chars > 175 else "black"
        st.markdown(f"<p style='text-align:right; color:{color_c}; font-size:12px; margin-top:-10px;'>Total caracteres: {total_chars} / 175</p>", unsafe_allow_html=True)

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown("<div class='label-negro'>FECHA INICIO</div>", unsafe_allow_html=True)
            fecha1 = st.date_input("f1", key="f1", label_visibility="collapsed", format="DD/MM/YYYY", value=st.session_state.get('v_f1', None))
        with c_f2:
            st.markdown("<div class='label-negro'>FECHA FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            fecha2 = st.date_input("f2", key="f2", label_visibility="collapsed", value=st.session_state.get('v_f2', None), format="DD/MM/YYYY")
        
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown("<div class='label-negro'>HORARIO INICIO</div>", unsafe_allow_html=True)
            hora1 = st.time_input("h1", key="h1", label_visibility="collapsed", value=st.session_state.get('v_h1', datetime.time(9, 0)))
        with c_h2:
            st.markdown("<div class='label-negro'>HORARIO FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            hora2 = st.time_input("h2", key="h2", label_visibility="collapsed", value=st.session_state.get('v_h2', None))
        
        st.markdown("<div class='label-negro'>DIRECCIÓN</div>", unsafe_allow_html=True)
        dir_texto = st.text_input("dir", key="dir", label_visibility="collapsed", placeholder="Ubicación del evento", max_chars=80, value=st.session_state.get('v_dir', ""))
        st.markdown(f"<p style='text-align:right; color:black; font-size:12px; margin-top:-10px;'>Caracteres: {len(dir_texto)} / 80</p>", unsafe_allow_html=True)
        
        st.markdown("<div class='label-negro'>LOGOS COLABORADORES (OPCIONAL)</div>", unsafe_allow_html=True)
        
        rutas_memoria = st.session_state.get('rutas_logos', [])
        if rutas_memoria and os.path.exists(rutas_memoria[0]):
            st.success("✅ LOGO COLABORADOR GUARDADO.")
            if st.button("❌ ELIMINAR LOGO GUARDADO", type="primary"):
                st.session_state['rutas_logos'] = []
                st.rerun()
            
        logos = st.file_uploader("lg", key="lg", accept_multiple_files=True, label_visibility="collapsed")
        
        st.markdown("<div class='label-negro' style='margin-top: 15px;'>SUBIR Y RECORTAR IMAGEN DE FONDO</div>", unsafe_allow_html=True)
        if 'v_fondo' in st.session_state:
            st.success("✅ IMAGEN DE FONDO GUARDADA. Sube una nueva solo si quieres reemplazarla.")
        
        archivo_subido = st.file_uploader("img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte. Recuerda usar imagenes de buena calidad.")
            img_crop = st_cropper(img_orig, realtime_update=True, aspect_ratio=(4, 5), should_resize_image=False)
            st.session_state['v_fondo'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Nueva imagen lista.")

        st.write("")
        if st.button("✨ GENERAR FLYERS ✨", type="primary", use_container_width=True):
            errores = []
            if not desc1: errores.append("Falta Descripcion 1")
            if not fecha1: errores.append("Falta Fecha Inicio")
            if 'v_fondo' not in st.session_state: errores.append("Falta recortar la Imagen de Fondo")
            if total_chars > 175: errores.append("Excediste el limite de 175 caracteres combinados")

            if errores:
                for e in errores: st.error(f"⚠️ {e}")
            else:
                rutas_logos = st.session_state.get('rutas_logos', [])
                
                if logos:
                    rutas_logos = []
                    for i, l in enumerate(logos):
                        with open(f"temp_{i}.png", "wb") as f: 
                            f.write(l.getvalue())
                        rutas_logos.append(f"temp_{i}.png")
                
                st.session_state.update({
                    'v_d1': desc1,
                    'v_d2': desc2,
                    'v_f1': fecha1,
                    'v_f2': fecha2,
                    'v_h1': hora1,
                    'v_h2': hora2,
                    'v_dir': dir_texto,
                    'rutas_logos': rutas_logos
                })

                datos = {
                    'fondo': st.session_state.v_fondo,
                    'desc1': desc1,
                    'desc2': desc2,
                    'fecha1': fecha1,
                    'fecha2': fecha2,
                    'hora1': hora1,
                    'hora2': hora2,
                    'lugar': dir_texto,
                    'logos': rutas_logos
                }
                
                generated = {}
                num_lg = len(rutas_logos)
                
                # ENRUTAMIENTO INTELIGENTE INCLUYENDO TIPO 6 (3 logos arriba, 2 descripciones)
                if num_lg >= 1 and not fecha2 and desc2:
                    generated = {'t6_v1': generar_tipo_6_v1(datos)}
                    tid = 6
                elif num_lg >= 1 and not fecha2 and not desc2:
                    generated = {'t5_v1': generar_tipo_5_v1(datos), 't5_v2': generar_tipo_5_v2(datos), 't5_v3': generar_tipo_5_v3(datos), 't5_v4': generar_tipo_5_v4(datos)}
                    tid = 5
                elif fecha2 and desc2 and num_lg == 0:
                    generated = {'t4_v1': generar_tipo_4_v1(datos), 't4_v2': generar_tipo_4_v2(datos), 't4_v3': generar_tipo_4_v3(datos), 't4_v4': generar_tipo_4_v4(datos)}
                    tid = 4
                elif fecha2 and not desc2 and num_lg == 0:
                    generated = {'t3_v1': generar_tipo_3_v1(datos), 't3_v2': generar_tipo_3_v2(datos), 't3_v3': generar_tipo_3_v3(datos), 't3_v4': generar_tipo_3_v4(datos)}
                    tid = 3
                elif desc2 and not fecha2 and num_lg == 0:
                    generated = {'t2_v1': generar_tipo_2_v1(datos), 't2_v2': generar_tipo_2_v2(datos), 't2_v3': generar_tipo_2_v3(datos), 't2_v4': generar_tipo_2_v4(datos)}
                    tid = 2
                elif num_lg == 0:
                    generated = {'v1': generar_tipo_1(datos), 'v2': generar_tipo_1_v2(datos), 'v3': generar_tipo_1_v3(datos), 'v4': generar_tipo_1_v4(datos)}
                    tid = 1
                
                st.session_state.update({'gen_imgs': generated, 'tid': tid, 'sel_var': list(generated.keys())[0]})
                st.query_params['area'] = 'Final'
                st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
    st.write("") 
    
    if 'gen_imgs' not in st.session_state:
        st.warning("No hay datos cargados.")
        if st.button("Volver al Inicio", type="primary"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    else:
        imgs = st.session_state.gen_imgs
        sel = st.session_state.sel_var
        
        c_l, c_c, c_r = st.columns([1.5, 3, 1.5])
        
        with c_l:
            st.write("")
            if os.path.exists("mascota_pincel.png"): 
                st.image("mascota_pincel.png", width=350)
            st.write("")
            if os.path.exists("firma_jota.png"): 
                st.image("firma_jota.png", width=280)

        with c_c:
            st.image(imgs[sel], use_container_width=True)
            st.write("")
            c_p, c_d, c_n = st.columns([1, 2, 1])
            
            vars_list = list(imgs.keys())
            idx = vars_list.index(sel)

            with c_p:
                if len(vars_list) > 1: 
                    if st.button("⬅️", key="prev_btn", type="secondary"):
                        st.session_state.sel_var = vars_list[(idx-1)%len(vars_list)]
                        st.rerun()
            
            with c_d:
                buf = io.BytesIO()
                imgs[sel].save(buf, format="PNG")
                b64_dl = base64.b64encode(buf.getvalue()).decode()
                
                if os.path.exists("mascota_final.png"):
                    with open("mascota_final.png", "rb") as f: 
                        m_b64 = base64.b64encode(f.read()).decode()
                    
                    html_btn = (
                        "<div style='text-align: center;'>"
                        f"<a href='data:image/png;base64,{b64_dl}' download='flyer_azuay_{sel}.png' style='text-decoration: none; border: none !important; outline: none !important;'>"
                        f"<img src='data:image/png;base64,{m_b64}' width='220' class='zoom-hover' style='border: none !important; outline: none !important; display: block; margin: auto;'>"
                        "<div style='font-family: \"Canaro\"; font-weight: bold; font-size: 18px; color: white; margin-top: 5px; text-decoration: none;'>DESCARGUE AQUI</div>"
                        "</a></div>"
                    )
                    st.markdown(html_btn, unsafe_allow_html=True)
                else:
                    st.download_button("⬇️ DESCARGAR", buf.getvalue(), f"flyer_azuay_{sel}.png", "image/png", use_container_width=True)

            with c_n:
                if len(vars_list) > 1:
                    if st.button("➡️", key="next_btn", type="secondary"):
                        st.session_state.sel_var = vars_list[(idx+1)%len(vars_list)]
                        st.rerun()

        with c_r:
            st.empty()

    st.write("---")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("✏️ MODIFICAR DATOS", type="primary", use_container_width=True):
            st.query_params['area'] = st.session_state.get('v_area', 'Culturas')
            st.rerun()
    with cc2:
        if st.button("🔄 CREAR NUEVO", type="primary", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            for item in os.listdir(os.getcwd()):
                if item.startswith("temp_") and item.endswith(".png"): 
                    os.remove(item)
            st.rerun()
