import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper
import io
import os
import textwrap
import base64
import datetime

# ==============================================================================
# 1. INICIALIZACIÓN DE ESTADOS Y CONFIGURACIÓN GLOBAL
# ==============================================================================

st.set_page_config(layout="wide", page_title="Generador Azuay")

def on_format_change():
    if 'v_fondo' in st.session_state:
        del st.session_state['v_fondo']

# EL "ESCUDO" DE MEMORIA: Aquí guardamos todo para que no se borre al cambiar de ventana
default_keys = {
    'saved_d1': "", 'saved_d2': "", 'saved_dir': "", 'saved_tel1': "", 'saved_tel2': "",
    'saved_f1': None, 'saved_f2': None, 'saved_h1': None, 'saved_h2': None,
    'saved_rad': "Ubicación", 'saved_titulo': True, 'saved_formato': "Publicación",
    'saved_movida': False, 'saved_orquesta': False, 'ruta_logo1': None, 'ruta_logo2': None
}
for k, v in default_keys.items():
    if k not in st.session_state: st.session_state[k] = v

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

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    return ""

def set_bg():
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        b64 = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"background-image: url('data:image/png;base64,{b64}'); background-size: cover; background-attachment: fixed;"
    st.markdown(f"<style>.stApp {{ {bg_style} }}</style>", unsafe_allow_html=True)
set_bg()

# PARÁMETROS DINÁMICOS Y MÁRGENES (105px)
if st.session_state.saved_formato == "Historia":
    W, H = 2400, 4267
    CROP_RATIO = (9, 16)
else:
    W, H = 2400, 3000
    CROP_RATIO = (4, 5)

SIDE_MARGIN = 105
Y_BOTTOM_BASELINE = H - 150
S_INVITA_CENTER = 147
S_INVITA_LEFT = 110

# ==============================================================================
# 2. MOTOR MATEMÁTICO Y DE LOGOS
# ==============================================================================

def ruta_abs(n): return os.path.join(os.getcwd(), n)
def get_font(path, size):
    try: return ImageFont.truetype(ruta_abs(path), size)
    except: return ImageFont.load_default()

def dibujar_texto_sombra(draw, txt, x, y, font, fill="white", shadow="black", offset=(4,4), anchor="mm"):
    if shadow: draw.text((x + offset[0], y + offset[1]), txt, font=font, fill=shadow, anchor=anchor)
    draw.text((x, y), txt, font=font, fill=fill, anchor=anchor)

def get_text_width(font, txt):
    try: return font.getbbox(txt)[2] - font.getbbox(txt)[0]
    except: return font.getsize(txt)[0]

def obtener_mes_nombre(m): return {1:"ENERO",2:"FEBRERO",3:"MARZO",4:"ABRIL",5:"MAYO",6:"JUNIO",7:"JULIO",8:"AGOSTO",9:"SEPTIEMBRE",10:"OCTUBRE",11:"NOVIEMBRE",12:"DICIEMBRE"}.get(m, "")
def obtener_mes_abbr(m): return {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"}.get(m, "")
def obtener_dia_semana(f): return ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"][f.weekday()]

def resize_por_alto(img, alto): return img.resize((int(img.width * (alto / img.height)), alto), Image.Resampling.LANCZOS) if img and img.height>0 else img
def resize_por_ancho(img, ancho): return img.resize((ancho, int(img.height * (ancho / img.width))), Image.Resampling.LANCZOS) if img and img.width>0 else img

def get_tipo_logo(p):
    pl = p.lower()
    if "movida" in pl: return "movida"
    if "orquesta" in pl: return "orquesta"
    if "extremo" in pl: return "extremo"
    return "collab"

def redim_interno(img, t): 
    if t=="movida": return resize_por_ancho(img, 600)
    elif t=="orquesta": return resize_por_alto(img, 375)
    elif t=="extremo": return resize_por_alto(img, 350)
    return img

def redim_interno_comp(img, t, top_count=0):
    if t=="movida": return resize_por_ancho(img, 500)
    elif t=="orquesta": return resize_por_alto(img, 300)
    elif t=="extremo": return resize_por_alto(img, 275) if top_count == 3 else resize_por_alto(img, 350)
    return img

def load_logo_single_bottom(p):
    try:
        c = Image.open(p).convert("RGBA"); t = get_tipo_logo(p)
        if t != "collab": return redim_interno(c, t)
        w, h = c.size; new_w = int(w * (400 / h))
        return c.resize((new_w, 400), Image.Resampling.LANCZOS) if new_w <= 700 else c.resize((700, int(h * (700 / w))), Image.Resampling.LANCZOS)
    except: return None

def load_logo_shared(p, top_count=0):
    try:
        c = Image.open(p).convert("RGBA"); t = get_tipo_logo(p)
        if t != "collab": return redim_interno_comp(c, t, top_count)
        w, h = c.size; new_w = int(w * (300 / h))
        return c.resize((new_w, 300), Image.Resampling.LANCZOS) if new_w <= 600 else c.resize((600, int(h * (600 / w))), Image.Resampling.LANCZOS)
    except: return None

def wrap_text_pixel(txt, font, max_w):
    if not txt: return []
    final_lines = []
    for block in txt.split('\n'):
        lineas, linea = [], ""
        for p in block.split():
            test = linea + " " + p if linea else p
            if get_text_width(font, test) <= max_w: linea = test
            else:
                if linea: lineas.append(linea)
                linea = p
        if linea: lineas.append(linea)
        final_lines.extend(lineas)
    return final_lines

def calcular_fuente_dinamica(txt, font_path, size_s, max_w, max_h):
    if not txt: return None, [], 0
    s = size_s
    while s > 30:
        f = get_font(font_path, s)
        lineas = wrap_text_pixel(txt, f, max_w)
        if len(lineas) * int(s * 1.15) <= max_h: return f, lineas, s
        s -= 5
    f = get_font(font_path, 30)
    return f, wrap_text_pixel(txt, f, max_w), 30

def init_canvas(fondo):
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    if os.path.exists("flyer_sombra.png"):
        s = Image.open("flyer_sombra.png").convert("RGBA").resize((W, H))
        img.paste(s, (0, 0), s)
    return img, draw

# ==============================================================================
# 3. HELPERS DE GRAVEDAD E INTELIGENCIA ESPACIAL
# ==============================================================================

def draw_ubicacion(img, draw, lugar, is_right, min_x_logos, gap, icono_type="lugar"):
    if not lugar: return Y_BOTTOM_BASELINE
    h_icon = int(221 * 0.8)
    s_lug = 61 if len(lugar) < 45 or '\n' in lugar else 51
    f_lug = get_font("Canaro-SemiBold.ttf", s_lug)
    ico_name = "flyer_icono_lugar.png" if icono_type == "lugar" else "logo.celular.png"
    icon = resize_por_alto(Image.open(ico_name).convert("RGBA"), h_icon) if os.path.exists(ico_name) else None
    
    if is_right:
        lines = wrap_text_pixel(lugar, f_lug, int(W * 0.4))
        h_block = max(len(lines) * int(s_lug * 1.1), h_icon)
        y_top = Y_BOTTOM_BASELINE - h_block
        x_start = W - SIDE_MARGIN - (max([get_text_width(f_lug, l) for l in lines]) if lines else 200)
        if icon: img.paste(icon, (int(x_start - icon.width - 25), int(y_top + (h_block - h_icon) / 2)), icon)
        y_txt = y_top + (h_block - len(lines)*int(s_lug*1.1))/2 + int(s_lug*1.1)
        for l in lines: dibujar_texto_sombra(draw, l, x_start, y_txt, f_lug, anchor="ls", offset=(3,3)); y_txt += int(s_lug*1.1)
        return y_top
    else:
        x_start = SIDE_MARGIN + (icon.width + 25 if icon else 0)
        max_w = (W - SIDE_MARGIN - x_start) if min_x_logos >= W else (min_x_logos - gap - x_start)
        if max_w < 400: max_w = 400 
        
        lines = wrap_text_pixel(lugar, f_lug, max_w)
        h_block = max(len(lines) * int(s_lug * 1.1), h_icon)
        y_top = Y_BOTTOM_BASELINE - h_block
        if icon: img.paste(icon, (SIDE_MARGIN, int(y_top + (h_block - h_icon) / 2)), icon)
        y_txt = y_top + (h_block - len(lines)*int(s_lug*1.1))/2 + int(s_lug*1.1)
        for l in lines: dibujar_texto_sombra(draw, l, x_start, y_txt, f_lug, anchor="ls", offset=(3,3)); y_txt += int(s_lug*1.1)
        return y_top

def draw_caja_cuadrada(img, draw, f1, h1, h2, lugar, y_loc_top, is_right):
    y_base = Y_BOTTOM_BASELINE if is_right or not lugar else (y_loc_top - 80)
    if not f1: return y_base
    
    # LA CAJA SIEMPRE MIDE 438, SIN IMPORTAR SI HAY HORA O NO
    h_caja, w_caja = 438, 438
    
    # Si no hay hora, el offset es más pequeño (la caja baja y se pega a la ubicación)
    offset_y = 145 if h1 else 80 
    y_box = y_base - offset_y - h_caja
    
    if os.path.exists("flyer_caja_fecha.png"):
        c = resize_por_alto(Image.open("flyer_caja_fecha.png").convert("RGBA"), h_caja)
        img.paste(c, (SIDE_MARGIN, int(y_box)), c); c_f = "white"
    else: draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+w_caja, y_box+h_caja], fill="white"); c_f = "black"
        
    cx, cy = SIDE_MARGIN + w_caja/2, y_box + h_caja/2
    draw.text((cx, cy - 33), str(f1.day), font=get_font("Canaro-Black.ttf", 237), fill=c_f, anchor="mm")
    draw.text((cx, cy + 115), obtener_mes_abbr(f1.month), font=get_font("Canaro-Black.ttf", 136), fill=c_f, anchor="mm")
    
    dibujar_texto_sombra(draw, obtener_dia_semana(f1), cx, y_box + h_caja + 57, get_font("Canaro-ExtraBold.ttf", 74), offset=(3,3), anchor="mm")
    if h1:
        s_h = 54 if h2 else 74
        str_h = h1.strftime('%H:%M %p') + (f" a {h2.strftime('%H:%M %p')}" if h2 else "")
        dibujar_texto_sombra(draw, str_h, cx, y_box + h_caja + 114, get_font("Canaro-ExtraBold.ttf", s_h), offset=(3,3), anchor="mm")
    return y_box

def draw_caja_larga(img, draw, f1, f2, h1, h2, lugar, y_loc_top, is_right):
    y_base = Y_BOTTOM_BASELINE if is_right or not lugar else (y_loc_top - 80)
    if not f1: return y_base

    # LA CAJA LARGA SIEMPRE MIDE 360, NUNCA SE ACHICA
    h_caja = 360
    is_dual_month = f2 and (f1.month != f2.month)
    
    if is_dual_month: 
        w_caja = 680
    else:
        txt_d = f"{f1.day} al {f2.day}" if f2 else str(f1.day)
        txt_m = obtener_mes_nombre(f1.month)
        w_caja = max(600, int(max(get_text_width(get_font("Canaro-Black.ttf", 150), txt_d), get_text_width(get_font("Canaro-Black.ttf", 120), txt_m)) + 200))
    
    # Gravedad si no hay hora
    offset_y = 90 if h1 else 40
    if is_dual_month and h1: offset_y = 45 

    y_box = y_base - offset_y - h_caja
    
    if os.path.exists("flyer_caja_fecha_larga.png"):
        c = Image.open("flyer_caja_fecha_larga.png").convert("RGBA").resize((w_caja, h_caja), Image.Resampling.LANCZOS)
        img.paste(c, (SIDE_MARGIN, int(y_box)), c); c_f = "white"
    else: draw.rectangle([SIDE_MARGIN, y_box, SIDE_MARGIN+w_caja, y_box+h_caja], fill="white"); c_f = "black"
        
    cx, cy = SIDE_MARGIN + w_caja/2, y_box + h_caja/2
    
    if is_dual_month:
        cxl = cx - 175
        cxr = cx + 175
        draw.text((cxl, cy - 40), str(f1.day), font=get_font("Canaro-Black.ttf", 150), fill=c_f, anchor="mm")
        draw.text((cxl, cy + 85), obtener_mes_abbr(f1.month), font=get_font("Canaro-Black.ttf", 100), fill=c_f, anchor="mm")
        draw.text((cx, cy + 10), "al", font=get_font("Canaro-Black.ttf", 80), fill=c_f, anchor="mm")
        draw.text((cxr, cy - 40), str(f2.day), font=get_font("Canaro-Black.ttf", 150), fill=c_f, anchor="mm")
        draw.text((cxr, cy + 85), obtener_mes_abbr(f2.month), font=get_font("Canaro-Black.ttf", 100), fill=c_f, anchor="mm")
    else:
        draw.text((cx, cy - 40), txt_d, font=get_font("Canaro-Black.ttf", 150), fill=c_f, anchor="mm")
        draw.text((cx, cy + 85), txt_m, font=get_font("Canaro-Black.ttf", 120), fill=c_f, anchor="mm")
    
    if h1:
        s_h = 64 if (is_dual_month and h2) else 84 if is_dual_month else 54 if h2 else 74
        str_h = h1.strftime('%H:%M %p') + (f" a {h2.strftime('%H:%M %p')}" if h2 else "")
        y_time = y_box + h_caja + (36 if is_dual_month else 72)
        dibujar_texto_sombra(draw, str_h, cx, y_time, get_font("Canaro-ExtraBold.ttf", s_h), offset=(3,3), anchor="mm")
    return y_box

def draw_textos(draw, is_center, is_plural, d1, d2, y_box, three_logos_top=False, mostrar_titulo=True):
    tit = "INVITAN" if is_plural else "INVITA"
    y_tit = 850 if not d2 else 690
    if three_logos_top: y_tit -= 80 
    
    if is_center:
        max_w_d1 = W - (220 * 2) 
        if mostrar_titulo:
            dibujar_texto_sombra(draw, tit, W/2, y_tit, get_font("Canaro-Bold.ttf", S_INVITA_CENTER), offset=(6,6))
            s_d1 = 110 if len(d1)<=75 else 90 if len(d1)<=120 else 75
            y_d = y_tit + 150
        else:
            y_d = y_tit
            s_d1 = 130 if len(d1)<=75 else 110 if len(d1)<=120 else 90

        f_d1 = get_font("Canaro-SemiBold.ttf", s_d1)
        lines_d1 = wrap_text_pixel(d1, f_d1, max_w_d1)
        for l in lines_d1: 
            dibujar_texto_sombra(draw, l, W/2, y_d, f_d1, offset=(4,4))
            y_d += int(s_d1*1.1)
            
        if d2:
            s_d2, f_d2 = 85, get_font("Canaro-SemiBold.ttf", 85)
            lines_d2 = wrap_text_pixel(d2, f_d2, int(W*0.6*0.75))
            y_d2 = y_box - 42 - len(lines_d2)*int(s_d2*1.15) + int(s_d2*1.15)
            for l in lines_d2: 
                dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_d2, f_d2, anchor="ls", offset=(3,3))
                y_d2 += int(s_d2*1.15)
    else:
        if mostrar_titulo:
            dibujar_texto_sombra(draw, tit, SIDE_MARGIN, y_tit, get_font("Canaro-Bold.ttf", S_INVITA_LEFT), offset=(5,5), anchor="lm")
            y_start_d1 = y_tit + 160 
            start_size_d1 = 100
        else:
            y_start_d1 = y_tit
            start_size_d1 = S_INVITA_LEFT
            
        if d2:
            s_d2, f_d2 = 85, get_font("Canaro-SemiBold.ttf", 85)
            lines_d2 = wrap_text_pixel(d2, f_d2, int(W*0.4*0.75))
            y_d2_top = y_box - 42 - len(lines_d2)*int(s_d2*1.15)
            f_d1, lines_d1, s_d1 = calcular_fuente_dinamica(d1, "Canaro-SemiBold.ttf", start_size_d1, int(W*0.4), y_d2_top - y_start_d1 - 50)
            y_d = y_start_d1
            for l in lines_d1: dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_d, f_d1, offset=(3,3), anchor="ls"); y_d += int(s_d1*1.15)
            y_d2 = y_d2_top + int(s_d2*1.15)
            for l in lines_d2: dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_d2, f_d2, offset=(3,3), anchor="ls"); y_d2 += int(s_d2*1.15)
        else:
            f_d1, lines_d1, s_d1 = calcular_fuente_dinamica(d1, "Canaro-SemiBold.ttf", start_size_d1, int(W*0.4), y_box - y_start_d1 - 50)
            y_d = y_start_d1
            for l in lines_d1: dibujar_texto_sombra(draw, l, SIDE_MARGIN, y_d, f_d1, offset=(3,3), anchor="ls"); y_d += int(s_d1*1.15)

def draw_logos_t1t4(img, is_center):
    min_x = W
    pref = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378) if os.path.exists("flyer_logo.png") else None
    y_center = 150 + (pref.height // 2 if pref else 378 // 2)
    
    if is_center:
        if pref: img.paste(pref, (200, 150), pref)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            img.paste(f, (W-f.width-200, y_center - f.height//2), f)
    else:
        if pref: img.paste(pref, ((W-pref.width)//2, 150), pref)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            x = W-f.width-SIDE_MARGIN
            img.paste(f, (x, Y_BOTTOM_BASELINE-f.height+50), f)
            min_x = min(min_x, x)
    return min_x

def draw_logos_t5t8(img, datos, var_type):
    min_x = W
    l_list = datos.get('logos', [])
    collab_img = load_logo_single_bottom(l_list[0]) if (l_list and var_type in [1, 3]) else load_logo_shared(l_list[0], top_count=2) if l_list else None
    pref = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378) if os.path.exists("flyer_logo.png") else None
    y_center = 150 + (pref.height // 2 if pref else 378 // 2)
    
    if var_type in [1, 3]:
        if pref: img.paste(pref, (200, 150), pref)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            img.paste(f, (W-f.width-200, y_center - f.height//2), f)
        if collab_img: 
            x = W - SIDE_MARGIN - collab_img.width
            img.paste(collab_img, (x, int(Y_BOTTOM_BASELINE - collab_img.height + 20)), collab_img)
            min_x = min(min_x, x)
    else:
        if pref: img.paste(pref, (300, 150), pref)
        if collab_img: img.paste(collab_img, (W - 300 - collab_img.width, y_center - collab_img.height//2), collab_img)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            x = W-f.width-SIDE_MARGIN
            img.paste(f, (x, Y_BOTTOM_BASELINE-f.height+50), f)
            min_x = min(min_x, x)
    return min_x

def draw_logos_t9t12(img, datos, var_type):
    min_x = W
    l_list = datos.get('logos', [])
    c1 = load_logo_shared(l_list[0], top_count=(3 if var_type in [2,4] else 0)) if len(l_list) > 0 else None
    c2 = load_logo_shared(l_list[1], top_count=(3 if var_type in [2,4] else 0)) if len(l_list) > 1 else None
    pref = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775) if os.path.exists("flyer_logo.png") else None
    y_center = 150 + (pref.height // 2 if pref else 378 // 2)

    if var_type in [1, 3]:
        pref_h = resize_por_alto(Image.open("flyer_logo.png").convert("RGBA"), 378) if os.path.exists("flyer_logo.png") else None
        y_c2 = 150 + (pref_h.height//2 if pref_h else 378//2)
        if pref_h: img.paste(pref_h, (200, 150), pref_h)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            img.paste(f, (W-f.width-200, y_c2 - f.height//2), f)
        xc = W - SIDE_MARGIN
        if c2: xc -= c2.width; img.paste(c2, (int(xc), int(Y_BOTTOM_BASELINE - c2.height + 20)), c2); min_x = min(min_x, xc); xc -= 65
        if c1: xc -= c1.width; img.paste(c1, (int(xc), int(Y_BOTTOM_BASELINE - c1.height + 20)), c1); min_x = min(min_x, xc)
    else:
        w1, w2, w3 = (c1.width if c1 else 0), (pref.width if pref else 0), (c2.width if c2 else 0)
        gap = (W - (w1+w2+w3))/4
        if c1: img.paste(c1, (int(gap), y_center - c1.height//2), c1)
        if pref: img.paste(pref, (int(gap*2 + w1), 150), pref)
        if c2: img.paste(c2, (int(gap*3 + w1 + w2), y_center - c2.height//2), c2)
        if os.path.exists("flyer_firma.png"): 
            f = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265)
            x = W-f.width-SIDE_MARGIN
            img.paste(f, (x, Y_BOTTOM_BASELINE-f.height+50), f)
            min_x = min(min_x, x)
    return min_x

def draw_logos_tc(img, datos, var_type):
    min_x = W
    int_path, t_int, l_list = datos.get('logo_interno'), datos.get('tipo_interno'), datos.get('logos', [])
    c1 = load_logo_shared(l_list[0], top_count=(3 if var_type in [2,4] else 0)) if len(l_list) > 0 else None
    c2 = load_logo_shared(l_list[1], top_count=(3 if var_type in [2,4] else 0)) if len(l_list) > 1 else None
    int_img = (redim_interno_comp(Image.open(int_path).convert("RGBA"), t_int, top_count=(3 if var_type in [1,3] else 0)) if t_int in ["movida","orquesta","extremo"] else redim_collab_top(Image.open(int_path).convert("RGBA"))) if int_path else None
    pref_img = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775) if os.path.exists("flyer_logo.png") else None
    firma_img = resize_por_alto(Image.open("flyer_firma.png").convert("RGBA"), 265) if os.path.exists("flyer_firma.png") else None
    y_center = 150 + (pref_img.height // 2 if pref_img else 378 // 2)

    if var_type in [1, 3]: 
        w1, w2, w3 = (int_img.width if int_img else 0), (pref_img.width if pref_img else 0), (firma_img.width if firma_img else 0)
        gap = (W - (w1 + w2 + w3)) / 4
        if int_img: img.paste(int_img, (int(gap), y_center - int_img.height//2), int_img)
        if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
        if firma_img: img.paste(firma_img, (int(gap*3 + w1 + w2), y_center - firma_img.height//2), firma_img)
        xc = W - SIDE_MARGIN
        if c2: xc -= c2.width; img.paste(c2, (int(xc), int(Y_BOTTOM_BASELINE - c2.height + 20)), c2); min_x = min(min_x, xc); xc -= 65
        if c1: xc -= c1.width; img.paste(c1, (int(xc), int(Y_BOTTOM_BASELINE - c1.height + 20)), c1); min_x = min(min_x, xc)
    else:
        w1, w2, w3 = (c1.width if c1 else 0), (pref_img.width if pref_img else 0), (c2.width if c2 else 0)
        gap = (W - (w1 + w2 + w3)) / 4
        if c1: img.paste(c1, (int(gap), y_center - c1.height//2), c1)
        if pref_img: img.paste(pref_img, (int(gap*2 + w1), 150), pref_img)
        if c2: img.paste(c2, (int(gap*3 + w1 + w2), y_center - c2.height//2), c2)
        xc = W - SIDE_MARGIN
        if firma_img: xc -= firma_img.width; img.paste(firma_img, (int(xc), int(Y_BOTTOM_BASELINE - firma_img.height + 50)), firma_img); min_x = min(min_x, xc); xc -= 65
        if int_img: xc -= int_img.width; img.paste(int_img, (int(xc), int(Y_BOTTOM_BASELINE - int_img.height + 20)), int_img); min_x = min(min_x, xc)
    return min_x

def draw_logos_doble(img, datos, var_type):
    min_x = W
    l_list = datos.get('logos', [])
    c1 = load_logo_shared(l_list[0], top_count=3) if len(l_list) > 0 else None
    c2 = load_logo_shared(l_list[1], top_count=3) if len(l_list) > 1 else None
    pref = resize_por_ancho(Image.open("flyer_logo.png").convert("RGBA"), 775) if os.path.exists("flyer_logo.png") else None
    y_center = 150 + (pref.height // 2 if pref else 378 // 2)

    w1, w2, w3 = (c1.width if c1 else 0), (pref.width if pref else 0), (c2.width if c2 else 0)
    gap = (W - (w1+w2+w3))/4
    if c1: img.paste(c1, (int(gap), y_center - c1.height//2), c1)
    if pref: img.paste(pref, (int(gap*2 + w1), 150), pref)
    if c2: img.paste(c2, (int(gap*3 + w1 + w2), y_center - c2.height//2), c2)

    orq = redim_doble_orquesta(Image.open("logo.orquesta.png").convert("RGBA")) if os.path.exists("logo.orquesta.png") else None
    mov = redim_doble_movida(Image.open("logo.movida.png").convert("RGBA")) if os.path.exists("logo.movida.png") else None
    firma = resize_por_ancho(Image.open("flyer_firma.png").convert("RGBA"), 400) if os.path.exists("flyer_firma.png") else None

    xc = W - SIDE_MARGIN
    if firma: xc -= firma.width; img.paste(firma, (int(xc), int(Y_BOTTOM_BASELINE - firma.height + 50)), firma); min_x = min(min_x, xc); xc -= 65
    if mov: xc -= mov.width; img.paste(mov, (int(xc), int(Y_BOTTOM_BASELINE - mov.height + 20)), mov); min_x = min(min_x, xc); xc -= 65
    if orq: xc -= orq.width; img.paste(orq, (int(xc), int(Y_BOTTOM_BASELINE - orq.height + 20)), orq); min_x = min(min_x, xc)
    return min_x

# ==============================================================================
# 4. RENDERIZADORES DE PLANTILLAS
# ==============================================================================

def generar_tipo_1_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, True, False, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_1_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, False, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_1_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, False, False, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_1_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, False, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_2_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, True, False, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_2_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, False, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_2_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, False, False, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_2_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, False, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_3_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_3_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_3_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_3_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_4_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_4_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_4_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, True); y_loc = draw_ubicacion(img, draw, d['lugar'], True, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, True); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_4_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t1t4(img, False); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_5_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_5_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_5_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_5_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_6_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_6_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_6_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_6_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_7_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_7_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_7_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_7_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_8_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_8_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_8_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_8_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t5t8(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_9_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_10_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_11_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_12_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, False, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_t9t12(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 600, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_9_c_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_c_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_c_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_c_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_10_c_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_c_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_c_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_c_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_11_c_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_c_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_c_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_c_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_12_c_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_c_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_c_v3(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 3); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_c_v4(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_tc(img, d, 4); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 300, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_9_doble_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_9_doble_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_10_doble_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_10_doble_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_cuadrada(img, draw, d['fecha1'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_11_doble_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_11_doble_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d.get('desc2',''), y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")

def generar_tipo_12_doble_v1(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 1); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, True, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")
def generar_tipo_12_doble_v2(d): img, draw = init_canvas(d['fondo']); min_x = draw_logos_doble(img, d, 2); y_loc = draw_ubicacion(img, draw, d['lugar'], False, min_x, 250, d.get('icono_contacto','lugar')); y_box = draw_caja_larga(img, draw, d['fecha1'], d['fecha2'], d['hora1'], d['hora2'], d['lugar'], y_loc, False); draw_textos(draw, False, True, d['desc1'], d['desc2'], y_box, True, d.get('mostrar_titulo',True)); return img.convert("RGB")


# ==============================================================================
# 5. INTERFAZ DE USUARIO Y ENRUTADOR PRINCIPAL
# ==============================================================================

if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

query_params = st.query_params
area_seleccionada = query_params.get("area", None)

if not area_seleccionada:
    st.markdown("<h2 style='text-align: center; color: white;'>SELECCIONA EL DEPARTAMENTO:</h2>", unsafe_allow_html=True)
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
    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c2:
         if os.path.exists("firma_jota.png"): st.image("firma_jota.png", use_container_width=True)

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
        if os.path.exists(icono): st.image(icono, width=350) 
        st.write("") 
        if os.path.exists("firma_jota.png"): st.image("firma_jota.png", width=200)

    with col_der:
        st.markdown("<div class='label-negro' style='margin-top: 15px;'>FORMATO DEL FLYER</div>", unsafe_allow_html=True)
        formato = st.radio("Formato", ["Publicación", "Historia"], key="temp_formato", horizontal=True, label_visibility="collapsed", on_change=on_format_change, index=0 if st.session_state.saved_formato=="Publicación" else 1)

        c_tit, _ = st.columns([3,1])
        with c_tit:
            mostrar_titulo = st.checkbox("Mostrar título (INVITA / INVITAN)", value=st.session_state.saved_titulo, key="temp_titulo")

        st.markdown("<div class='label-negro'>DESCRIPCIÓN 1</div>", unsafe_allow_html=True)
        desc1 = st.text_area("d1", key="temp_d1", label_visibility="collapsed", placeholder="Escribe aqui...", height=150, max_chars=175, value=st.session_state.saved_d1)
        
        st.markdown("<div class='label-negro'>DESCRIPCIÓN 2 (OPCIONAL)</div>", unsafe_allow_html=True)
        desc2 = st.text_area("d2", key="temp_d2", label_visibility="collapsed", placeholder="", height=100, max_chars=175, value=st.session_state.saved_d2)
        
        total_chars = len(desc1) + len(desc2)
        color_c = "red" if total_chars > 175 else "black"
        st.markdown(f"<p style='text-align:right; color:{color_c}; font-size:12px; margin-top:-10px;'>Total caracteres: {total_chars} / 175</p>", unsafe_allow_html=True)

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown("<div class='label-negro'>FECHA INICIO (OPCIONAL)</div>", unsafe_allow_html=True)
            cc1, cc2 = st.columns([5, 1])
            with cc1: fecha1 = st.date_input("f1", key="temp_f1", label_visibility="collapsed", format="DD/MM/YYYY", value=st.session_state.saved_f1)
            with cc2: 
                if st.button("❌", key="x_f1", help="Borrar Fecha"): 
                    st.session_state.saved_f1 = None
                    st.session_state.saved_h1 = None
                    st.session_state.saved_h2 = None
                    st.session_state.saved_f2 = None
                    st.rerun()

        with c_f2:
            st.markdown("<div class='label-negro'>FECHA FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            cc1, cc2 = st.columns([5, 1])
            with cc1: fecha2 = st.date_input("f2", key="temp_f2", label_visibility="collapsed", format="DD/MM/YYYY", value=st.session_state.saved_f2)
            with cc2: 
                if st.button("❌", key="x_f2", help="Borrar Fecha Final"): 
                    st.session_state.saved_f2 = None
                    st.rerun()
        
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown("<div class='label-negro'>HORARIO INICIO (OPCIONAL)</div>", unsafe_allow_html=True)
            cc1, cc2 = st.columns([5, 1])
            with cc1: hora1 = st.time_input("h1", key="temp_h1", label_visibility="collapsed", value=st.session_state.saved_h1)
            with cc2:
                if st.button("❌", key="x_h1", help="Borrar Horario"): 
                    st.session_state.saved_h1 = None
                    st.session_state.saved_h2 = None
                    st.rerun()

        with c_h2:
            st.markdown("<div class='label-negro'>HORARIO FINAL (OPCIONAL)</div>", unsafe_allow_html=True)
            cc1, cc2 = st.columns([5, 1])
            with cc1: hora2 = st.time_input("h2", key="temp_h2", label_visibility="collapsed", value=st.session_state.saved_h2)
            with cc2:
                if st.button("❌", key="x_h2", help="Borrar Horario Final"): 
                    st.session_state.saved_h2 = None
                    st.rerun()
        
        st.write("")
        tipo_contacto = st.radio("SELECCIONA TIPO DE CONTACTO:", ["Ubicación", "Celular"], horizontal=True, key="temp_rad", index=0 if st.session_state.saved_rad=="Ubicación" else 1)
        
        if tipo_contacto == "Ubicación":
            st.markdown("<div class='label-negro'>DIRECCIÓN</div>", unsafe_allow_html=True)
            dir_texto = st.text_input("dir", key="temp_dir", label_visibility="collapsed", placeholder="Ubicación del evento", max_chars=80, value=st.session_state.saved_dir)
            tel1 = st.session_state.saved_tel1
            tel2 = st.session_state.saved_tel2
            icono_contacto = "lugar"
        else:
            st.markdown("<div class='label-negro'>NÚMEROS DE CELULAR</div>", unsafe_allow_html=True)
            col_t1, col_t2 = st.columns(2)
            with col_t1: tel1 = st.text_input("tel1", key="temp_tel1", label_visibility="collapsed", placeholder="Celular 1", value=st.session_state.saved_tel1)
            with col_t2: tel2 = st.text_input("tel2", key="temp_tel2", label_visibility="collapsed", placeholder="Celular 2", value=st.session_state.saved_tel2)
            celulares = []
            if tel1: celulares.append(tel1)
            if tel2: celulares.append(tel2)
            dir_texto = "\n".join(celulares)
            icono_contacto = "celular"

        usar_movida = False
        usar_orquesta = False
        if area_seleccionada == "Culturas":
            st.markdown("<div class='label-negro' style='margin-top: 5px;'>LOGOS INTERNOS DEL DEPARTAMENTO</div>", unsafe_allow_html=True)
            col_chk1, col_chk2 = st.columns(2)
            with col_chk1: usar_movida = st.checkbox("Usar logo de La Movida", key="temp_movida", value=st.session_state.saved_movida)
            with col_chk2: usar_orquesta = st.checkbox("Usar logo de La Orquesta", key="temp_orquesta", value=st.session_state.saved_orquesta)
        elif area_seleccionada == "Recreación":
            st.markdown("<div class='label-negro' style='margin-top: 5px; color:transparent;'>Espacio Reservado</div>", unsafe_allow_html=True)

        st.markdown("<div class='label-negro' style='margin-top: 15px;'>LOGOS COLABORADORES EXTERNOS</div>", unsafe_allow_html=True)
        col_logo1, col_logo2 = st.columns(2)
        
        logo1 = logo2 = None
        with col_logo1:
            if st.session_state.ruta_logo1 and os.path.exists(st.session_state.ruta_logo1):
                st.success("✅ LOGO EXTR. 1 LISTO")
                if st.button("❌ QUITAR LOGO 1", key="del_l1", use_container_width=True): st.session_state.ruta_logo1 = None; st.rerun()
            else: logo1 = st.file_uploader("l1", type=['png', 'jpg', 'jpeg'], key="l1", label_visibility="collapsed")
                
        with col_logo2:
            if st.session_state.ruta_logo2 and os.path.exists(st.session_state.ruta_logo2):
                st.success("✅ LOGO EXTR. 2 LISTO")
                if st.button("❌ QUITAR LOGO 2", key="del_l2", use_container_width=True): st.session_state.ruta_logo2 = None; st.rerun()
            else: logo2 = st.file_uploader("l2", type=['png', 'jpg', 'jpeg'], key="l2", label_visibility="collapsed")
        
        st.markdown("<div class='label-negro' style='margin-top: 15px;'>SUBIR Y RECORTAR IMAGEN DE FONDO</div>", unsafe_allow_html=True)
        if 'v_fondo' in st.session_state: st.success("✅ IMAGEN DE FONDO GUARDADA. Sube otra si deseas cambiarla.")
        
        archivo_subido = st.file_uploader("img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        if archivo_subido:
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte y presiona Submit.")
            img_crop = st_cropper(img_orig, realtime_update=True, aspect_ratio=CROP_RATIO, should_resize_image=False)
            st.session_state['v_fondo'] = img_crop.resize((W, H), Image.Resampling.LANCZOS)
            st.write("✅ Nueva imagen lista.")

        st.write("")
        if st.button("GENERAR FLYERS AZUAY", type="primary", use_container_width=True):
            errores = []
            if not desc1: errores.append("Falta Descripcion 1")
            if 'v_fondo' not in st.session_state: errores.append("Falta recortar la Imagen de Fondo")
            if total_chars > 175: errores.append("Excediste el límite de 175 caracteres combinados")

            if errores:
                for e in errores: st.error(f"⚠️ {e}")
            else:
                if not fecha1:
                    hora1, hora2, fecha2 = None, None, None
                if not hora1:
                    hora2 = None

                if logo1:
                    with open("temp_logo1.png", "wb") as f: f.write(logo1.getvalue())
                    st.session_state.ruta_logo1 = "temp_logo1.png"
                if logo2:
                    with open("temp_logo2.png", "wb") as f: f.write(logo2.getvalue())
                    st.session_state.ruta_logo2 = "temp_logo2.png"

                # G U A R D A D O   D E   M E M O R I A   S E G U R A
                st.session_state.saved_d1 = desc1
                st.session_state.saved_d2 = desc2
                st.session_state.saved_f1 = fecha1
                st.session_state.saved_f2 = fecha2
                st.session_state.saved_h1 = hora1
                st.session_state.saved_h2 = hora2
                st.session_state.saved_rad = tipo_contacto
                st.session_state.saved_titulo = mostrar_titulo
                st.session_state.saved_formato = formato
                if tipo_contacto == "Ubicación": st.session_state.saved_dir = dir_texto
                else: 
                    st.session_state.saved_tel1 = tel1
                    st.session_state.saved_tel2 = tel2
                if area_seleccionada == "Culturas":
                    st.session_state.saved_movida = usar_movida
                    st.session_state.saved_orquesta = usar_orquesta

                rutas_externos = []
                if st.session_state.ruta_logo1 and os.path.exists(st.session_state.ruta_logo1): rutas_externos.append(st.session_state.ruta_logo1)
                if st.session_state.ruta_logo2 and os.path.exists(st.session_state.ruta_logo2): rutas_externos.append(st.session_state.ruta_logo2)
                
                internos_paths = []
                if area_seleccionada == "Culturas":
                    if usar_movida and os.path.exists("logo.movida.png"): internos_paths.append("logo.movida.png")
                    if usar_orquesta and os.path.exists("logo.orquesta.png"): internos_paths.append("logo.orquesta.png")
                elif area_seleccionada == "Recreación":
                    if os.path.exists("logo.extremo.png"): internos_paths.append("logo.extremo.png")

                num_ext = len(rutas_externos)
                num_int = len(internos_paths)

                datos = {'fondo': st.session_state.v_fondo, 'desc1': desc1, 'desc2': desc2, 'fecha1': fecha1, 'fecha2': fecha2, 'hora1': hora1, 'hora2': hora2, 'lugar': dir_texto, 'icono_contacto': icono_contacto, 'mostrar_titulo': mostrar_titulo}
                generated = {}
                tid = "N/A"
                
                # ENRUTAMIENTO INTELIGENTE
                if num_int == 2 and num_ext == 2:
                    datos['logos'] = rutas_externos 
                    if fecha2 and desc2: generated = {'t12d_v1': generar_tipo_12_doble_v1(datos), 't12d_v2': generar_tipo_12_doble_v2(datos)}; tid = "12_Doble"
                    elif fecha2 and not desc2: generated = {'t11d_v1': generar_tipo_11_doble_v1(datos), 't11d_v2': generar_tipo_11_doble_v2(datos)}; tid = "11_Doble"
                    elif not fecha2 and desc2: generated = {'t10d_v1': generar_tipo_10_doble_v1(datos), 't10d_v2': generar_tipo_10_doble_v2(datos)}; tid = "10_Doble"
                    else: generated = {'t9d_v1': generar_tipo_9_doble_v1(datos), 't9d_v2': generar_tipo_9_doble_v2(datos)}; tid = "9_Doble"
                        
                elif num_int == 2 and num_ext == 1:
                    datos['logo_interno'] = rutas_externos[0]
                    datos['tipo_interno'] = "collab"
                    datos['logos'] = internos_paths 
                    if fecha2 and desc2: generated = {'t12c_v1': generar_tipo_12_c_v1(datos), 't12c_v2': generar_tipo_12_c_v2(datos), 't12c_v3': generar_tipo_12_c_v3(datos), 't12c_v4': generar_tipo_12_c_v4(datos)}; tid = "12_Especial"
                    elif fecha2 and not desc2: generated = {'t11c_v1': generar_tipo_11_c_v1(datos), 't11c_v2': generar_tipo_11_c_v2(datos), 't11c_v3': generar_tipo_11_c_v3(datos), 't11c_v4': generar_tipo_11_c_v4(datos)}; tid = "11_Especial"
                    elif not fecha2 and desc2: generated = {'t10c_v1': generar_tipo_10_c_v1(datos), 't10c_v2': generar_tipo_10_c_v2(datos), 't10c_v3': generar_tipo_10_c_v3(datos), 't10c_v4': generar_tipo_10_c_v4(datos)}; tid = "10_Especial"
                    else: generated = {'t9c_v1': generar_tipo_9_c_v1(datos), 't9c_v2': generar_tipo_9_c_v2(datos), 't9c_v3': generar_tipo_9_c_v3(datos), 't9c_v4': generar_tipo_9_c_v4(datos)}; tid = "9_Especial"

                elif num_int == 1 and num_ext == 2:
                    datos['logo_interno'] = internos_paths[0]
                    datos['tipo_interno'] = get_tipo_logo(internos_paths[0])
                    datos['logos'] = rutas_externos 
                    if fecha2 and desc2: generated = {'t12c_v1': generar_tipo_12_c_v1(datos), 't12c_v2': generar_tipo_12_c_v2(datos), 't12c_v3': generar_tipo_12_c_v3(datos), 't12c_v4': generar_tipo_12_c_v4(datos)}; tid = "12_Especial"
                    elif fecha2 and not desc2: generated = {'t11c_v1': generar_tipo_11_c_v1(datos), 't11c_v2': generar_tipo_11_c_v2(datos), 't11c_v3': generar_tipo_11_c_v3(datos), 't11c_v4': generar_tipo_11_c_v4(datos)}; tid = "11_Especial"
                    elif not fecha2 and desc2: generated = {'t10c_v1': generar_tipo_10_c_v1(datos), 't10c_v2': generar_tipo_10_c_v2(datos), 't10c_v3': generar_tipo_10_c_v3(datos), 't10c_v4': generar_tipo_10_c_v4(datos)}; tid = "10_Especial"
                    else: generated = {'t9c_v1': generar_tipo_9_c_v1(datos), 't9c_v2': generar_tipo_9_c_v2(datos), 't9c_v3': generar_tipo_9_c_v3(datos), 't9c_v4': generar_tipo_9_c_v4(datos)}; tid = "9_Especial"
                        
                else:
                    logos_combinados = internos_paths + rutas_externos
                    logos_combinados = logos_combinados[:2]
                    datos['logos'] = logos_combinados
                    num_lg = len(logos_combinados)
                    
                    if num_lg == 2 and fecha2 and desc2: generated = {'t12_v1': generar_tipo_12_v1(datos), 't12_v2': generar_tipo_12_v2(datos), 't12_v3': generar_tipo_12_v3(datos), 't12_v4': generar_tipo_12_v4(datos)}; tid = 12
                    elif num_lg == 2 and fecha2 and not desc2: generated = {'t11_v1': generar_tipo_11_v1(datos), 't11_v2': generar_tipo_11_v2(datos), 't11_v3': generar_tipo_11_v3(datos), 't11_v4': generar_tipo_11_v4(datos)}; tid = 11
                    elif num_lg == 2 and not fecha2 and desc2: generated = {'t10_v1': generar_tipo_10_v1(datos), 't10_v2': generar_tipo_10_v2(datos), 't10_v3': generar_tipo_10_v3(datos), 't10_v4': generar_tipo_10_v4(datos)}; tid = 10
                    elif num_lg == 2 and not fecha2 and not desc2: generated = {'t9_v1': generar_tipo_9_v1(datos), 't9_v2': generar_tipo_9_v2(datos), 't9_v3': generar_tipo_9_v3(datos), 't9_v4': generar_tipo_9_v4(datos)}; tid = 9
                    elif num_lg == 1 and fecha2 and desc2: generated = {'t8_v1': generar_tipo_8_v1(datos), 't8_v2': generar_tipo_8_v2(datos), 't8_v3': generar_tipo_8_v3(datos), 't8_v4': generar_tipo_8_v4(datos)}; tid = 8
                    elif num_lg == 1 and fecha2 and not desc2: generated = {'t7_v1': generar_tipo_7_v1(datos), 't7_v2': generar_tipo_7_v2(datos), 't7_v3': generar_tipo_7_v3(datos), 't7_v4': generar_tipo_7_v4(datos)}; tid = 7
                    elif num_lg == 1 and not fecha2 and desc2: generated = {'t6_v1': generar_tipo_6_v1(datos), 't6_v2': generar_tipo_6_v2(datos), 't6_v3': generar_tipo_6_v3(datos), 't6_v4': generar_tipo_6_v4(datos)}; tid = 6
                    elif num_lg == 1 and not fecha2 and not desc2: generated = {'t5_v1': generar_tipo_5_v1(datos), 't5_v2': generar_tipo_5_v2(datos), 't5_v3': generar_tipo_5_v3(datos), 't5_v4': generar_tipo_5_v4(datos)}; tid = 5
                    elif num_lg == 0 and fecha2 and desc2: generated = {'t4_v1': generar_tipo_4_v1(datos), 't4_v2': generar_tipo_4_v2(datos), 't4_v3': generar_tipo_4_v3(datos), 't4_v4': generar_tipo_4_v4(datos)}; tid = 4
                    elif num_lg == 0 and fecha2 and not desc2: generated = {'t3_v1': generar_tipo_3_v1(datos), 't3_v2': generar_tipo_3_v2(datos), 't3_v3': generar_tipo_3_v3(datos), 't3_v4': generar_tipo_3_v4(datos)}; tid = 3
                    elif num_lg == 0 and not fecha2 and desc2: generated = {'t2_v1': generar_tipo_2_v1(datos), 't2_v2': generar_tipo_2_v2(datos), 't2_v3': generar_tipo_2_v3(datos), 't2_v4': generar_tipo_2_v4(datos)}; tid = 2
                    else: generated = {'v1': generar_tipo_1_v1(datos), 'v2': generar_tipo_1_v2(datos), 'v3': generar_tipo_1_v3(datos), 'v4': generar_tipo_1_v4(datos)}; tid = 1
                
                st.session_state.update({'gen_imgs': generated, 'tid': tid, 'sel_var': list(generated.keys())[0]})
                st.query_params['area'] = 'Final'
                st.rerun()

elif area_seleccionada == "Final":
    st.markdown("<h1 style='text-align: center; color: white; text-shadow: 2px 2px 4px #000; font-size: 60px;'>¡ARTE LISTO!</h1>", unsafe_allow_html=True)
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
                    if st.button("⬅️", key="prev_btn", type="secondary", use_container_width=True):
                        st.session_state.sel_var = vars_list[(idx-1)%len(vars_list)]
                        st.rerun()
            
            with c_d:
                buf = io.BytesIO()
                imgs[sel].save(buf, format="PNG")
                b64_dl = base64.b64encode(buf.getvalue()).decode()
                
                if os.path.exists("mascota_final.png"):
                    m_b64 = get_base64_of_bin_file("mascota_final.png")
                    html_btn = (
                        "<div style='text-align: center;'>"
                        f"<a href='data:image/png;base64,{b64_dl}' download='flyer_azuay_{sel}.png' style='text-decoration: none; border: none !important; outline: none !important;'>"
                        f"<img src='data:image/png;base64,{m_b64}' width='220' class='zoom-hover' style='border: none !important; outline: none !important; display: block; margin: auto;'>"
                        "<div style='font-family: \"Canaro\"; font-weight: bold; font-size: 18px; color: white; margin-top: 5px; text-decoration: none; text-shadow: 1px 1px 2px black;'>DESCARGUE AQUI</div>"
                        "</a></div>"
                    )
                    st.markdown(html_btn, unsafe_allow_html=True)
                else:
                    st.download_button("⬆️ DESCARGAR", buf.getvalue(), f"flyer_azuay_{sel}.png", "image/png", use_container_width=True)

            with c_n:
                if len(vars_list) > 1:
                    if st.button("➡️", key="next_btn", type="secondary", use_container_width=True):
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
                if item.startswith("temp_") and item.endswith(".png"): os.remove(item)
            st.rerun()
