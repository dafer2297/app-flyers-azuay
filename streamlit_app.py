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
# 2. MOTOR GRÁFICO (LÓGICA DE DISEÑO)
# ==============================================================================

def dibujar_texto_sombra(draw, texto, x, y, fuente, color="white", sombra="black", offset=(6,6), anchor="mm"):
    # Sombra
    draw.text((x+offset[0], y+offset[1]), texto, font=fuente, fill=sombra, anchor=anchor)
    # Texto
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)

def obtener_mes_abbr(numero_mes):
    meses = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}
    return meses.get(numero_mes, "")

def obtener_dia_semana(fecha):
    dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    return dias[fecha.weekday()]

# --- PLANTILLA TIPO 1 (CULTURA - 1 FECHA) ---
def generar_tipo_1(datos):
    fondo = datos['fondo']
    desc1 = datos['desc1']
    fecha1 = datos['fecha1']
    hora1 = datos['hora1']
    hora2 = datos['hora2']
    lugar = datos['lugar']
    logos_colab = datos['logos']
    
    W, H = 2400, 3000
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 1. SOMBRA SUPERPUESTA (PNG)
    if os.path.exists("flyer_sombra.png"):
        sombra_img = Image.open("flyer_sombra.png").convert("RGBA")
        sombra_img = sombra_img.resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
    else:
        # Fallback si falta el archivo
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.3), H):
            alpha = int(255 * ((y - H*0.3)/(H*0.7)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.9)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img) 

    # --- FUENTES ---
    try:
        f_black_base = "Canaro-Black.ttf"
        f_bold_base = "Canaro-Bold.ttf"
        f_semibold_base = "Canaro-SemiBold.ttf" if os.path.exists("Canaro-SemiBold.ttf") else "Canaro-Bold.ttf"
        f_medium_base = "Canaro-Medium.ttf"
        
        # Tamaños Base
        size_invita = 180
        f_invita = ImageFont.truetype(f_bold_base, size_invita)
        
        # Fuentes Fecha Caja
        f_dia_box = ImageFont.truetype(f_black_base, 200) # Número Grande Black
        f_mes_box = ImageFont.truetype(f_bold_base, 90)   # Mes Bold
        f_info_fecha = ImageFont.truetype(f_bold_base, 65) # Día semana y hora
        f_lugar = ImageFont.truetype(f_medium_base, 70)    # Dirección Medium
        
    except:
        f_invita = f_dia_box = f_mes_box = f_info_fecha = f_lugar = ImageFont.load_default()
        f_semibold_base = "arial.ttf" # Fallback

    # --- A. LOGOS HEADER (DIVIDIDOS) ---
    y_logos = 150
    margin_logos = 100
    
    # 1. Logo Prefectura (Izquierda)
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA")
        # Ajuste de tamaño (ej: ancho 700)
        ratio = 700 / logo.width
        h_logo = int(logo.height * ratio)
        logo = logo.resize((700, h_logo), Image.Resampling.LANCZOS)
        img.paste(logo, (margin_logos, y_logos), logo)
    
    # 2. Logo Jota (Derecha)
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA")
        # Ajuste de tamaño (ej: ancho 500)
        ratio_f = 500 / firma.width
        h_firma = int(firma.height * ratio_f)
        firma = firma.resize((500, h_firma), Image.Resampling.LANCZOS)
        img.paste(firma, (W - 500 - margin_logos, y_logos + 20), firma) # Un poquito más abajo para alinear visualmente

    # --- B. TÍTULO ---
    titulo_texto = "INVITA"
    if logos_colab:
        titulo_texto = "INVITAN"
    
    y_titulo = 650
    dibujar_texto_sombra(draw, titulo_texto, W/2, y_titulo, f_invita)
    
    # --- C. DESCRIPCIÓN (AUTO-AJUSTE) ---
    y_desc = y_titulo + 150
    margen_desc = 200
    ancho_max_desc = W - (margen_desc * 2)
    
    # Lógica de tamaño dinámico (Máximo 3/5 del título = 180 * 0.6 = 108)
    size_desc = 108 
    
    # Ajustamos el tamaño hasta que quepa bien o llegue a un mínimo
    f_desc = ImageFont.truetype(f_semibold_base, size_desc)
    
    # Envolver texto y probar altura
    lines = textwrap.wrap(desc1, width=30) # Ancho inicial estimado
    
    # Si hay muchas líneas, reducimos la letra un poco
    if len(lines) > 4:
        size_desc = 90
        f_desc = ImageFont.truetype(f_semibold_base, size_desc)
        lines = textwrap.wrap(desc1, width=35) # Recalcular wrap con letra más chica
    
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc)
        y_desc += int(size_desc * 1.2) # Espaciado dinámico

    # --- D. CAJA DE FECHA (IZQUIERDA ABAJO) ---
    # Coordenadas
    x_box = 200
    y_box = 2100 
    
    if os.path.exists("flyer_caja_fecha.png"):
        caja = Image.open("flyer_caja_fecha.png").convert("RGBA")
        caja = caja.resize((450, 450), Image.Resampling.LANCZOS) # Cuadrado grande
        img.paste(caja, (x_box, y_box), caja)
        
        # Contenido de la Caja
        cx = x_box + 225 # Centro de la caja (450/2)
        cy = y_box + 225
        
        dia_num = str(fecha1.day)
        mes_txt = obtener_mes_abbr(fecha1.month)
        
        # Dibujar Número (Black)
        draw.text((cx, cy - 40), dia_num, font=f_dia_box, fill="white", anchor="mm")
        # Dibujar Mes (Bold)
        draw.text((cx, cy + 90), mes_txt, font=f_mes_box, fill="white", anchor="mm")
        
        # Debajo de la caja: Día semana y Hora
        dia_sem = obtener_dia_semana(fecha1)
        
        # Lógica Horario (Inicio o Inicio - Final)
        str_hora = hora1.strftime('%H:%M %p') # 12:00 PM
        if hora2:
            str_hora += f" a {hora2.strftime('%H:%M %p')}"
            
        # Dibujar Día
        y_info = y_box + 450 + 40
        dibujar_texto_sombra(draw, dia_sem, cx, y_info, f_info_fecha, anchor="mm")
        # Dibujar Hora
        dibujar_texto_sombra(draw, str_hora, cx, y_info + 80, f_info_fecha, anchor="mm")
        
    else:
        # Fallback texto plano
        draw.text((x_box, y_box), f"{fecha1.day} {obtener_mes_abbr(fecha1.month)}", font=f_invita, fill="white")

    # --- E. UBICACIÓN (DERECHA ABAJO) ---
    # Alineado con la caja de fecha visualmente
    x_loc = 1400 
    y_loc = 2250 
    
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA")
        icon = icon.resize((100, 100), Image.Resampling.LANCZOS)
        img.paste(icon, (x_loc, y_loc), icon)
        
        # Texto Dirección (Medium)
        # Envolvemos si es muy largo
        lines_loc = textwrap.wrap(lugar, width=25)
        y_loc_txt = y_loc + 10
        for l in lines_loc:
            dibujar_texto_sombra(draw, l, x_loc + 130, y_loc_txt, f_lugar, anchor="lm") # Anchor left-middle
            y_loc_txt += 80
            
    else:
        dibujar_texto_sombra(draw, f"📍 {lugar}", x_loc, y_loc, f_lugar, anchor="lm")

    return img

# --- RESTO DE PLANTILLAS (POR AHORA USAN LA 1) ---
def generar_tipo_2(datos): return generar_tipo_1(datos)
def generar_tipo_3(datos): return generar_tipo_1(datos)
def generar_tipo_4(datos): return generar_tipo_1(datos)
def generar_tipo_5(datos): return generar_tipo_1(datos)
def generar_tipo_6(datos): return generar_tipo_1(datos)
def generar_tipo_7(datos): return generar_tipo_1(datos)
def generar_tipo_8(datos): return generar_tipo_1(datos)
def generar_tipo_9(datos): return generar_tipo_1(datos)
def generar_tipo_10(datos): return generar_tipo_1(datos)
def generar_tipo_11(datos): return generar_tipo_1(datos)
def generar_tipo_12(datos): return generar_tipo_1(datos)

# --- CONTROLADOR MAESTRO ---
def generar_flyer_automatico(datos):
    # Por ahora forzamos Tipo 1 para probar tu diseño
    # Cuando hagamos las otras, descomentamos el árbol de decisión
    return generar_tipo_1(datos)

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
        st.markdown('<div class="label-negro">DESCRIPCIÓN</div>', unsafe_allow_html=True)
        desc1 = st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        desc2 = st.text_area("lbl_desc2", key="lbl_desc2", label_visibility="collapsed", placeholder="Información extra...", height=100)
        
        total_chars = len(desc1) + len(desc2)
        if total_chars <= 150:
            st.markdown(f'<div class="contador-ok">Caracteres: {total_chars} / 150 ✅</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="contador-mal">Caracteres: {total_chars} / 150 ❌ (Exceso: {total_chars - 150})</div>', unsafe_allow_html=True)

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
        dir_texto = st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")
        
        len_dir = len(dir_texto)
        if len_dir <= 75:
            st.markdown(f'<div class="contador-ok" style="font-size:12px;">Dirección: {len_dir} / 75</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="contador-mal">Dirección muy larga: {len_dir} / 75</div>', unsafe_allow_html=True)

        st.markdown('<div class="label-negro" style="margin-top: 15px;">SUBIR Y RECORTAR IMAGEN DE FONDO</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("lbl_img", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
        
        if archivo_subido:
            st.info("✂️ Ajusta el recuadro rojo. Se convertirá a HD automáticamente.")
            img_orig = Image.open(archivo_subido)
            img_crop = st_cropper(img_orig, realtime_update=True, box_color='#FF0000', aspect_ratio=(4, 5))
            st.session_state['imagen_lista_para_flyer'] = img_crop.resize((2400, 3000), Image.Resampling.LANCZOS)
            st.write("✅ Imagen lista.")

        st.markdown('<div class="label-negro">LOGOS COLABORADORES <span class="label-blanco">(MÁX 2)</span></div>', unsafe_allow_html=True)
        st.file_uploader("lbl_logos", key="lbl_logos", accept_multiple_files=True, label_visibility="collapsed")
        
        st.write("")
        
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
            errores = []
            if (len(st.session_state.lbl_desc) + len(st.session_state.lbl_desc2)) > 150: errores.append("Texto demasiado largo en descripción (Máx 150)")
            if len(st.session_state.lbl_dir) > 75: errores.append("Dirección demasiado larga (Máx 75 caracteres)")
            if not st.session_state.lbl_fecha1: errores.append("Falta la Fecha de Inicio")
            if 'imagen_lista_para_flyer' not in st.session_state: errores.append("Falta recortar la Imagen de Fondo")
                
            if errores:
                st.error(f"⚠️ {', '.join(errores)}")
            else:
                st.session_state['datos_finales'] = {
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
                st.query_params["area"] = "Final"
                st.rerun()

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
        if 'datos_finales' in st.session_state:
            paquete = st.session_state['datos_finales']
            flyer_final = generar_flyer_automatico(paquete)
            st.image(flyer_final, caption="Diseño Generado", use_container_width=True)
            buf = io.BytesIO()
            flyer_final.save(buf, format="PNG")
            byte_im = buf.getvalue()
        else:
            st.warning("⚠️ No hay datos. Vuelve al inicio.")
            if st.button("Volver al Inicio"):
                st.query_params.clear()
                st.rerun()

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
        keys_borrar = ['imagen_lista_para_flyer', 'datos_finales', 'lbl_desc', 'lbl_desc2']
        for k in keys_borrar:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
