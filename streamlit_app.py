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
st.set_page_config(page_title="Generador Azuay - Culturas", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design():
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"background-image: url('data:image/png;base64,{bin_str}'); background-size: cover; background-position: center; background-attachment: fixed;"

    font_css = ""
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css += f"@font-face {{ font-family: 'Canaro'; src: url('data:font/ttf;base64,{font_b64}') format('truetype'); }}\n"

    css_str = (
        "<style>\n"
        + ".stApp { " + bg_style + " }\n"
        + font_css +
        "h1, h2, h3 { font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }\n"
        "div[data-testid='stButton'] button[kind='primary'] { background-color: transparent; color: white; border: 2px solid white; border-radius: 15px; width: 100%; height: auto; padding: 10px 20px; font-weight: bold; font-size: 16px; box-shadow: none; }\n"
        "div[data-testid='stButton'] button[kind='primary']:hover { background-color: #D81B60; border-color: #D81B60; transform: none; }\n"
        ".stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label, .stFileUploader label { display: none !important; }\n"
        ".label-negro { font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; }\n"
        ".label-menu { font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 20px; color: white !important; margin-top: 10px; text-transform: uppercase; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); text-decoration: none !important; }\n"
        "a { text-decoration: none !important; }\n"
        ".zoom-hover { transition: transform 0.2s; cursor: pointer; }\n"
        ".zoom-hover:hover { transform: scale(1.05); }\n"
        "#MainMenu, footer, header { visibility: hidden; }\n"
        "</style>"
    )
    st.markdown(css_str, unsafe_allow_html=True)

set_design()

# ==============================================================================
# 2. MOTOR MATEMÁTICO Y AYUDANTES COMPLETOS
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

def redimensionar_logo_interno(img, tipo_logo):
    if tipo_logo == "movida":
        return resize_por_ancho(img, 600)
    elif tipo_logo == "orquesta":
        return resize_por_alto(img, 375)
    return img

def redimensionar_logo_interno_compartido(img, tipo_logo):
    if tipo_logo == "movida":
        return resize_por_ancho(img, 500)
    elif tipo_logo == "orquesta":
        return resize_por_alto(img, 325)
    return img

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
# 3. GENERADORES DE PLANTILLAS TIPO 1 (1 Desc, 1 Fecha, 0 Collab)
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN 60px
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    
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

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

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

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(Y_BOTTOM_BASELINE - firma.height + 50)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = y_box_top - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
# 4. GENERADORES DE PLANTILLAS TIPO 2 (1 Desc, 1 Fecha, Desc 2, 0 Collab)
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    f_invita = get_font("Canaro-Bold.ttf", 220)
    f_dia_box = get_font("Canaro-Black.ttf", 297)
    f_mes_box = get_font("Canaro-Black.ttf", 170)
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 750
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_desc2_top, y_loc_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

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

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
# 5. GENERADORES DE PLANTILLAS TIPO 3 (Recuadro Largo Dinámico con Gap Corregido)
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)  

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360 
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    y_box_top = Y_BOTTOM_BASELINE - 72 - h_caja 

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72 
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    y_box_top = Y_BOTTOM_BASELINE - 72 - h_caja

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_firma_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    
    y_hora = y_box_top + h_caja + 72 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 6. GENERADORES DE PLANTILLAS TIPO 4 (Recuadro Largo Dinámico, 2 Descripciones)
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
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN A 265px
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    # 1. Calculo Exacto Ubicacion (Derecha) - ALINEACION INFERIOR EXACTA
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Fecha Larga (Izquierda Fija, Ancho Dinámico)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360 
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Hereda distancia exacta
    y_box_top = Y_BOTTOM_BASELINE - 72 - h_caja

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
    
    # 3. Descripcion 1 Centro
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

    # Dibujar Caja Larga (Dinámica)
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion Derecha
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # 1. Calculo Exacto Ubicacion (Izquierda) - ALINEACION INFERIOR
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Larga Fecha (Izquierda, Ancho Dinámico, Apilada sobre ubicacion)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Hereda la distancia exacta de apilamiento
    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # 3. Descripcion 2 (Izquierda, Apilada sobre la caja de fecha)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Firma (Derecha Abajo)
    y_firma_top = Y_BOTTOM_BASELINE
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN A 265px
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo Centro
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 4. Descripcion 1 Centro
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

    # Dibujar Desc2 (Izquierda sobre la caja)
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    # Dibujar Ubicacion (Izquierda Abajo)
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72 
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
    else:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

    f_invita = get_font("Canaro-Bold.ttf", 220)
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN A 265px
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 1. Calculo Exacto Ubicacion (Derecha) - ALINEACION INFERIOR
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # Caja Fecha Larga (Izquierda Fija, Ancho Dinámico)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Hereda distancia
    y_box_top = Y_BOTTOM_BASELINE - 72 - h_caja

    # Descripcion 2 (Izquierda, arriba caja)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Titulo (Izquierda)
    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    # 3. Descripcion 1 (DINAMICA, Izquierda) - Bajado 30px
    limit_y = min(y_desc2_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 180 
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

    # Dibujar Caja Larga (Dinámica)
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    # Dibujar Ubicacion Derecha
    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    # 1. Calculo Exacto Ubicacion (Izquierda) - ALINEACION INFERIOR
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Larga Fecha (Izquierda, Ancho Dinámico, Apilada sobre ubicacion)
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Hereda distancia del cuadrado
    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # 3. Descripcion 2 (Izquierda, apilada sobre la caja de fecha)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN A 265px
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 4. Descripcion 1 (DINAMICA, Izquierda) - Bajado 30px
    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Desc2 (Izquierda, sobre caja)
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    # Dibujar Ubicacion
    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    
    y_hora = y_box_top + h_caja + 72 
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
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCIÓN 60px
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 1. Calculo Exacto Ubicacion (Izquierda) <-- ALINEACION INFERIOR EXACTA
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Fecha (Izquierda, Apilada 100px sobre la ubicacion) 
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

    # 3. LOGO COLABORADOR (Abajo Derecha) CON MOTOR INTERNO + 20px
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20 
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    # Titulo Centro
    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 4. Descripcion 1 Centro 
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

    # Dibujar Ubicacion (Izquierda)
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
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

    cx_box = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    
    draw.text((cx_box, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")

    y_dia_txt = y_box_top + h_caja + 72
    y_hora_txt = y_dia_txt + 72
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx_box, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

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

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador_top(img_c)
                
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    # 2. Calculo Exacto Ubicacion (Izquierda) - ALINEACION INFERIOR
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 3. Caja Fecha (Apilada 100px arriba de Ubicacion)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCION A 265px
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo Centro
    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    # 4. Descripcion 1 Centro
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
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
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
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCION A 265px
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 1. Calculo Exacto Ubicacion (Izquierda) <-- ALINEACION INFERIOR EXACTA
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Fecha (Izquierda, Apilada 100px sobre ubicacion)
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

    # 3. LOGO COLABORADOR (Abajo Derecha) CON MOTOR INTERNO + 20px
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
                
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    # Titulo (Izquierda)
    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 4. Descripcion 1 (DINAMICA, Izquierda) - Bajado 30px
    limit_y = y_box_top - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    # Dibujar Ubicacion (Izquierda)
    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
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

    cx_box = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx_box, cy - 42), str(datos['fecha1'].day), font=f_dia_box, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 144), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_fecha, anchor="mm")

    y_dia_txt = y_box_top + h_caja + 72
    y_hora_txt = y_dia_txt + 72
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx_box, y_dia_txt, f_dia_semana, offset=(6,6), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora_txt, f_hora, offset=(6,6), anchor="mm")

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

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador_top(img_c)
                
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    # 2. Calculo Exacto Ubicacion (Izquierda) - ALINEACION INFERIOR
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 3. Caja Fecha (Apilada 100px arriba)
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # Firma (Derecha)
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) # REDUCCION A 265px
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Titulo (Izquierda)
    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    # 4. Descripcion 1 (DINAMICA, Izquierda) - Bajado 30px
    limit_y = min(y_box_top, y_firma_top) - 50
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
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
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
# 8. GENERADORES DE PLANTILLAS TIPO 6 (1 Fecha Cuadrada, 2 Desc, Logos Arriba)
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

    f_invita = get_font("Canaro-Bold.ttf", 220) 
    f_dia_box = get_font("Canaro-Black.ttf", 297) 
    f_mes_box = get_font("Canaro-Black.ttf", 170) 
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", 93) 

    # 1. 3 LOGOS SUPERIORES CON MOTOR INTERNO
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador_top(img_c)
        except Exception as e: pass

    prefectura_img = None
    if os.path.exists("flyer_logo.png"):
        prefectura_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    firma_img = None
    if os.path.exists("flyer_firma.png"):
        firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = collab_img.width if collab_img else 0
    w2 = prefectura_img.width if prefectura_img else 0
    w3 = firma_img.width if firma_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if collab_img: img.paste(collab_img, (int(x1), y_logos + (300 - collab_img.height)//2), collab_img)
    if prefectura_img: img.paste(prefectura_img, (int(x2), y_logos), prefectura_img)
    if firma_img: img.paste(firma_img, (int(x3), y_logos + (300 - firma_img.height)//2), firma_img)

    # 2. Calculo Ubicacion (Derecha) 
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 3. Caja Fecha (Izquierda)
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    # 4. Descripcion 2 (Izquierda)
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 34 - total_h_d2

    # Titulo (Centro) - 3 LOGOS ARRIBA = 690px
    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

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

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_6_v2(datos):
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

    # 1. 2 LOGOS ARRIBA CON MOTOR INTERNO
    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            x_collab = W - margin_logos_top - collab_img.width
            y_collab = 150 + (378 - collab_img.height) // 2
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    # 2. Calculo Exacto Ubicacion
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

def generar_tipo_6_v3(datos):
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

    # 1. 3 LOGOS SUPERIORES CON MOTOR INTERNO
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador_top(img_c)
        except Exception as e: pass

    prefectura_img = None
    if os.path.exists("flyer_logo.png"):
        prefectura_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    firma_img = None
    if os.path.exists("flyer_firma.png"):
        firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = collab_img.width if collab_img else 0
    w2 = prefectura_img.width if prefectura_img else 0
    w3 = firma_img.width if firma_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if collab_img: img.paste(collab_img, (int(x1), y_logos + (300 - collab_img.height)//2), collab_img)
    if prefectura_img: img.paste(prefectura_img, (int(x2), y_logos), prefectura_img)
    if firma_img: img.paste(firma_img, (int(x3), y_logos + (300 - firma_img.height)//2), firma_img)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    y_box_top = Y_BOTTOM_BASELINE - 144 - h_caja

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    # TITULO - REGLA 3 LOGOS = 690px
    y_titulo = 690
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_desc2_top, y_loc_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

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

    x_txt_anchor = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_txt_anchor - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_6_v4(datos):
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

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. 2 LOGOS ARRIBA CON MOTOR INTERNO
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            x_collab = W - margin_logos_top - collab_img.width
            y_collab = 150 + (378 - collab_img.height) // 2
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
# 9. GENERADORES DE PLANTILLAS TIPO 7 (Logo Collab Derecho, Loc Izq, 2 Fechas)
# ==============================================================================

def generar_tipo_7_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # 3. LOGO COLABORADOR (Derecha Abajo) + 20px CON MOTOR INTERNO
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_7_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_7_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # 3. LOGO COLABORADOR (Derecha Abajo) + 20px CON MOTOR INTERNO
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_7_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_firma_top) - 50
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 10. GENERADORES DE PLANTILLAS TIPO 8 (Logo Collab, 2 Fechas, 2 Desc)
# ==============================================================================

def generar_tipo_8_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    firma = None
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2) 
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # 3. LOGO COLABORADOR (Derecha Abajo) + 20px CON MOTOR INTERNO
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width 
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass
    
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_8_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_8_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 800)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_COLLAB_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_COLLAB_BOX - h_caja_block

    # 3. LOGO COLABORADOR (Derecha Abajo) + 20px CON MOTOR INTERNO
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width 
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except Exception as e: pass
    
    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 800)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)
        
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_8_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha) CON MOTOR INTERNO
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower():
                collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else:
                collab_img = redimensionar_logo_colaborador(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except Exception as e: pass

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = wrap_text_pixel(lugar, f_lugar, 1000)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)
        
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 10.1 REDIMENSIONADOR COMPARTIDO (PARA TIPOS 9, 10, 11 Y 12)
# ==============================================================================

def redimensionar_logo_interno_compartido(img, tipo_logo):
    """
    Cuando el logo de Culturas se comparte con otro colaborador en el mismo flyer.
    La movida = ancho 500
    La orquesta = alto 325
    """
    if tipo_logo == "movida":
        return resize_por_ancho(img, 500)
    elif tipo_logo == "orquesta":
        return resize_por_alto(img, 325)
    return img

# ==============================================================================
# 11. GENERADORES DE PLANTILLAS TIPO 9 (1 Desc, 1 Fecha Cuadrada, 2 Logos)
# ==============================================================================

def generar_tipo_9_v1(datos):
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

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    
    lines_loc = textwrap.wrap(lugar, width=19) # Regla 19
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    # 3. 2 Logos Colaboradores con Motor Inteligente Compartido
    collab1 = None
    collab2 = None
    logos_list = datos.get('logos', [])
    
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        x_cursor -= 65 # Separación extra de 15px (Total 65px)
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")

def generar_tipo_9_v2(datos):
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

    # 1. LOGOS ARRIBA CON MOTOR INTERNO
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    # 2. Firma 
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # 3. Calculo Ubicacion 
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 4. Calculo Caja 
    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # DISTANCIA APLICADA: 3 LOGOS = 690
    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

def generar_tipo_9_v3(datos):
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

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    # 3. 2 Logos Colaboradores (+20px, Margen 90) CON MOTOR
    collab1 = None
    collab2 = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    logos_list = datos.get('logos', [])
    
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab2.height + 20)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab1.height + 20)

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")

def generar_tipo_9_v4(datos):
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

    # 1. LOGOS ARRIBA CON MOTOR 
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_box_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
# 12. GENERADORES DE PLANTILLAS TIPO 10 (2 Desc, 1 Fecha, 2 Logos)
# ==============================================================================

def generar_tipo_10_v1(datos):
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

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 34 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")

def generar_tipo_10_v2(datos):
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

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

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

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

def generar_tipo_10_v3(datos):
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

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

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

    collab1 = collab2 = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    logos_list = datos.get('logos', [])
    
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab2.height + 20)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab1.height + 20)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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

    return img.convert("RGB")

def generar_tipo_10_v4(datos):
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

    # 1. LOGOS ARRIBA CON MOTOR
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
        
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 548
    w_caja = 548
    x_box = SIDE_MARGIN
    total_h_date_block = h_caja + 144
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

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
# NUEVO: 13. GENERADORES DE PLANTILLAS TIPO 11 (1 Desc, Caja Larga, 2 Logos)
# ==============================================================================

def generar_tipo_11_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 1. Calculo Exacto Ubicacion (Izquierda Abajo) - WRAP 19
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    
    lines_loc = textwrap.wrap(lugar, width=19) 
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 2. Caja Fecha Larga
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    # 3. 2 Logos Colaboradores con Motor Interno Compartido
    collab1 = None
    collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
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

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    # 1. LOGOS ARRIBA CON MOTOR COMPARTIDO
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0

    espacio_restante = W - (w1 + w2 + w3)
    gap = espacio_restante / 4

    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    # 2. Firma 
    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # 3. Calculo Exacto Ubicacion (Izquierda Abajo) - WRAP 19
    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # 4. Calculo Caja Larga
    GAP_LOC_BOX = 100
    h_caja = 360
    
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    # DISTANCIA EXACTA 3 LOGOS = 690px
    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

    # 5. Descripcion 1 Centro
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
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    # Dibujar Caja 
    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
        
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"

    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    collab1 = collab2 = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab2.height + 20)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab1.height + 20)

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_box_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_box_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# NUEVO: 14. GENERADORES DE PLANTILLAS TIPO 12 (2 Desc, Caja Larga, 2 Logos)
# ==============================================================================

def generar_tipo_12_v1(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19) 
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    GAP_LOC_BOX = 100
    h_caja_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - h_caja_block

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 34 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val, wrap_width = 110, 35
    elif chars_desc <= 120: size_desc_val, wrap_width = 90, 45
    elif chars_desc <= 150: size_desc_val, wrap_width = 75, 55
    else: size_desc_val, wrap_width = 65, 65

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 180
    for line in textwrap.wrap(datos['desc1'], width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v2(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)
    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(10,10))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val, wrap_width = 110, 35
    elif chars_desc <= 120: size_desc_val, wrap_width = 90, 45
    elif chars_desc <= 150: size_desc_val, wrap_width = 75, 55
    else: size_desc_val, wrap_width = 65, 65

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 180
    for line in textwrap.wrap(datos['desc1'], width=wrap_width):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v3(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51 
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    collab1 = collab2 = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab1 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab1 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                collab2 = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                collab2 = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass

    RIGHT_MARGIN = 90
    x_cursor = W - RIGHT_MARGIN
    if collab2:
        x_cursor -= collab2.width
        img.paste(collab2, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab2.height + 20)), collab2)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab2.height + 20)
        x_cursor -= 65 
    if collab1:
        x_cursor -= collab1.width
        img.paste(collab1, (int(x_cursor), int(Y_BOTTOM_BASELINE - collab1.height + 20)), collab1)
        y_logo_collab_top = min(y_logo_collab_top, Y_BOTTOM_BASELINE - collab1.height + 20)

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 700)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")
    
    limit_y = min(y_desc2_top, y_logo_collab_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110 
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v4(datos):
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
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        path = logos_list[0]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c1_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c1_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if len(logos_list) > 1:
        path = logos_list[1]
        try:
            img_c = Image.open(path).convert("RGBA")
            if "logo.movida" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(path).lower():
                c2_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else:
                c2_img = redimensionar_logo_colaborador_tipo9(img_c)
        except: pass
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if c1_img: img.paste(c1_img, (int(x1), y_logos + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), y_logos + (300 - c2_img.height)//2), c2_img)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    lugar = datos['lugar']
    s_lug = 61 if len(lugar) < 45 else 51
    f_lugar = get_font("Canaro-Medium.ttf", s_lug)
    lines_loc = textwrap.wrap(lugar, width=19)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_icon = 221
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    GAP_LOC_BOX = 100
    h_caja = 360
    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    mes_nombre = obtener_mes_nombre(datos['fecha1'].month)
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, mes_nombre)
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    cx_box = x_box + (w_caja / 2)
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    total_h_date_block = h_caja + 72
    y_box_top = y_loc_top - GAP_LOC_BOX - total_h_date_block

    desc2 = datos.get('desc2', "")
    s_desc2 = 68
    f_desc2 = get_font("Canaro-Medium.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, 900)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.1)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(10,10), anchor="lm")

    limit_y = min(y_desc2_top, y_firma_top) - 50 
    y_start_desc1 = y_titulo + 180 
    max_h_desc1 = limit_y - y_start_desc1
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 130, 900, max_h_desc1)
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(8,8), anchor="ls")
        y_desc += int(s_desc * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.1)

    x_txt_start = SIDE_MARGIN + 110
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
        x_txt_start = SIDE_MARGIN + icon.width + 25

    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja_orig = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
        caja = caja_orig.resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_fecha = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_fecha = "black"

    cy = y_box_top + (h_caja / 2)
    draw.text((cx_box, cy - 40), texto_dias, font=f_dias_largo, fill=color_fecha, anchor="mm")
    draw.text((cx_box, cy + 85), mes_nombre, font=f_mes_largo, fill=color_fecha, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx_box, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 15. INTERFAZ DE USUARIO Y LOGICA PRINCIPAL ENRUTADA (1 A 12 TIPOS)
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
            fecha1 = st.date_input("f1", key="f1", label_visibility="collapsed", format="DD/MM/YYYY", value=st.session_state.get('v_f1', datetime.date.today()))
        with c_f2:
            st.markdown("<div class='label-negro'>FECHA FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            c_f2_input, c_f2_btn = st.columns([4, 1.5])
            with c_f2_input:
                fecha2 = st.date_input("f2", key="f2", label_visibility="collapsed", value=st.session_state.get('v_f2', None), min_value=fecha1, format="DD/MM/YYYY")
            with c_f2_btn:
                if st.button("❌ BORRAR", help="Quitar segunda fecha"):
                    st.session_state['v_f2'] = None
                    if 'f2' in st.session_state: del st.session_state['f2']
                    st.rerun()
        
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
        
        # CHECKS PARA LOGOS INTERNOS (SOLO CULTURAS)
        usar_movida = False
        usar_orquesta = False
        if area_seleccionada == "Culturas":
            st.markdown("<div class='label-negro' style='margin-top: 5px;'>LOGOS INTERNOS DEL DEPARTAMENTO</div>", unsafe_allow_html=True)
            col_chk1, col_chk2 = st.columns(2)
            with col_chk1:
                usar_movida = st.checkbox("Usar logo de La Movida", value=st.session_state.get('chk_movida', False), key="chk_movida")
            with col_chk2:
                usar_orquesta = st.checkbox("Usar logo de La Orquesta", value=st.session_state.get('chk_orquesta', False), key="chk_orquesta")
            
            if usar_movida and usar_orquesta:
                st.warning("⚠️ Selecciona solo UN logo interno (Movida u Orquesta). Se priorizará La Movida.")
                usar_orquesta = False

        st.markdown("<div class='label-negro' style='margin-top: 15px;'>LOGOS COLABORADORES EXTERNOS</div>", unsafe_allow_html=True)
        col_logo1, col_logo2 = st.columns(2)
        
        logo1 = logo2 = None
        with col_logo1:
            if st.session_state.get('ruta_logo1') and os.path.exists(st.session_state['ruta_logo1']):
                st.success("✅ LOGO EXTR. 1 LISTO")
                if st.button("❌ QUITAR LOGO 1", key="del_l1", use_container_width=True):
                    st.session_state['ruta_logo1'] = None
                    st.rerun()
            else:
                logo1 = st.file_uploader("l1", type=['png', 'jpg', 'jpeg'], key="l1", label_visibility="collapsed")
                
        with col_logo2:
            if st.session_state.get('ruta_logo2') and os.path.exists(st.session_state['ruta_logo2']):
                st.success("✅ LOGO EXTR. 2 LISTO")
                if st.button("❌ QUITAR LOGO 2", key="del_l2", use_container_width=True):
                    st.session_state['ruta_logo2'] = None
                    st.rerun()
            else:
                logo2 = st.file_uploader("l2", type=['png', 'jpg', 'jpeg'], key="l2", label_visibility="collapsed")
        
        st.markdown("<div class='label-negro' style='margin-top: 15px;'>SUBIR Y RECORTAR IMAGEN DE FONDO</div>", unsafe_allow_html=True)
        if 'v_fondo' in st.session_state:
            st.success("✅ IMAGEN DE FONDO GUARDADA. Sube una nueva solo si quieres reemplazarla.")
        
        archivo_subido = st.file_uploader("img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte y presiona Submit.")
            img_crop = st_cropper(img_orig, realtime_update=True, aspect_ratio=(4, 5), should_resize_image=False)
            st.session_state['v_fondo'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Nueva imagen lista.")

        st.write("")
        if st.button("GENERAR FLYERS AZUAY", type="primary", use_container_width=True):
            errores = []
            if not desc1: errores.append("Falta Descripcion 1")
            if not fecha1: errores.append("Falta Fecha Inicio")
            if 'v_fondo' not in st.session_state: errores.append("Falta recortar la Imagen de Fondo")
            if total_chars > 175: errores.append("Excediste el límite de 175 caracteres combinados")

            if errores:
                for e in errores: st.error(f"⚠️ {e}")
            else:
                if logo1:
                    with open("temp_logo1.png", "wb") as f: f.write(logo1.getvalue())
                    st.session_state['ruta_logo1'] = "temp_logo1.png"
                if logo2:
                    with open("temp_logo2.png", "wb") as f: f.write(logo2.getvalue())
                    st.session_state['ruta_logo2'] = "temp_logo2.png"

                # CONSTRUIR LISTA DE LOGOS INTELIGENTE
                rutas_logos = []
                
                # 1. Inyectar Logo Interno si aplica
                if usar_movida and os.path.exists("logo.movida.png"):
                    rutas_logos.append("logo.movida.png")
                elif usar_orquesta and os.path.exists("logo.orquesta.png"):
                    rutas_logos.append("logo.orquesta.png")
                
                # 2. Inyectar Logos Externos
                if st.session_state.get('ruta_logo1') and os.path.exists(st.session_state['ruta_logo1']):
                    rutas_logos.append(st.session_state['ruta_logo1'])
                if st.session_state.get('ruta_logo2') and os.path.exists(st.session_state['ruta_logo2']):
                    rutas_logos.append(st.session_state['ruta_logo2'])
                
                # 3. Limitar a 2 logos máximos (para los Tipos 9 al 12)
                rutas_logos = rutas_logos[:2]
                
                st.session_state.update({
                    'v_d1': desc1,
                    'v_d2': desc2,
                    'v_f1': fecha1,
                    'v_f2': fecha2,
                    'v_h1': hora1,
                    'v_h2': hora2,
                    'v_dir': dir_texto
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
                
                # ENRUTAMIENTO INTELIGENTE A LOS 12 TIPOS
                if num_lg == 2 and fecha2 and desc2:
                    generated = {'t12_v1': generar_tipo_12_v1(datos), 't12_v2': generar_tipo_12_v2(datos), 't12_v3': generar_tipo_12_v3(datos), 't12_v4': generar_tipo_12_v4(datos)}
                    tid = 12
                elif num_lg == 2 and fecha2 and not desc2:
                    generated = {'t11_v1': generar_tipo_11_v1(datos), 't11_v2': generar_tipo_11_v2(datos), 't11_v3': generar_tipo_11_v3(datos), 't11_v4': generar_tipo_11_v4(datos)}
                    tid = 11
                elif num_lg == 2 and not fecha2 and desc2:
                    generated = {'t10_v1': generar_tipo_10_v1(datos), 't10_v2': generar_tipo_10_v2(datos), 't10_v3': generar_tipo_10_v3(datos), 't10_v4': generar_tipo_10_v4(datos)}
                    tid = 10
                elif num_lg == 2 and not fecha2 and not desc2:
                    generated = {'t9_v1': generar_tipo_9_v1(datos), 't9_v2': generar_tipo_9_v2(datos), 't9_v3': generar_tipo_9_v3(datos), 't9_v4': generar_tipo_9_v4(datos)}
                    tid = 9
                elif num_lg == 1 and fecha2 and desc2:
                    generated = {'t8_v1': generar_tipo_8_v1(datos), 't8_v2': generar_tipo_8_v2(datos), 't8_v3': generar_tipo_8_v3(datos), 't8_v4': generar_tipo_8_v4(datos)}
                    tid = 8
                elif num_lg == 1 and fecha2 and not desc2:
                    generated = {'t7_v1': generar_tipo_7_v1(datos), 't7_v2': generar_tipo_7_v2(datos), 't7_v3': generar_tipo_7_v3(datos), 't7_v4': generar_tipo_7_v4(datos)}
                    tid = 7
                elif num_lg == 1 and not fecha2 and desc2:
                    generated = {'t6_v1': generar_tipo_6_v1(datos), 't6_v2': generar_tipo_6_v2(datos), 't6_v3': generar_tipo_6_v3(datos), 't6_v4': generar_tipo_6_v4(datos)}
                    tid = 6
                elif num_lg == 1 and not fecha2 and not desc2:
                    generated = {'t5_v1': generar_tipo_5_v1(datos), 't5_v2': generar_tipo_5_v2(datos), 't5_v3': generar_tipo_5_v3(datos), 't5_v4': generar_tipo_5_v4(datos)}
                    tid = 5
                elif num_lg == 0 and fecha2 and desc2:
                    generated = {'t4_v1': generar_tipo_4_v1(datos), 't4_v2': generar_tipo_4_v2(datos), 't4_v3': generar_tipo_4_v3(datos), 't4_v4': generar_tipo_4_v4(datos)}
                    tid = 4
                elif num_lg == 0 and fecha2 and not desc2:
                    generated = {'t3_v1': generar_tipo_3_v1(datos), 't3_v2': generar_tipo_3_v2(datos), 't3_v3': generar_tipo_3_v3(datos), 't3_v4': generar_tipo_3_v4(datos)}
                    tid = 3
                elif num_lg == 0 and not fecha2 and desc2:
                    generated = {'t2_v1': generar_tipo_2_v1(datos), 't2_v2': generar_tipo_2_v2(datos), 't2_v3': generar_tipo_2_v3(datos), 't2_v4': generar_tipo_2_v4(datos)}
                    tid = 2
                else:
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
                    st.download_button("⬆️ DESCARGAR", buf.getvalue(), f"flyer_azuay_{sel}.png", "image/png", use_container_width=True)

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
