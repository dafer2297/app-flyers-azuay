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

# --- PLANTILLA TIPO 1 ---
def generar_tipo_1(datos):
    fondo = datos['fondo']
    desc1 = datos['desc1']
    fecha1 = datos['fecha1']
    fecha2 = datos['fecha2']
    hora1 = datos['hora1']
    hora2 = datos['hora2']
    lugar = datos['lugar']
    logos_colab = datos['logos']
    
    W, H = 2400, 3000
    
    # CONSTANTES DE MÁRGENES (Aumentados para cumplir con el diseño)
    PADDING_BOTTOM = 250 
    PADDING_SIDES = 200

    # 1. LIENZO BASE
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 2. SOMBRA PNG
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

    # --- 3. CARGA DE FUENTES ---
    try:
        # TÍTULO: Tamaño reducido
        f_invita = ImageFont.truetype(ruta_abs("Canaro-Bold.ttf"), 250) 
        
        # CAJA FECHA:
        f_dia_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 350)
        f_mes_box = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 180) # Mes más pequeño que el número
        
        # DÍA SEMANA / HORA:
        path_extra = ruta_abs("Canaro-ExtraBold.ttf")
        if not os.path.exists(path_extra): path_extra = ruta_abs("Canaro-Black.ttf")
        f_dia_semana = ImageFont.truetype(path_extra, 110)
        
        # DESC:
        path_desc = ruta_abs("Canaro-SemiBold.ttf")
        
    except Exception as e:
        print(f"Error fuentes: {e}")
        f_invita = f_dia_box = f_mes_box = f_dia_semana = ImageFont.load_default()
        path_desc = None

    # --- 4. CABECERA ---
    
    # TÍTULO "INVITA"
    y_titulo = 850 
    titulo_texto = "INVITA" if not logos_colab else "INVITAN"
    dibujar_texto_sombra(draw, titulo_texto, W/2, y_titulo, f_invita, offset=(10,10))
    
    # DESCRIPCIÓN (Tamaños reducidos)
    y_desc = y_titulo + 180 
    chars_desc = len(desc1)
    
    if chars_desc <= 75:
        size_desc_val = 110 
    elif chars_desc <= 150:
        size_desc_val = 90 
    else:
        size_desc_val = 75
        
    if path_desc and os.path.exists(path_desc):
        f_desc = ImageFont.truetype(path_desc, size_desc_val)
    else:
        f_desc = ImageFont.load_default()
    
    width_wrap = 28 if size_desc_val >= 110 else (35 if size_desc_val >= 90 else 45)
    lines = textwrap.wrap(desc1, width=width_wrap)
    
    for line in lines:
        dibujar_texto_sombra(draw, line, W/2, y_desc, f_desc, offset=(8,8))
        y_desc += int(size_desc_val * 1.3)

    # --- 5. CAJA DE FECHA (CORREGIDA) ---
    h_caja = 645
    x_box = PADDING_SIDES 
    # Subimos la caja para dar espacio a la info de abajo
    y_box = H - h_caja - PADDING_BOTTOM - 150
    
    # Info Hora
    str_hora = hora1.strftime('%H:%M %p')
    if hora2: str_hora += f" a {hora2.strftime('%H:%M %p')}"
    
    size_hora = 110
    if hora2: size_hora = 90
        
    try: f_hora = ImageFont.truetype(path_extra, size_hora)
    except: f_hora = ImageFont.load_default()

    # DIBUJAR CAJA Y CONTENIDO
    if fecha2: # Larga
        if os.path.exists("flyer_caja_fecha_larga.png"):
            caja = Image.open("flyer_caja_fecha_larga.png").convert("RGBA")
            caja = resize_por_alto(caja, h_caja)
            img.paste(caja, (x_box, y_box), caja)
            w_caja = caja.width
            color_fecha = "white"
        else:
            w_caja = 1000
            draw.rectangle([x_box, y_box, x_box+w_caja, y_box+h_caja], fill="white")
            color_fecha = "black"

        cx = x_box + (w_caja / 2)
        cy = y_box + (h_caja / 2)
        
        txt_nums = f"{fecha1.day} - {fecha2.day}"
        txt_mes = obtener_mes_nombre(fecha1.month) if fecha1.month == fecha2.month else f"{obtener_mes_nombre(fecha1.month)} - {obtener_mes_nombre(fecha2.month)}"
        
        # MES ARRIBA, NÚMERO ABAJO
        f_mes_uso = f_mes_box
        if len(txt_mes) > 15: 
            try: f_mes_uso = ImageFont.truetype(ruta_abs("Canaro-Black.ttf"), 120)
            except: pass

        draw.text((cx, cy - 100), txt_mes, font=f_mes_uso, fill=color_fecha, anchor="mm")
        draw.text((cx, cy + 100), txt_nums, font=f_dia_box, fill=color_fecha, anchor="mm")
        
        # INFO INFERIOR
        y_info_dia = y_box + h_caja + 50
        dibujar_texto_sombra(draw, str_hora, cx, y_info_dia, f_hora, offset=(8,8))
            
    else: # Corta (1 fecha)
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
        
        # MES ARRIBA, NÚMERO ABAJO
        draw.text((cx, cy - 100), mes_txt, font=f_mes_box, fill=color_fecha, anchor="mm")
        draw.text((cx, cy + 100), dia_num, font=f_dia_box, fill=color_fecha, anchor="mm")
        
        dia_sem = obtener_dia_semana(fecha1)
        
        # INFO INFERIOR
        y_info_dia = y_box + h_caja + 50
        dibujar_texto_sombra(draw, dia_sem, cx, y_info_dia, f_dia_semana, offset=(8,8))
        dibujar_texto_sombra(draw, str_hora, cx, y_info_dia + 110, f_hora, offset=(8,8))

    # --- 6. UBICACIÓN (CORREGIDA: ICONO AL LADO, MÁRGENES) ---
    
    len_lug = len(lugar)
    if len_lug < 45: s_lug = 100
    else: s_lug = 80
        
    try: f_lugar = ImageFont.truetype(ruta_abs("Canaro-Medium.ttf"), s_lug)
    except: f_lugar = ImageFont.load_default()

    wrap_width = 18 if s_lug == 100 else 22
    lines_loc = textwrap.wrap(lugar, width=wrap_width)
    
    line_height = int(s_lug * 1.1)
    total_text_height = len(lines_loc) * line_height
    
    # Posición base Y (respetando padding inferior)
    # El texto se dibuja desde abajo hacia arriba, la base es H - PADDING_BOTTOM
    y_base_txt = H - PADDING_BOTTOM
    
    # Coordenada X del texto (alineado a la derecha, respetando padding lateral)
    x_txt_anchor = W - PADDING_SIDES

    # Cargar Icono
    h_icon = 260
    if os.path.exists("flyer_icono_lugar.png"):
        icon = Image.open("flyer_icono_lugar.png").convert("RGBA")
        icon = resize_por_alto(icon, h_icon)
        w_icon = icon.width
    else:
        icon = None
        w_icon = 100

    # Calcular centro vertical del bloque de texto
    y_text_center = y_base_txt - (total_text_height / 2)
    
    # Posición Y del icono (centrado con el texto)
    y_icon = y_text_center - (h_icon / 2)
    
    # Posición X del icono (a la izquierda del texto con un margen)
    # Estimamos el ancho del texto para colocar el icono a su izquierda
    try:
        # Usamos la línea más larga para estimar el ancho del bloque
        max_line_width = max([f_lugar.getlength(line) for line in lines_loc])
    except:
        max_line_width = 400 # Valor por defecto si falla getlength

    x_icon = x_txt_anchor - max_line_width - w_icon - 40 # 40px de separación
    
    # Dibujar Icono
    if icon:
        img.paste(icon, (int(x_icon), int(y_icon)), icon)
    else:
        dibujar_texto_sombra(draw, "📍", x_icon + w_icon/2, y_icon + h_icon/2, f_lugar, anchor="mm")

    # Dibujar Texto (línea por línea hacia arriba desde la base)
    current_y_txt = y_base_txt - ((len(lines_loc)-1) * line_height)
    for l in lines_loc:
        dibujar_texto_sombra(draw, l, x_txt_anchor, current_y_txt, f_lugar, anchor="rm", offset=(5,5))
        current_y_txt += line_height

    # --- 7. LOGOS SUPERIORES (CAPA FINAL) ---
    y_logos = 150
    margin_logos = 200 
    
    # LOGO PREFECTURA
    if os.path.exists("flyer_logo.png"):
        logo = Image.open("flyer_logo.png").convert("RGBA")
        target_h_logo = 378
        if abs(logo.height - target_h_logo) > 10:
             logo = resize_por_alto(logo, target_h_logo)

        for _ in range(2): 
            img.paste(logo, (margin_logos, y_logos), logo)
    
    # LOGO JOTA
    if os.path.exists("flyer_firma.png"):
        firma = Image.open("flyer_firma.png").convert("RGBA")
        firma = resize_por_alto(firma, 378)
        img.paste(firma, (W - firma.width - margin_logos, y_logos + 20), firma)

    # --- 8. APLANAR A RGB ---
    img_final = img.convert("RGB")
    
    return img_final

def generar_flyer_automatico(datos):
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
            img_orig = Image.open(archivo_subido)
            st.info("Ajusta el recorte. Recuerda usar imágenes de buena calidad.")
            img_crop = st_cropper(
                img_orig, 
                realtime_update=True, 
                box_color='#FF0000', 
                aspect_ratio=(4, 5),
                should_resize_image=False 
            )
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
