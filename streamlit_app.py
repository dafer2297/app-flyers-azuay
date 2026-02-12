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
    # Fondo General de la App
    bg_style = "background-color: #1E88E5;" 
    if os.path.exists("fondo_app.png"):
        bin_str = get_base64_of_bin_file("fondo_app.png")
        bg_style = f"""
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """

    # Carga de Fuentes CSS (Para que la web se vea bonita)
    font_css = ""
    # Intentamos cargar la Black para títulos de la app
    if os.path.exists("Canaro-Black.ttf"):
        font_b64 = get_base64_of_bin_file("Canaro-Black.ttf")
        font_css += f"""@font-face {{ font-family: 'Canaro'; src: url('data:font/ttf;base64,{font_b64}') format('truetype'); }}"""

    st.markdown(
        f"""
        <style>
        .stApp {{ {bg_style} }}
        {font_css}
        
        /* Tipografías Web */
        h1, h2, h3 {{ font-family: 'Canaro', sans-serif !important; color: white !important; text-transform: uppercase; }}
        
        /* Botones */
        .stButton > button {{ background-color: transparent; color: white; border: 2px solid white; border-radius: 15px; padding: 10px 20px; font-weight: bold; }}
        .stButton > button:hover {{ background-color: #D81B60; border-color: #D81B60; }}
        
        /* Inputs */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, 
        .stDateInput > div > div > input, .stTimeInput > div > div > input {{
            background-color: white !important; color: black !important; border-radius: 8px; border: none;
        }}
        .stTextInput label, .stTextArea label, .stDateInput label, .stTimeInput label {{ display: none; }}

        /* Etiquetas */
        .label-negro {{ font-family: 'Canaro', sans-serif; font-weight: bold; font-size: 16px; color: black !important; margin-bottom: 2px; margin-top: 10px; text-shadow: none !important; }}
        .label-blanco {{ font-family: 'Canaro', sans-serif; font-weight: normal; font-size: 12px; color: white !important; margin-left: 5px; }}
        
        /* Contador de Caracteres */
        .contador-ok {{ color: #C6FF00 !important; font-weight: bold; font-size: 14px; }}
        .contador-mal {{ color: #FF5252 !important; font-weight: bold; font-size: 14px; }}

        #MainMenu, footer, header {{visibility: hidden;}}
        </style>
        """, unsafe_allow_html=True
    )

set_design()

# ==============================================================================
# 2. MOTOR GRÁFICO
# ==============================================================================

# Función auxiliar para dibujar texto con sombra
def dibujar_texto_sombra(draw, texto, x, y, fuente, color="white", sombra="black", offset=(5,5), anchor="mm"):
    draw.text((x+offset[0], y+offset[1]), texto, font=fuente, fill=sombra, anchor=anchor)
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)

# --- CARGADOR DE FUENTES PYTHON (PIL) ---
def cargar_fuentes():
    fuentes = {}
    try:
        # Tamaños base, luego se pueden escalar o pedir tamaño específico
        # Ajusta los nombres de archivo si los tienes diferentes (ej: Canaro-Medium.otf vs .ttf)
        fuentes['Medium'] = ImageFont.truetype("Canaro-Medium.ttf", 100)
        fuentes['SemiBold'] = ImageFont.truetype("Canaro-SemiBold.ttf", 100)
        fuentes['Bold'] = ImageFont.truetype("Canaro-Bold.ttf", 100)
        fuentes['ExtraBold'] = ImageFont.truetype("Canaro-ExtraBold.ttf", 100)
        fuentes['Black'] = ImageFont.truetype("Canaro-Black.ttf", 100)
    except:
        # Fallback por si faltan archivos
        def_font = ImageFont.load_default()
        fuentes = {k: def_font for k in ['Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black']}
    return fuentes

# --- PLANTILLA TIPO 1 (BASE) ---
def generar_tipo_1(datos):
    # Desempaquetar datos
    fondo = datos['fondo']
    desc1 = datos['desc1']
    fecha1 = datos['fecha1']
    hora1 = datos['hora1']
    lugar = datos['lugar']
    logos_colab = datos['logos']
    
    # 1. Lienzo Base
    W, H = 2400, 3000
    img = fondo.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 2. Sombra PNG (Asset externo)
    if os.path.exists("sombra.png"):
        sombra_img = Image.open("sombra.png").convert("RGBA")
        sombra_img = sombra_img.resize((W, H), Image.Resampling.LANCZOS)
        img.paste(sombra_img, (0, 0), sombra_img)
    else:
        # Fallback si no suben la sombra.png (Sombra manual)
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d_over = ImageDraw.Draw(overlay)
        for y in range(int(H*0.4), H):
            alpha = int(255 * ((y - H*0.4)/(H*0.6)))
            d_over.line([(0,y), (W,y)], fill=(0,0,0, int(alpha*0.8)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img) # Reiniciar draw

    # 3. Cargar Fuentes (Tamaños específicos para esta plantilla)
    try:
        f_invita = ImageFont.truetype("Canaro-Bold.ttf", 180) # Título siempre Bold
        f_desc = ImageFont.truetype("Canaro-Medium.ttf", 110)
        f_dato = ImageFont.truetype("Canaro-SemiBold.ttf", 90)
    except:
        f_invita = f_desc = f_dato = ImageFont.load_default()

    # --- ELEMENTOS VISUALES ---

    # A. Logo Prefectura (Arriba Centro)
    y_cursor = 150 # Posición vertical inicial
    if os.path.exists("logo_superior.png"):
        logo = Image.open("logo_superior.png").convert("RGBA")
        ratio = 1000 / logo.width
        h_logo = int(logo.height * ratio)
        logo = logo.resize((1000, h_logo), Image.Resampling.LANCZOS)
        img.paste(logo, (int((W-1000)/2), y_cursor), logo)
        y_cursor += h_logo + 50 # Bajamos el cursor

    # B. Logos Colaboradores (Si existen)
    titulo_texto = "INVITA"
    if logos_colab:
        titulo_texto = "INVITAN" # Cambia el título
        # Lógica básica para poner logos colaboradores aquí (la definiremos mejor viendo tu diseño)
        # Por ahora solo reserva espacio
        y_cursor += 150 
    
    # C. Título (INVITA / INVITAN) - Canaro Bold
    # Se coloca DEBAJO de los logos
    w_tit = draw.textlength(titulo_texto, font=f_invita)
    draw.text(((W - w_tit)/2, y_cursor), titulo_texto, font=f_invita, fill="white")
    
    # D. Descripción
    # Usamos posición fija provisional hasta ver tu diseño
    y_txt = 1400 
    if desc1:
        lines = textwrap.wrap(desc1, width=30)
        for line in lines:
            dibujar_texto_sombra(draw, line, W/2, y_txt, f_desc)
            y_txt += 130
        
    # E. Fecha y Hora
    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    txt_fecha = f"{fecha1.day} de {meses[fecha1.month]}   |   {hora1.strftime('%H:%M')}"
    
    y_info = y_txt + 200
    # Icono calendario/reloj se puede agregar aquí
    dibujar_texto_sombra(draw, txt_fecha, W/2, y_info, f_dato)
    
    # F. Lugar + Icono
    y_lugar = y_info + 200
    if os.path.exists("icono_lugar.png"):
        icon_lug = Image.open("icono_lugar.png").convert("RGBA")
        icon_lug = icon_lug.resize((80, 80), Image.Resampling.LANCZOS)
        # Calcular ancho total para centrar icono + texto
        w_lug_txt = draw.textlength(lugar, font=f_dato)
        w_total = 80 + 20 + w_lug_txt # Icono + espacio + texto
        start_x = (W - w_total) / 2
        
        img.paste(icon_lug, (int(start_x), int(y_lugar - 40)), icon_lug)
        dibujar_texto_sombra(draw, lugar, start_x + 100, y_lugar, f_dato, anchor="lm") # Anchor left-middle
    else:
        dibujar_texto_sombra(draw, f"📍 {lugar}", W/2, y_lugar, f_dato)

    # G. Firma Jota (Abajo Izquierda)
    if os.path.exists("firma_jota.png"):
        firma = Image.open("firma_jota.png").convert("RGBA")
        ratio = 600 / firma.width
        firma = firma.resize((600, int(firma.height * ratio)), Image.Resampling.LANCZOS)
        img.paste(firma, (100, H - firma.height - 100), firma)

    return img

# --- RESTO DE PLANTILLAS (POR IMPLEMENTAR DETALLES VISUALES) ---
def generar_tipo_2(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_3(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_4(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_5(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_6(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_7(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_8(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_9(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_10(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_11(datos): return generar_tipo_1(datos) # Placeholder
def generar_tipo_12(datos): return generar_tipo_1(datos) # Placeholder


# ==============================================================================
# 3. CONTROLADOR MAESTRO
# ==============================================================================
def generar_flyer_automatico(datos):
    """ Elige la plantilla correcta (1 al 12) según los datos """
    tiene_desc2 = bool(datos['desc2'])
    tiene_fecha2 = bool(datos['fecha2'])
    num_colabs = len(datos['logos']) if datos['logos'] else 0
    
    # ÁRBOL DE DECISIÓN
    if num_colabs == 0:
        if not tiene_desc2 and not tiene_fecha2: return generar_tipo_1(datos)
        elif tiene_desc2 and not tiene_fecha2: return generar_tipo_2(datos)
        elif not tiene_desc2 and tiene_fecha2: return generar_tipo_3(datos)
        elif tiene_desc2 and tiene_fecha2: return generar_tipo_4(datos)

    elif num_colabs == 1:
        if not tiene_desc2 and not tiene_fecha2: return generar_tipo_5(datos)
        elif tiene_desc2 and not tiene_fecha2: return generar_tipo_6(datos)
        elif not tiene_desc2 and tiene_fecha2: return generar_tipo_7(datos)
        elif tiene_desc2 and tiene_fecha2: return generar_tipo_8(datos)

    elif num_colabs >= 2:
        if not tiene_desc2 and not tiene_fecha2: return generar_tipo_9(datos)
        elif tiene_desc2 and not tiene_fecha2: return generar_tipo_10(datos)
        elif not tiene_desc2 and tiene_fecha2: return generar_tipo_11(datos)
        elif tiene_desc2 and tiene_fecha2: return generar_tipo_12(datos)

    return datos['fondo'] # Fallback

# ==============================================================================
# 4. INTERFAZ DE USUARIO
# ==============================================================================

if os.path.exists("logo_superior.png"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image("logo_superior.png", use_container_width=True)

query_params = st.query_params
area_seleccionada = query_params.get("area", None)

# --- PÁGINA 1: INICIO ---
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

# --- PÁGINA 2: FORMULARIO ---
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
        # --- DESCRIPCIÓN 1 (NO OBLIGATORIA) ---
        st.markdown('<div class="label-negro">DESCRIPCIÓN</div>', unsafe_allow_html=True)
        desc1 = st.text_area("lbl_desc", key="lbl_desc", label_visibility="collapsed", placeholder="Escribe aquí...", height=150)
        
        # --- DESCRIPCIÓN 2 (OPCIONAL) ---
        st.markdown('<div class="label-negro">DESCRIPCIÓN 2 <span class="label-blanco">(OPCIONAL)</span></div>', unsafe_allow_html=True)
        desc2 = st.text_area("lbl_desc2", key="lbl_desc2", label_visibility="collapsed", placeholder="Información extra...", height=100)
        
        # --- VALIDACIÓN DE CARACTERES EN TIEMPO REAL ---
        total_chars = len(desc1) + len(desc2)
        if total_chars <= 150:
            st.markdown(f'<div class="contador-ok">Caracteres: {total_chars} / 150 ✅</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="contador-mal">Caracteres: {total_chars} / 150 ❌ (Te pasaste por {total_chars - 150})</div>', unsafe_allow_html=True)

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
        st.text_input("lbl_dir", key="lbl_dir", label_visibility="collapsed", placeholder="Ubicación del evento")
        
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
        
        # --- BOTÓN GENERAR CON VALIDACIONES ACTUALIZADAS ---
        if st.button("✨ GENERAR FLYER ✨", type="primary", use_container_width=True):
            errores = []
            
            # Validación 1: Caracteres máximos 150 (Suma de las dos)
            if (len(st.session_state.lbl_desc) + len(st.session_state.lbl_desc2)) > 150:
                errores.append("Texto demasiado largo (Máx 150 caracteres entre ambas descripciones)")
            
            # Validación 2: Fecha Obligatoria
            if not st.session_state.lbl_fecha1: 
                errores.append("Falta la Fecha de Inicio")
            
            # Validación 3: Imagen Obligatoria
            if 'imagen_lista_para_flyer' not in st.session_state: 
                errores.append("Falta recortar la Imagen de Fondo")
                
            if errores:
                st.error(f"⚠️ {', '.join(errores)}")
            else:
                st.query_params["area"] = "Final"
                st.rerun()

# --- PÁGINA 3: RESULTADO ---
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
        if 'imagen_lista_para_flyer' in st.session_state:
            
            # Empaquetamos todo en un diccionario para pasarlo al Generador
            paquete = {
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
            
            # ¡GENERAR!
            flyer_final = generar_flyer_automatico(paquete)
            
            st.image(flyer_final, caption="Diseño Generado", use_container_width=True)
            
            buf = io.BytesIO()
            flyer_final.save(buf, format="PNG")
            byte_im = buf.getvalue()
        else:
            st.error("Datos perdidos. Vuelve al inicio.")

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
        if 'imagen_lista_para_flyer' in st.session_state: del st.session_state['imagen_lista_para_flyer']
        st.rerun()
