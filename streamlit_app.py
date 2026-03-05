import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper
import io
import os
import textwrap
import base64
import datetime

# ==============================================================================
# 1. CONFIGURACIÓN GLOBAL Y PARÁMETROS DE DISEÑO REVISADOS
# ==============================================================================

st.set_page_config(layout="wide", page_title="Flyers Azuay - Prefectura")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stButton>button { border-radius: 10px; font-weight: bold; }
            .zoom-hover { transition: transform .2s; }
            .zoom-hover:hover { transform: scale(1.05); }
            div[data-testid="stText"] p, .label-negro { font-family: 'Canaro', sans-serif; color: black !important; font-weight: bold; font-size: 18px; margin-bottom: 5px; }
            .label-menu { font-family: 'Canaro', sans-serif; color: white; font-weight: bold; font-size: 22px; margin-top: 10px; text-transform: uppercase; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); }
            a { text-decoration: none !important; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def set_bg():
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        with open("fondo_app.png", 'rb') as f: data = f.read()
        b64 = base64.b64encode(data).decode()
        bg_style = f"background-image: url('data:image/png;base64,{b64}'); background-size: cover; background-attachment: fixed;"
    st.markdown(f"<style>.stApp {{ {bg_style} }}</style>", unsafe_allow_html=True)
set_bg()

# PARÁMETROS GLOBALES (Modificados según requerimientos)
W, H = 2400, 3000
SIDE_MARGIN = 90  # Reducido a la mitad

# Tamaños "Invitan" drásticamente reducidos
S_INVITA_CENTER = 147 # 1/3 menos
S_INVITA_LEFT = 110   # Mitad

# ==============================================================================
# 2. MOTOR MATEMÁTICO Y AYUDANTES
# ==============================================================================

def ruta_abs(nombre): return os.path.join(os.getcwd(), nombre)

def get_font(path_str, size):
    try: return ImageFont.truetype(ruta_abs(path_str), size)
    except: return ImageFont.load_default()

def dibujar_texto_sombra(draw, text, x, y, font, fill="white", shadow="black", offset=(4,4), anchor="mm"):
    if shadow: draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def get_text_width(font, text):
    try: return font.getbbox(text)[2] - font.getbbox(text)[0]
    except: return font.getsize(text)[0]

def obtener_mes_nombre(m): return {1:"ENERO",2:"FEBRERO",3:"MARZO",4:"ABRIL",5:"MAYO",6:"JUNIO",7:"JULIO",8:"AGOSTO",9:"SEPTIEMBRE",10:"OCTUBRE",11:"NOVIEMBRE",12:"DICIEMBRE"}.get(m, "")
def obtener_mes_abbr(m): return {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"}.get(m, "")
def obtener_dia_semana(f): return ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"][f.weekday()]

def resize_por_alto(img, alto):
    if not img: return None
    w, h = img.size
    return img.resize((int(w * (alto / h)), alto), Image.Resampling.LANCZOS) if h>0 else img

def resize_por_ancho(img, ancho):
    if not img: return None
    w, h = img.size
    return img.resize((ancho, int(h * (ancho / w))), Image.Resampling.LANCZOS) if w>0 else img

def redimensionar_logo_colaborador(img):
    w, h = img.size
    if w == h: return resize_por_alto(img, 400)
    new_w = int(w * (400 / h))
    if new_w <= 700: return img.resize((new_w, 400), Image.Resampling.LANCZOS)
    return img.resize((700, int(h * (700 / w))), Image.Resampling.LANCZOS)

def redimensionar_logo_colaborador_top(img):
    w, h = img.size
    new_w = int(w * (300 / h))
    if new_w <= 600: return img.resize((new_w, 300), Image.Resampling.LANCZOS)
    return img.resize((600, int(h * (600 / w))), Image.Resampling.LANCZOS)

def redimensionar_logo_colaborador_tipo9(img):
    w, h = img.size
    new_w = int(w * (300 / h))
    if new_w <= 600: return img.resize((new_w, 300), Image.Resampling.LANCZOS)
    return img.resize((600, int(h * (600 / w))), Image.Resampling.LANCZOS)

def redimensionar_logo_interno(img, tipo):
    if tipo == "movida": return resize_por_ancho(img, 600)
    elif tipo == "orquesta": return resize_por_alto(img, 375)
    return img

def redimensionar_logo_interno_compartido(img, tipo):
    if tipo == "movida": return resize_por_ancho(img, 500)
    elif tipo == "orquesta": return resize_por_alto(img, 300)
    return img

def redimensionar_logo_movida_doble(img): return resize_por_ancho(img, 425)
def redimensionar_logo_orquesta_doble(img): return resize_por_alto(img, 225)

def wrap_text_pixel(texto, font, max_w):
    if not texto: return []
    palabras = texto.split()
    lineas, linea_actual = [], ""
    for p in palabras:
        test = linea_actual + " " + p if linea_actual else p
        if get_text_width(font, test) <= max_w: linea_actual = test
        else:
            if linea_actual: lineas.append(linea_actual)
            linea_actual = p
    if linea_actual: lineas.append(linea_actual)
    return lineas

def calcular_fuente_dinamica(texto, font_path, size_start, max_w, max_h):
    if not texto: return None, [], 0
    s = size_start
    while s > 30:
        f = get_font(font_path, s)
        lineas = wrap_text_pixel(texto, f, max_w)
        h_tot = len(lineas) * int(s * 1.15)
        if h_tot <= max_h: return f, lineas, s
        s -= 5
    f = get_font(font_path, 30)
    return f, wrap_text_pixel(texto, f, max_w), 30


# ==============================================================================
# 3. GENERADORES TIPO 1 (1 Desc, 1 Fecha Cuadrada Reducida, 0 Logos)
# ==============================================================================

def generar_tipo_1_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER)
    
    # Caja Cuadrada Reducida al 80% (438px)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    # Caja Izquierda
    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN
    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion Derecha (CORRECCIÓN)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    max_w_loc = int(W * 0.4) # Limite 4/10 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = W - SIDE_MARGIN - max_line_w
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
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN
    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion a la Izquierda (al lado de la caja) o apilada? En T1_v2 estaba apilada o a la derecha?
    # En V2 dejamos Ubicacion a la derecha para equilibrar firma
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # Calcular X con respecto al limite derecho (Firma)
    x_limite_der = W - SIDE_MARGIN - 400 # 400 es aprox ancho de firma
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_limite_der - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_1_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    # Limite 4/10 del ancho, inicia en 100 (un poco menos que Invita)
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion a la Derecha (CORRECCIÓN)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    max_w_loc = int(W * 0.4)
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = W - SIDE_MARGIN - max_line_w
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
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion a la Derecha 
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    x_limite_der = W - SIDE_MARGIN - 400
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_limite_der - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

# ==============================================================================
# 4. GENERADORES TIPO 2 (2 Desc, 1 Fecha Cuadrada, 0 Logos)
# ==============================================================================

def generar_tipo_2_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    # Desc 2
    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    max_w_d2 = int((W * 0.4) * 0.75) if desc2 else 0 # 3/4 del ancho d1
    lines_d2 = wrap_text_pixel(desc2, f_desc2, max_w_d2)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion Derecha
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = W - SIDE_MARGIN - max_line_w
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
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    max_w_d2 = int((W * 0.4) * 0.75) if desc2 else 0 
    lines_d2 = wrap_text_pixel(desc2, f_desc2, max_w_d2)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITA", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion Derecha Limitada
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    x_limite_der = W - SIDE_MARGIN - 400 
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_limite_der - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

def generar_tipo_2_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    max_w_d2 = int((W * 0.4) * 0.75) if desc2 else 0 
    lines_d2 = wrap_text_pixel(desc2, f_desc2, max_w_d2)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion Derecha
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = W - SIDE_MARGIN - max_line_w
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
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    y_box_top = Y_BOTTOM_BASELINE - int(144*0.8) - h_caja
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    max_w_d2 = int((W * 0.4) * 0.75) if desc2 else 0 
    lines_d2 = wrap_text_pixel(desc2, f_desc2, max_w_d2)
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITA", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8)
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8)
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_box_bottom = y_box_top + h_caja
    y_dia_txt = y_box_bottom + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    # Ubicacion Derecha Limitada
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    x_limite_der = W - SIDE_MARGIN - 400
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_limite_der - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    return img.convert("RGB")

# ==============================================================================
# 5. GENERADORES TIPO 3 (1 Desc, Caja Larga Dinámica, 0 Collab)
# ==============================================================================

def generar_tipo_3_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    
    # Caja Larga original (NO SE REDUCE)
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)  

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360 
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicación a la Izquierda con Tolerancia (1 logo firma derecha) -> Tol = 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - icon.height)), icon) # dummy pos for width
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    # Draw real icon
    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + 72 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_3_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (SIDE_MARGIN, int(Y_BOTTOM_BASELINE - icon.height)), icon) 
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + 72 
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
def generar_tipo_3_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda - Tolerancia 600px (1 logo firma arriba, ninguno abajo) -> Usamos limite estricto
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 # Tolerancia 1 logo (aunque este arriba, aplicamos seguridad)
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_3_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT)
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda - Tolerancia 600px (1 logo firma abajo derecha)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 6. GENERADORES TIPO 4 (2 Desc, Caja Larga Dinámica, 0 Collab)
# ==============================================================================

def generar_tipo_4_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo) 
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma) 

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion a la Derecha Limitada
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    max_w_loc = int(W * 0.4) 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    x_limite_der = W - SIDE_MARGIN
    max_line_w = max([get_text_width(f_lugar, l) for l in lines_loc]) if lines_loc else 200
    x_text_start = x_limite_der - max_line_w
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        img.paste(icon, (int(x_text_start - icon.width - 25), int(y_loc_icon_top)), icon)
        
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_text_start, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75)) # Limitada
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_4_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_4_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion a la Izquierda (Tol 600)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_4_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja = int(360 * 0.8)
    f_dias_largo = get_font("Canaro-Black.ttf", int(150*0.8))
    f_mes_largo = get_font("Canaro-Black.ttf", int(120*0.8))

    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, ((W - logo.width)//2, 150), logo)

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(int(600*0.8), int(max(w_txt_dias, w_txt_mes) + 150))
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(72*0.8)

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - int(40*0.8)), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(85*0.8)), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + int(72*0.8)
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(4,4), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 7. GENERADORES TIPO 5 (1 Parrafo, 1 Fecha Cuadrada, 1 Logo Collab/Interno)
# ==============================================================================

def generar_tipo_5_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # Logo Colaborador Abajo Derecha (1 logo = Tol 600)
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20 
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_5_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # Logo Colaborador Arriba Derecha
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_5_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_5_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 8. GENERADORES TIPO 6 (2 Desc, Fecha Cuadrada Reducida, 1 Logo Collab/Interno)
# ==============================================================================

def generar_tipo_6_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    # 3 LOGOS SUPERIORES CON MOTOR INTERNO COMPARTIDO
    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
        except: pass

    pref_img = None
    if os.path.exists("flyer_logo.png"):
        pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    firma_img = None
    if os.path.exists("flyer_firma.png"):
        firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = collab_img.width if collab_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if collab_img: img.paste(collab_img, (int(x1), y_logos + (300 - collab_img.height)//2), collab_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if firma_img: img.paste(firma_img, (int(x3), y_logos + (300 - firma_img.height)//2), firma_img)

    # Ubicacion Izquierda (0 logos abajo -> ocupa casi todo el ancho)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 100 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_6_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Ubicacion Izquierda Tol 600 (1 logo firma derecha)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_6_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    collab_img = None
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno_compartido(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno_compartido(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
        except: pass

    pref_img = None
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    firma_img = None
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = collab_img.width if collab_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    y_logos = 150

    if collab_img: img.paste(collab_img, (int(x1), y_logos + (300 - collab_img.height)//2), collab_img)
    if pref_img: img.paste(pref_img, (int(x2), y_logos), pref_img)
    if firma_img: img.paste(firma_img, (int(x3), y_logos + (300 - firma_img.height)//2), firma_img)

    # Ubicacion Izquierda (0 logos abajo)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 100 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_6_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"
        
    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 9. GENERADORES TIPO 7 (1 Desc, Caja Larga, 1 Logo Collab/Interno)
# ==============================================================================

def generar_tipo_7_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    
    # Caja Larga (NO REDUCIDA)
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Logo Colaborador Abajo Derecha
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_7_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha)
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_7_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Logo Colaborador Abajo Derecha
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_7_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha)
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 10. GENERADORES TIPO 8 (2 Desc, Caja Larga, 1 Logo Collab/Interno)
# ==============================================================================

def generar_tipo_8_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Logo Colaborador Abajo Derecha
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width 
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_8_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha) 
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_8_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
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

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Logo Colaborador Abajo Derecha
    collab_img = None
    y_logo_collab_top = Y_BOTTOM_BASELINE
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador(img_c)
            y_logo_collab_top = Y_BOTTOM_BASELINE - collab_img.height + 20
            x_collab = W - SIDE_MARGIN - collab_img.width 
            img.paste(collab_img, (int(x_collab), int(y_logo_collab_top)), collab_img)
        except: pass

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)
        
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_8_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos_top = 300
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos_top, 150), logo)

    # 1. LOGO COLABORADOR (Arriba Derecha)
    if datos.get('logos') and len(datos['logos']) > 0:
        logo_path = datos['logos'][0]
        try:
            img_c = Image.open(logo_path).convert("RGBA")
            if "logo.movida" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "movida")
            elif "logo.orquesta" in os.path.basename(logo_path).lower(): collab_img = redimensionar_logo_interno(img_c, "orquesta")
            else: collab_img = redimensionar_logo_colaborador_top(img_c)
            y_collab = 150 + (378 - collab_img.height) // 2
            x_collab = W - margin_logos_top - collab_img.width
            img.paste(collab_img, (int(x_collab), int(y_collab)), collab_img)
        except: pass

    y_firma_top = Y_BOTTOM_BASELINE
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        y_firma_top = Y_BOTTOM_BASELINE - firma.height + 50
        img.paste(firma, (W - firma.width - SIDE_MARGIN, int(y_firma_top)), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    h_caja = 360
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 800 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)
        
    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 11. GENERADORES TIPO 9 (1 Desc, Fecha Cuadrada Reducida, 2 Logos Compartidos)
# ==============================================================================

def generar_tipo_9_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    # 2 Logos Abajo Derecha (Uso de MOTOR COMPARTIDO)
    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300 (2 logos abajo derecha)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_9_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    # 3 LOGOS ARRIBA CON MOTOR COMPARTIDO
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 600 (1 logo firma derecha)
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_9_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) 
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_9_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT)
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 12. GENERADORES TIPO 10 (2 Desc, Fecha Cuadrada Reducida, 2 Logos Compartidos)
# ==============================================================================

def generar_tipo_10_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_10_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 600 
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_10_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    collab1 = collab2 = None
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            img_c1 = Image.open(datos['logos'][0]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if datos.get('logos') and len(datos['logos']) > 1:
        try:
            img_c2 = Image.open(datos['logos'][1]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

def generar_tipo_10_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 600 
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
        
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)

    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 13. GENERADORES TIPO 11 (1 Desc, Caja Larga, 2 Logos Compartidos)
# ==============================================================================

def generar_tipo_11_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    # 3 LOGOS ARRIBA
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    collab1 = collab2 = None
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            img_c1 = Image.open(datos['logos'][0]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if datos.get('logos') and len(datos['logos']) > 1:
        try:
            img_c2 = Image.open(datos['logos'][1]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_11_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    # 3 LOGOS ARRIBA
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

# ==============================================================================
# 14. GENERADORES TIPO 12 (2 Desc, Caja Larga, 2 Logos Compartidos)
# ==============================================================================

def generar_tipo_12_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    collab1 = collab2 = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 780 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    # 3 LOGOS ARRIBA
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))

    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60

    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    margin_logos = 200
    if os.path.exists("flyer_logo.png"):
        logo = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378)
        img.paste(logo, (margin_logos, 150), logo)
    if os.path.exists("flyer_firma.png"):
        firma = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
        img.paste(firma, (W - firma.width - margin_logos, 150 + 20), firma)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    collab1 = collab2 = None
    if datos.get('logos') and len(datos['logos']) > 0:
        try:
            img_c1 = Image.open(datos['logos'][0]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][0]).lower(): collab1 = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: collab1 = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if datos.get('logos') and len(datos['logos']) > 1:
        try:
            img_c2 = Image.open(datos['logos'][1]).convert("RGBA")
            if "logo.movida" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(datos['logos'][1]).lower(): collab2 = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: collab2 = redimensionar_logo_colaborador_tipo9(img_c2)
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

    # Ubicacion Izquierda Tol 300
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 850 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")

def generar_tipo_12_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150)
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    # 3 LOGOS ARRIBA
    c1_img = c2_img = pref_img = None
    logos_list = datos.get('logos', [])
    if len(logos_list) > 0:
        try:
            img_c1 = Image.open(logos_list[0]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[0]).lower(): c1_img = redimensionar_logo_interno_compartido(img_c1, "orquesta")
            else: c1_img = redimensionar_logo_colaborador_tipo9(img_c1)
        except: pass
    if len(logos_list) > 1:
        try:
            img_c2 = Image.open(logos_list[1]).convert("RGBA")
            if "logo.movida" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "movida")
            elif "logo.orquesta" in os.path.basename(logos_list[1]).lower(): c2_img = redimensionar_logo_interno_compartido(img_c2, "orquesta")
            else: c2_img = redimensionar_logo_colaborador_tipo9(img_c2)
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

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora_dyn = get_font("Canaro-ExtraBold.ttf", size_h)

    # Ubicacion Izquierda Tol 600
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 600 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"):
        img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")

    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls")
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora_dyn, offset=(6,6), anchor="mm")

    return img.convert("RGB")
# ==============================================================================
# 15. GENERADORES TIPO 9_C (1 Desc, Fecha Cuadrada, 5 Logos)
# ==============================================================================

def generar_tipo_9_c_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_9_c_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    if c1_img: img.paste(c1_img, (int(x1), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_9_c_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    if int_img: img.paste(int_img, (int(x1), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(x2), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(x3), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65 
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_9_c_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    x1 = gap
    x2 = x1 + w1 + gap
    x3 = x2 + w2 + gap
    if c1_img: img.paste(c1_img, (int(x1), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(x2), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(x3), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2

    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

# ==============================================================================
# 16. GENERADORES TIPO 10_C (2 Desc, Fecha Cuadrada, 5 Logos)
# ==============================================================================

def generar_tipo_10_c_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_10_c_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_10_c_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65 
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_10_c_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")
# ==============================================================================
# 17. GENERADORES TIPO 11_C (1 Desc, Fecha Larga, 5 Logos)
# ==============================================================================

def generar_tipo_11_c_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")

    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_11_c_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_11_c_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65 
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = 68 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_11_c_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

# ==============================================================================
# 18. GENERADORES TIPO 12_C (2 Desc, Fecha Larga, 5 Logos)
# ==============================================================================

def generar_tipo_12_c_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_12_c_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_12_c_v3(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    int_img = pref_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_top(im)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    w1 = int_img.width if int_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = firma_img.width if firma_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if int_img: img.paste(int_img, (int(gap), 150 + (300 - int_img.height)//2), int_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), 150 + (300 - firma_img.height)//2), firma_img)

    l_list = datos.get('logos', [])
    col1 = col2 = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            col1 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            col2 = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass

    x_c = W - 90
    if col2:
        x_c -= col2.width
        img.paste(col2, (int(x_c), int(Y_BOTTOM_BASELINE - col2.height + 20)), col2)
        x_c -= 65 
    if col1:
        x_c -= col1.width
        img.paste(col1, (int(x_c), int(Y_BOTTOM_BASELINE - col1.height + 20)), col1)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_12_c_v4(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try:
            c = Image.open(l_list[0]).convert("RGBA")
            c1_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[0].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[0].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if len(l_list)>1:
        try:
            c = Image.open(l_list[1]).convert("RGBA")
            c2_img = redimensionar_logo_interno_compartido(c, "movida") if "movida" in l_list[1].lower() else redimensionar_logo_interno_compartido(c, "orquesta") if "orquesta" in l_list[1].lower() else redimensionar_logo_colaborador_tipo9(c)
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    int_img = firma_img = None
    if datos.get('logo_interno'):
        try:
            im = Image.open(datos['logo_interno']).convert("RGBA")
            t = datos.get('tipo_interno')
            int_img = redimensionar_logo_interno_compartido(im, t) if t in ["movida","orquesta"] else redimensionar_logo_colaborador_tipo9(im)
        except: pass
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65 
    if int_img:
        x_c -= int_img.width
        img.paste(int_img, (int(x_c), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 300 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

# ==============================================================================
# 19. GENERADORES ESPECIALES "DOBLE" (2 Internos + 2 Externos + Pref + Jota)
# ==============================================================================

def generar_tipo_9_doble_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 # Tol 250 para 3 logos
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_9_doble_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_10_doble_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_10_doble_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    h_caja, w_caja = 438, 438
    f_dia_box = get_font("Canaro-Black.ttf", int(297*0.8))
    f_mes_box = get_font("Canaro-Black.ttf", int(170*0.8))
    f_dia_semana = get_font("Canaro-ExtraBold.ttf", int(93*0.8))

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    y_box_top = y_loc_top - 100 - h_caja - int(144*0.8)
    x_box = SIDE_MARGIN

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha.png"):
        caja = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = int(y_box_top + (h_caja / 2))
    draw.text((cx, cy - int(42*0.8)), str(datos['fecha1'].day), font=f_dia_box, fill=color_f, anchor="mm")
    draw.text((cx, cy + int(144*0.8)), obtener_mes_abbr(datos['fecha1'].month), font=f_mes_box, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = int(93*0.8) 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_dia_txt = y_box_top + h_caja + int(72*0.8)
    y_hora_txt = y_dia_txt + int(72*0.8)
    dibujar_texto_sombra(draw, obtener_dia_semana(datos['fecha1']), cx, y_dia_txt, f_dia_semana, offset=(4,4), anchor="mm")
    dibujar_texto_sombra(draw, str_hora, cx, y_hora_txt, f_hora, offset=(4,4), anchor="mm")
    return img.convert("RGB")

def generar_tipo_11_doble_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_11_doble_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_box_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_12_doble_v1(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_CENTER) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", W/2, y_titulo, f_invita, offset=(8,8))
    chars_desc = len(datos['desc1'])
    if chars_desc <= 75: size_desc_val = 110; wrap_w = 40
    elif chars_desc <= 120: size_desc_val = 90; wrap_w = 50
    else: size_desc_val = 75; wrap_w = 60
    f_desc = get_font("Canaro-SemiBold.ttf", size_desc_val)
    y_desc = y_titulo + 150
    for l in textwrap.wrap(datos['desc1'], width=wrap_w):
        dibujar_texto_sombra(draw, l, W/2, y_desc, f_desc, offset=(6,6))
        y_desc += int(size_desc_val * 1.1)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, x_box, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

def generar_tipo_12_doble_v2(datos):
    fondo = datos['fondo'].copy()
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)

    f_invita = get_font("Canaro-Bold.ttf", S_INVITA_LEFT) 
    f_dias_largo = get_font("Canaro-Black.ttf", 150) 
    f_mes_largo = get_font("Canaro-Black.ttf", 120)

    l_list = datos.get('logos', [])
    c1_img = c2_img = pref_img = None
    if len(l_list)>0:
        try: c1_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[0]).convert("RGBA"))
        except: pass
    if len(l_list)>1:
        try: c2_img = redimensionar_logo_colaborador_tipo9(Image.open(l_list[1]).convert("RGBA"))
        except: pass
    if os.path.exists("flyer_logo.png"): pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775)

    w1 = c1_img.width if c1_img else 0
    w2 = pref_img.width if pref_img else 0
    w3 = c2_img.width if c2_img else 0
    gap = (W - (w1 + w2 + w3)) / 4
    if c1_img: img.paste(c1_img, (int(gap), 150 + (300 - c1_img.height)//2), c1_img)
    if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
    if c2_img: img.paste(c2_img, (int(gap*3 + w1 + w2), 150 + (300 - c2_img.height)//2), c2_img)

    orq_img = mov_img = firma_img = None
    if os.path.exists("logo.orquesta.png"): orq_img = redimensionar_logo_orquesta_doble(Image.open("logo.orquesta.png").convert("RGBA"))
    if os.path.exists("logo.movida.png"): mov_img = redimensionar_logo_movida_doble(Image.open("logo.movida.png").convert("RGBA"))
    if os.path.exists("flyer_firma.png"): firma_img = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400)

    x_c = W - 90
    if firma_img:
        x_c -= firma_img.width
        img.paste(firma_img, (int(x_c), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img)
        x_c -= 65
    if mov_img:
        x_c -= mov_img.width
        img.paste(mov_img, (int(x_c), int(Y_BOTTOM_BASELINE - mov_img.height + 20)), mov_img)
        x_c -= 65
    if orq_img:
        x_c -= orq_img.width
        img.paste(orq_img, (int(x_c), int(Y_BOTTOM_BASELINE - orq_img.height + 20)), orq_img)

    h_icon = int(221 * 0.8)
    s_lug = 61 if len(datos['lugar']) < 45 else 51
    f_lugar = get_font("Canaro-SemiBold.ttf", s_lug)
    x_start_loc = SIDE_MARGIN
    if os.path.exists("flyer_icono_lugar.png"):
        icon = resize_por_alto(Image.open("flyer_icono_lugar.png").convert("RGBA"), h_icon)
        x_start_loc = SIDE_MARGIN + icon.width + 25
    max_w_loc = W - SIDE_MARGIN - x_start_loc - 250 
    lines_loc = wrap_text_pixel(datos['lugar'], f_lugar, max_w_loc)
    total_h_loc = len(lines_loc) * int(s_lug * 1.1)
    h_loc_block = max(total_h_loc, h_icon)
    y_loc_top = Y_BOTTOM_BASELINE - h_loc_block
    y_loc_icon_top = y_loc_top + (h_loc_block - h_icon) / 2
    y_loc_text_top = y_loc_top + (h_loc_block - total_h_loc) / 2
    if os.path.exists("flyer_icono_lugar.png"): img.paste(icon, (SIDE_MARGIN, int(y_loc_icon_top)), icon)
    curr_y_loc = y_loc_text_top + int(s_lug * 1.1)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_start_loc, curr_y_loc, f_lugar, anchor="ls", offset=(3,3))
        curr_y_loc += int(s_lug * 1.1)

    dia1 = datos['fecha1'].day
    dia2 = datos['fecha2'].day if datos['fecha2'] else dia1
    texto_dias = f"{dia1} al {dia2}"
    w_txt_dias = get_text_width(f_dias_largo, texto_dias)
    w_txt_mes = get_text_width(f_mes_largo, obtener_mes_nombre(datos['fecha1'].month))
    w_caja = max(600, int(max(w_txt_dias, w_txt_mes) + 200))
    h_caja = 360
    x_box = SIDE_MARGIN
    y_box_top = y_loc_top - 100 - h_caja - 72

    desc2 = datos.get('desc2', "")
    s_desc2 = 75
    f_desc2 = get_font("Canaro-SemiBold.ttf", s_desc2)
    lines_d2 = wrap_text_pixel(desc2, f_desc2, int((W*0.4)*0.75))
    total_h_d2 = len(lines_d2) * int(s_desc2 * 1.15)
    y_desc2_top = y_box_top - 42 - total_h_d2

    y_titulo = 690 
    dibujar_texto_sombra(draw, "INVITAN", SIDE_MARGIN, y_titulo, f_invita, offset=(6,6), anchor="lm")
    y_start_desc1 = y_titulo + 100 
    max_h_desc1 = y_desc2_top - y_start_desc1 - 50
    f_desc, lines_d1, s_desc = calcular_fuente_dinamica(datos['desc1'], "Canaro-SemiBold.ttf", 100, int(W*0.4), max_h_desc1)
    
    y_desc = y_start_desc1
    for l in lines_d1:
        dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_desc, f_desc, offset=(4,4), anchor="ls")
        y_desc += int(s_desc * 1.15)

    if desc2:
        y_cursor_d2 = y_desc2_top + int(s_desc2 * 1.1)
        for l in lines_d2:
            dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_cursor_d2, f_desc2, offset=(4,4), anchor="ls") 
            y_cursor_d2 += int(s_desc2 * 1.15)

    if os.path.exists("flyer_caja_fecha_larga.png"):
        caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(caja, (x_box, int(y_box_top)), caja)
        color_f = "white"
    else:
        draw.rectangle([x_box, y_box_top, x_box+w_caja, y_box_top+h_caja], fill="white")
        color_f = "black"

    cx = x_box + (w_caja / 2)
    cy = y_box_top + (h_caja / 2)
    draw.text((cx, cy - 40), texto_dias, font=f_dias_largo, fill=color_f, anchor="mm")
    draw.text((cx, cy + 85), obtener_mes_nombre(datos['fecha1'].month), font=f_mes_largo, fill=color_f, anchor="mm")
    str_hora = datos['hora1'].strftime('%H:%M %p')
    size_h = 93 
    if datos['hora2']: 
        str_hora += f" a {datos['hora2'].strftime('%H:%M %p')}"
        size_h = int(68*0.8) 
    f_hora = get_font("Canaro-ExtraBold.ttf", size_h)
    y_hora = y_box_top + h_caja + 72
    dibujar_texto_sombra(draw, str_hora, cx, y_hora, f_hora, offset=(6,6), anchor="mm")
    return img.convert("RGB")

# ==============================================================================
# 20. INTERFAZ DE USUARIO Y LOGICA PRINCIPAL ENRUTADA INTELIGENTE
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
        
        usar_movida = False
        usar_orquesta = False
        if area_seleccionada == "Culturas":
            st.markdown("<div class='label-negro' style='margin-top: 5px;'>LOGOS INTERNOS DEL DEPARTAMENTO</div>", unsafe_allow_html=True)
            col_chk1, col_chk2 = st.columns(2)
            with col_chk1:
                usar_movida = st.checkbox("Usar logo de La Movida", value=st.session_state.get('chk_movida', False), key="chk_movida")
            with col_chk2:
                usar_orquesta = st.checkbox("Usar logo de La Orquesta", value=st.session_state.get('chk_orquesta', False), key="chk_orquesta")

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
            st.success("✅ IMAGEN DE FONDO GUARDADA.")
        
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

                rutas_externos = []
                if st.session_state.get('ruta_logo1') and os.path.exists(st.session_state['ruta_logo1']):
                    rutas_externos.append(st.session_state['ruta_logo1'])
                if st.session_state.get('ruta_logo2') and os.path.exists(st.session_state['ruta_logo2']):
                    rutas_externos.append(st.session_state['ruta_logo2'])
                
                internos_paths = []
                if usar_movida and os.path.exists("logo.movida.png"): internos_paths.append("logo.movida.png")
                if usar_orquesta and os.path.exists("logo.orquesta.png"): internos_paths.append("logo.orquesta.png")

                num_ext = len(rutas_externos)
                num_int = len(internos_paths)

                st.session_state.update({
                    'v_d1': desc1, 'v_d2': desc2, 'v_f1': fecha1, 'v_f2': fecha2,
                    'v_h1': hora1, 'v_h2': hora2, 'v_dir': dir_texto
                })

                datos = {
                    'fondo': st.session_state.v_fondo, 'desc1': desc1, 'desc2': desc2,
                    'fecha1': fecha1, 'fecha2': fecha2, 'hora1': hora1, 'hora2': hora2,
                    'lugar': dir_texto
                }
                
                generated = {}
                tid = "N/A"
                
                # ENRUTAMIENTO INTELIGENTE DEFINITIVO
                
                # CASO 1: 2 INTERNOS + 2 EXTERNOS (ENRUTAMIENTO DOBLE)
                if num_int == 2 and num_ext == 2:
                    datos['logos'] = rutas_externos 
                    if fecha2 and desc2:
                        generated = {'t12d_v1': generar_tipo_12_doble_v1(datos), 't12d_v2': generar_tipo_12_doble_v2(datos)}
                        tid = "12_Doble"
                    elif fecha2 and not desc2:
                        generated = {'t11d_v1': generar_tipo_11_doble_v1(datos), 't11d_v2': generar_tipo_11_doble_v2(datos)}
                        tid = "11_Doble"
                    elif not fecha2 and desc2:
                        generated = {'t10d_v1': generar_tipo_10_doble_v1(datos), 't10d_v2': generar_tipo_10_doble_v2(datos)}
                        tid = "10_Doble"
                    else:
                        generated = {'t9d_v1': generar_tipo_9_doble_v1(datos), 't9d_v2': generar_tipo_9_doble_v2(datos)}
                        tid = "9_Doble"
                        
                # CASO 2: 2 INTERNOS + 1 EXTERNO (ENRUTAMIENTO C)
                elif num_int == 2 and num_ext == 1:
                    datos['logo_interno'] = rutas_externos[0]
                    datos['tipo_interno'] = "collab"
                    datos['logos'] = internos_paths 
                    if fecha2 and desc2:
                        generated = {'t12c_v1': generar_tipo_12_c_v1(datos), 't12c_v2': generar_tipo_12_c_v2(datos), 't12c_v3': generar_tipo_12_c_v3(datos), 't12c_v4': generar_tipo_12_c_v4(datos)}
                        tid = "12_Especial"
                    elif fecha2 and not desc2:
                        generated = {'t11c_v1': generar_tipo_11_c_v1(datos), 't11c_v2': generar_tipo_11_c_v2(datos), 't11c_v3': generar_tipo_11_c_v3(datos), 't11c_v4': generar_tipo_11_c_v4(datos)}
                        tid = "11_Especial"
                    elif not fecha2 and desc2:
                        generated = {'t10c_v1': generar_tipo_10_c_v1(datos), 't10c_v2': generar_tipo_10_c_v2(datos), 't10c_v3': generar_tipo_10_c_v3(datos), 't10c_v4': generar_tipo_10_c_v4(datos)}
                        tid = "10_Especial"
                    else:
                        generated = {'t9c_v1': generar_tipo_9_c_v1(datos), 't9c_v2': generar_tipo_9_c_v2(datos), 't9c_v3': generar_tipo_9_c_v3(datos), 't9c_v4': generar_tipo_9_c_v4(datos)}
                        tid = "9_Especial"

                # CASO 3: 1 INTERNO + 2 EXTERNOS (ENRUTAMIENTO C ORIGINAL)
                elif num_int == 1 and num_ext == 2:
                    datos['logo_interno'] = internos_paths[0]
                    datos['tipo_interno'] = "movida" if "movida" in internos_paths[0] else "orquesta"
                    datos['logos'] = rutas_externos 
                    if fecha2 and desc2:
                        generated = {'t12c_v1': generar_tipo_12_c_v1(datos), 't12c_v2': generar_tipo_12_c_v2(datos), 't12c_v3': generar_tipo_12_c_v3(datos), 't12c_v4': generar_tipo_12_c_v4(datos)}
                        tid = "12_Especial"
                    elif fecha2 and not desc2:
                        generated = {'t11c_v1': generar_tipo_11_c_v1(datos), 't11c_v2': generar_tipo_11_c_v2(datos), 't11c_v3': generar_tipo_11_c_v3(datos), 't11c_v4': generar_tipo_11_c_v4(datos)}
                        tid = "11_Especial"
                    elif not fecha2 and desc2:
                        generated = {'t10c_v1': generar_tipo_10_c_v1(datos), 't10c_v2': generar_tipo_10_c_v2(datos), 't10c_v3': generar_tipo_10_c_v3(datos), 't10c_v4': generar_tipo_10_c_v4(datos)}
                        tid = "10_Especial"
                    else:
                        generated = {'t9c_v1': generar_tipo_9_c_v1(datos), 't9c_v2': generar_tipo_9_c_v2(datos), 't9c_v3': generar_tipo_9_c_v3(datos), 't9c_v4': generar_tipo_9_c_v4(datos)}
                        tid = "9_Especial"
                        
                # CASO 4: ENRUTAMIENTO NORMAL 
                else:
                    logos_combinados = internos_paths + rutas_externos
                    logos_combinados = logos_combinados[:2]
                    datos['logos'] = logos_combinados
                    num_lg = len(logos_combinados)
                    
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
                        generated = {'v1': generar_tipo_1_v1(datos), 'v2': generar_tipo_1_v2(datos), 'v3': generar_tipo_1_v3(datos), 'v4': generar_tipo_1_v4(datos)}
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
