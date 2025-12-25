import streamlit as st
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import textwrap
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PDF Fusion Lab", page_icon="🧪", layout="centered")

# --- LÓGICA AUXILIAR (ADAPTADA PARA MEMORIA) ---
def crear_separador(titulo):
    packet = io.BytesIO()
    try:
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFillColor(colors.black)
        can.setFont("Courier-Bold", 18)
        lineas = textwrap.wrap(titulo, width=45)
        y_inicio = A4[1]/2 + ((len(lineas)/2)*25)
        for i, linea in enumerate(lineas):
            can.drawCentredString(A4[0]/2, y_inicio - (i*25), linea.upper())
        can.setLineWidth(0.5)
        can.line(150, y_inicio - (len(lineas)*25) - 10, A4[0]-150, y_inicio - (len(lineas)*25) - 10)
        can.save()
        packet.seek(0)
        return packet
    except: return None

def crear_paginas_indice(entradas):
    paginas_pdf = []
    try:
        total_pags = math.ceil(len(entradas) / 30)
        for p in range(total_pags):
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            can.setFillColor(colors.black)
            can.setFont("Courier-Bold", 16)
            can.drawString(70, A4[1]-60, f"ÍNDICE DE CONTENIDOS (Pág. {p+1}/{total_pags})")
            can.setFont("Courier", 11)
            y = A4[1]-100
            for nombre, pag in entradas[p*30 : (p+1)*30]:
                nombre_c = (nombre[:60] + '..') if len(nombre) > 60 else nombre
                can.drawString(70, y, nombre_c)
                can.drawRightString(A4[0]-70, y, str(pag))
                y -= 20
            can.save()
            packet.seek(0)
            paginas_pdf.append(packet)
        return paginas_pdf
    except: return []

# --- INTERFAZ WEB ---
st.title("PDFlab")
st.markdown("### Tu laboratorio online para unir documentos")

# Barra lateral de opciones
with st.sidebar:
    st.header("⚙️ Configuración")
    check_indice = st.checkbox("Incluir Índice", value=False)
    check_separadores = st.checkbox("Páginas Separadoras", value=False)
    check_numeracion = st.checkbox("Numerar Capítulos", value=False)
    check_compresion = st.checkbox("Compresión (Lento)", value=False)
    
    st.info("**Nota:** La compresión puede tardar unos segundos extra.")

# Zona de Drag & Drop
uploaded_files = st.file_uploader("Arrastra tus archivos PDF aquí (el orden importa)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"V {len(uploaded_files)} archivos cargados.")
    
    # Botón principal
    if st.button("🚀 FUSIONAR DOCUMENTOS AHORA", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            writer = PdfWriter()
            entries = []
            
            # Cálculo de páginas inicial (aprox)
            curr_p = (math.ceil(len(uploaded_files) / 30) if check_indice else 0) + 1
            
            # 1. Primera pasada: Lectura
            for i, upload_file in enumerate(uploaded_files):
                reader = PdfReader(upload_file)
                base_name = upload_file.name
                display_name = f"{i+1:02d}. {base_name}" if check_numeracion else base_name
                entries.append((upload_file, curr_p, display_name))
                curr_p += (1 if check_separadores else 0) + len(reader.pages)
            
            # 2. Generar Índice
            if check_indice:
                status_text.text("Generando índice...")
                data_idx = [(item[2], item[1]) for item in entries]
                for p_s in crear_paginas_indice(data_idx):
                    writer.append(PdfReader(p_s))
            
            # 3. Procesar Archivos
            total_steps = len(entries)
            for i, (upload_file, p_start, display_name) in enumerate(entries):
                status_text.text(f"Procesando: {display_name}")
                
                # Reiniciamos el puntero del archivo para leerlo de nuevo
                upload_file.seek(0)
                reader = PdfReader(upload_file)
                
                if check_separadores:
                    sep = crear_separador(display_name)
                    if sep: writer.append(PdfReader(sep))
                
                writer.add_outline_item(display_name, p_start - 1)
                writer.append(reader)
                
                progress_bar.progress((i + 1) / total_steps)

            # 4. Compresión
            if check_compresion:
                status_text.text("Optimizando y comprimiendo... (esto lleva un poco)")
                writer.compress_identical_objects(remove_identicals=True)
                for page in writer.pages:
                    page.compress_content_streams()

            # 5. Guardar en memoria RAM
            output_pdf = io.BytesIO()
            writer.write(output_pdf)
            output_pdf.seek(0)
            
            status_text.text("V ¡Listo!")
            progress_bar.progress(100)
            
            # BOTÓN DE DESCARGA
            st.balloons()
            st.download_button(
                label="📥 DESCARGAR PDF FUSIONADO",
                data=output_pdf,
                file_name="fusion_completa.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")