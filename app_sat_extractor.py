import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Extractor SAT XML",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS modernos y minimalistas
st.markdown("""
    <style>
    /* Fuentes y colores principales */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .main {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem 3rem;
    }

    /* Header */
    .header-container {
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid #e5e7eb;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .subtitle {
        font-size: 1rem;
        color: #6b7280;
        font-weight: 400;
    }

    /* File uploader personalizado */
    .uploadedFile {
        border: 2px dashed #d1d5db !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        background: #f9fafb !important;
        transition: all 0.3s ease;
    }

    .uploadedFile:hover {
        border-color: #667eea !important;
        background: #f3f4f6 !important;
    }

    /* Botones */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 0.95rem;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .stButton > button[kind="secondary"] {
        background: white;
        color: #374151;
        border: 1.5px solid #e5e7eb;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #f9fafb;
        border-color: #d1d5db;
    }

    /* Mensajes de estado */
    .status-success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }

    .status-info {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .status-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }

    .status-error {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }

    /* Tablas */
    .dataframe {
        font-size: 0.9rem !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        transition: all 0.2s ease !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }

    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">Extractor SAT XML</h1>
        <p class="subtitle">Convierte tus facturas XML a Excel con desglose de impuestos</p>
    </div>
""", unsafe_allow_html=True)

# Namespaces
NS = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'cfdi3': 'http://www.sat.gob.mx/cfd/3',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
}

def parse_xml_invoice_one_row(xml_text):
    """Parsea un XML y devuelve UNA fila por factura con totales agregados"""
    try:
        root = ET.fromstring(xml_text)

        # Datos principales del comprobante
        fecha = root.get('Fecha', '')
        total = float(root.get('Total', '0') or 0)
        subtotal = float(root.get('SubTotal', '0') or 0)
        moneda = root.get('Moneda', 'MXN')
        tipo_comprobante = root.get('TipoDeComprobante', '')

        # UUID
        timbre = root.find('.//tfd:TimbreFiscalDigital', NS)
        uuid = timbre.get('UUID', '') if timbre is not None else ''

        # Emisor
        emisor = (root.find('cfdi:Emisor', NS) 
                  or root.find('cfdi3:Emisor', NS) 
                  or root.find('Emisor'))
        emisor_rfc = emisor.get('Rfc', '') if emisor is not None else ''
        emisor_nombre = emisor.get('Nombre', '') if emisor is not None else ''

        # Conceptos
        conceptos = (root.findall('cfdi:Conceptos/cfdi:Concepto', NS)
                     or root.findall('cfdi3:Conceptos/cfdi3:Concepto', NS)
                     or root.findall('.//Concepto'))

        # Variables para acumular
        total_cantidad = 0.0
        total_importe = 0.0
        iva_traslado = 0.0
        isr_retenido = 0.0
        iva_retenido = 0.0
        ieps = 0.0
        descripciones = []

        for concepto in conceptos:
            cantidad = float(concepto.get('Cantidad', '0') or 0)

            # Valor unitario (CFDI 4.0) o precio unitario (CFDI 3.3)
            precio_unitario = concepto.get('ValorUnitario', '')
            if not precio_unitario:
                precio_unitario = concepto.get('PrecioUnitario', '0')

            importe = float(concepto.get('Importe', '0') or 0)
            desc = concepto.get('Descripcion', '')

            if desc:
                descripciones.append(desc)

            total_cantidad += cantidad
            total_importe += importe

            # Extraer impuestos del concepto
            impuestos_concepto = (concepto.find('cfdi:Impuestos', NS)
                                  or concepto.find('cfdi3:Impuestos', NS)
                                  or concepto.find('Impuestos'))

            if impuestos_concepto is not None:
                # Traslados (IVA, IEPS)
                traslados = (impuestos_concepto.findall('cfdi:Traslados/cfdi:Traslado', NS)
                             or impuestos_concepto.findall('cfdi3:Traslados/cfdi3:Traslado', NS)
                             or impuestos_concepto.findall('.//Traslado'))

                for traslado in traslados:
                    impuesto_tipo = traslado.get('Impuesto', '')
                    importe_imp = float(traslado.get('Importe', '0') or 0)

                    if impuesto_tipo == '002':  # IVA
                        iva_traslado += importe_imp
                    elif impuesto_tipo == '003':  # IEPS
                        ieps += importe_imp

                # Retenciones (ISR, IVA)
                retenciones = (impuestos_concepto.findall('cfdi:Retenciones/cfdi:Retencion', NS)
                               or impuestos_concepto.findall('cfdi3:Retenciones/cfdi3:Retencion', NS)
                               or impuestos_concepto.findall('.//Retencion'))

                for retencion in retenciones:
                    impuesto_tipo = retencion.get('Impuesto', '')
                    importe_imp = float(retencion.get('Importe', '0') or 0)

                    if impuesto_tipo == '001':  # ISR
                        isr_retenido += importe_imp
                    elif impuesto_tipo == '002':  # IVA
                        iva_retenido += importe_imp

        # Concatenar descripciones
        descripcion_resumen = ' | '.join(descripciones) if descripciones else ''

        return {
            'UUID': uuid,
            'Fecha': fecha,
            'Tipo': tipo_comprobante,
            'RFC Emisor': emisor_rfc,
            'Emisor': emisor_nombre,
            'Descripcion': descripcion_resumen,
            'Cantidad': total_cantidad,
            'Importe': round(total_importe, 2),
            'IVA': round(iva_traslado, 2),
            'ISR Retenido': round(isr_retenido, 2),
            'IVA Retenido': round(iva_retenido, 2),
            'IEPS': round(ieps, 2),
            'Subtotal': subtotal,
            'Total': total,
            'Moneda': moneda
        }

    except ET.ParseError as e:
        st.error(f"Error al parsear XML: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def process_files(uploaded_files):
    """Procesa múltiples archivos XML - una fila por factura"""
    all_invoices = []
    errors = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            xml_content = uploaded_file.read().decode('utf-8', errors='ignore')
            invoice = parse_xml_invoice_one_row(xml_content)

            if invoice:
                all_invoices.append(invoice)
                status_text.text(f"Procesado: {uploaded_file.name}")
            else:
                errors.append(f"{uploaded_file.name}: No se pudo extraer información")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        except Exception as e:
            errors.append(f"{uploaded_file.name}: {str(e)}")

    progress_bar.empty()
    status_text.empty()

    return pd.DataFrame(all_invoices) if all_invoices else None, errors

# Interfaz principal
uploaded_files = st.file_uploader(
    "Seleccionar archivos XML",
    type=['xml'],
    accept_multiple_files=True,
    help="Arrastra o selecciona múltiples archivos XML"
)

if uploaded_files:
    st.markdown(f'<div class="status-info">{len(uploaded_files)} archivo(s) seleccionado(s)</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        process_btn = st.button('Procesar y Descargar', type="primary", use_container_width=True)

    with col2:
        preview_btn = st.button('Vista Previa', type="secondary", use_container_width=True)

    if process_btn:
        with st.spinner('Procesando archivos...'):
            df, errors = process_files(uploaded_files)

        if df is not None and len(df) > 0:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Facturas', index=False)

                worksheet = writer.sheets['Facturas']
                column_widths = {
                    'UUID': 40,
                    'Fecha': 20,
                    'Tipo': 8,
                    'RFC Emisor': 15,
                    'Emisor': 30,
                    'Descripcion': 60,
                    'Cantidad': 12,
                    'Importe': 12,
                    'IVA': 12,
                    'ISR Retenido': 15,
                    'IVA Retenido': 15,
                    'IEPS': 12,
                    'Subtotal': 12,
                    'Total': 12,
                    'Moneda': 10
                }

                for idx, col in enumerate(df.columns):
                    width = column_widths.get(col, 20)
                    col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                    worksheet.column_dimensions[col_letter].width = width

            output.seek(0)

            st.markdown(f'<div class="status-success">{len(df)} factura(s) procesada(s)</div>', unsafe_allow_html=True)

            st.download_button(
                label="Descargar Excel",
                data=output.getvalue(),
                file_name=f"Facturas_SAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            if errors:
                st.markdown(f'<div class="status-warning">Advertencias: {len(errors)} archivo(s) con problemas</div>', unsafe_allow_html=True)
                with st.expander("Ver detalles"):
                    for error in errors:
                        st.text(error)
        else:
            st.markdown('<div class="status-error">No se encontraron facturas válidas</div>', unsafe_allow_html=True)
            if errors:
                for error in errors:
                    st.error(error)

    if preview_btn:
        df, errors = process_files(uploaded_files)

        if df is not None and len(df) > 0:
            st.markdown("### Vista Previa")
            st.dataframe(df.head(10), use_container_width=True, height=400)
            st.caption(f"Mostrando primeros 10 de {len(df)} facturas")

            if errors:
                with st.expander("Advertencias"):
                    for error in errors:
                        st.text(error)
        else:
            st.markdown('<div class="status-error">Error al procesar archivos</div>', unsafe_allow_html=True)