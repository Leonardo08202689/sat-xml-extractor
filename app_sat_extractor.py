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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .main {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem 3rem;
    }

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

    .dataframe {
        font-size: 0.9rem !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }

    .stSpinner > div {
        border-top-color: #667eea !important;
    }

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

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="header-container">
        <h1 class="main-title">Extractor SAT XML</h1>
        <p class="subtitle">Convierte tus facturas y pagos XML a Excel con desglose de impuestos</p>
    </div>
""", unsafe_allow_html=True)

NS = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'cfdi3': 'http://www.sat.gob.mx/cfd/3',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20'
}

# ============= PARSERS PARA FACTURAS (RECIBIDAS) =============

def parse_xml_invoice_one_row(xml_text):
    """Parsea un XML de factura y devuelve UNA fila por factura"""
    try:
        root = ET.fromstring(xml_text)

        fecha = root.get('Fecha', '')
        total = float(root.get('Total', '0') or 0)
        subtotal = float(root.get('SubTotal', '0') or 0)
        moneda = root.get('Moneda', 'MXN')
        tipo_comprobante = root.get('TipoDeComprobante', '')

        timbre = root.find('.//tfd:TimbreFiscalDigital', NS)
        uuid = timbre.get('UUID', '') if timbre is not None else ''

        # Emisor
        emisor = root.find('cfdi:Emisor', NS)
        if emisor is None:
            emisor = root.find('cfdi3:Emisor', NS)
        if emisor is None:
            emisor = root.find('Emisor')

        emisor_rfc = ''
        emisor_nombre = ''
        if emisor is not None:
            emisor_rfc = emisor.get('Rfc', '')
            emisor_nombre = emisor.get('Nombre', '')

        # Conceptos
        conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', NS)
        if not conceptos:
            conceptos = root.findall('cfdi3:Conceptos/cfdi3:Concepto', NS)
        if not conceptos:
            conceptos = root.findall('.//Concepto')

        total_cantidad = 0.0
        total_importe = 0.0
        iva_traslado = 0.0
        isr_retenido = 0.0
        iva_retenido = 0.0
        ieps = 0.0
        descripciones = []

        for concepto in conceptos:
            cantidad = float(concepto.get('Cantidad', '0') or 0)
            importe = float(concepto.get('Importe', '0') or 0)
            desc = concepto.get('Descripcion', '')

            if desc:
                descripciones.append(desc)

            total_cantidad += cantidad
            total_importe += importe

            impuestos_concepto = concepto.find('cfdi:Impuestos', NS)
            if impuestos_concepto is None:
                impuestos_concepto = concepto.find('cfdi3:Impuestos', NS)
            if impuestos_concepto is None:
                impuestos_concepto = concepto.find('Impuestos')

            if impuestos_concepto is not None:
                traslados = impuestos_concepto.findall('cfdi:Traslados/cfdi:Traslado', NS)
                if not traslados:
                    traslados = impuestos_concepto.findall('cfdi3:Traslados/cfdi3:Traslado', NS)
                if not traslados:
                    traslados = impuestos_concepto.findall('.//Traslado')

                for traslado in traslados:
                    impuesto_tipo = traslado.get('Impuesto', '')
                    importe_imp = float(traslado.get('Importe', '0') or 0)

                    if impuesto_tipo == '002':
                        iva_traslado += importe_imp
                    elif impuesto_tipo == '003':
                        ieps += importe_imp

                retenciones = impuestos_concepto.findall('cfdi:Retenciones/cfdi:Retencion', NS)
                if not retenciones:
                    retenciones = impuestos_concepto.findall('cfdi3:Retenciones/cfdi3:Retencion', NS)
                if not retenciones:
                    retenciones = impuestos_concepto.findall('.//Retencion')

                for retencion in retenciones:
                    impuesto_tipo = retencion.get('Impuesto', '')
                    importe_imp = float(retencion.get('Importe', '0') or 0)

                    if impuesto_tipo == '001':
                        isr_retenido += importe_imp
                    elif impuesto_tipo == '002':
                        iva_retenido += importe_imp

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

    except Exception:
        return None

# ============= PARSER PARA PAGOS =============

def parse_xml_payment(xml_text):
    """Parsea un XML de pago (Comprobante de Pago con complemento pago20)"""
    try:
        root = ET.fromstring(xml_text)

        # Datos principales del comprobante
        fecha_comprobante = root.get('Fecha', '')
        folio_comprobante = root.get('Folio', '')

        # Receptor
        receptor = root.find('cfdi:Receptor', NS)
        if receptor is None:
            receptor = root.find('Receptor')

        receptor_rfc = ''
        receptor_nombre = ''
        if receptor is not None:
            receptor_rfc = receptor.get('Rfc', '')
            receptor_nombre = receptor.get('Nombre', '')

        # Buscar el complemento de pagos
        pagos = root.find('.//pago20:Pagos', NS)
        if pagos is None:
            pagos = root.find('.//Pagos')

        rows = []

        if pagos is not None:
            # Iterar sobre cada pago (Pago)
            pago_list = pagos.findall('pago20:Pago', NS)
            if not pago_list:
                pago_list = pagos.findall('.//Pago')

            for pago in pago_list:
                fecha_pago = pago.get('FechaPago', '')
                monto_pago = float(pago.get('Monto', '0') or 0)

                # Buscar documentos relacionados dentro de este pago
                doc_relacionados = pago.findall('pago20:DoctoRelacionado', NS)
                if not doc_relacionados:
                    doc_relacionados = pago.findall('.//DoctoRelacionado')

                if doc_relacionados:
                    for docto in doc_relacionados:
                        folio_docto = docto.get('Folio', '')
                        # CORREGIDO: leer ImpPagado correctamente
                        monto_docto = float(
                            docto.get('ImpPagado', '0') or
                            docto.get('ImPagado', '0') or
                            docto.get('MontoPagado', '0') or
                            docto.get('MontoPagedo', '0') or
                            0
                        )

                        rows.append({
                            'Receptor': receptor_nombre,
                            'Fecha': fecha_comprobante,
                            'Mes': '',  # Se llena después
                            'RFC Receptor': receptor_rfc,
                            'Folio Pago': folio_comprobante,
                            'Folio Documento': folio_docto,
                            'Monto Pagado': round(monto_docto, 2)
                        })
                else:
                    # Si no hay documentos relacionados, crear una fila con el monto del pago
                    rows.append({
                        'Receptor': receptor_nombre,
                        'Fecha': fecha_comprobante,
                        'Mes': '',  # Se llena después
                        'RFC Receptor': receptor_rfc,
                        'Folio Pago': folio_comprobante,
                        'Folio Documento': '',
                        'Monto Pagado': round(monto_pago, 2)
                    })

        return rows

    except Exception:
        return []

# ============= PARSER PARA FACTURAS EMITIDAS ============= 

def parse_xml_emitted_invoice(xml_text):
    """Parsea un XML de factura emitida y devuelve UNA fila con la estructura deseada"""
    try:
        root = ET.fromstring(xml_text)

        # Datos generales
        fecha = root.get('Fecha', '')
        subtotal = float(root.get('SubTotal', '0') or 0)
        total = float(root.get('Total', '0') or 0)
        descuento = float(root.get('Descuento', '0') or 0)
        folio = root.get('Folio', '')
        serie = root.get('Serie', '')
        no_factura = f"{serie}{folio}" if serie else folio

        # Receptor (cliente)
        receptor = root.find('cfdi:Receptor', NS)
        if receptor is None:
            receptor = root.find('cfdi3:Receptor', NS)
        if receptor is None:
            receptor = root.find('Receptor')

        cliente_nombre = receptor.get('Nombre', '') if receptor is not None else ''
        cliente_rfc = receptor.get('Rfc', '') if receptor is not None else ''

        # Impuestos a nivel comprobante
        iva_trasladado = 0.0
        iva_retenido = 0.0

        impuestos = root.find('cfdi:Impuestos', NS)
        if impuestos is None:
            impuestos = root.find('cfdi3:Impuestos', NS)
        if impuestos is None:
            impuestos = root.find('Impuestos')

        if impuestos is not None:
            # Traslados
            traslados = impuestos.findall('cfdi:Traslados/cfdi:Traslado', NS) or \
                        impuestos.findall('cfdi3:Traslados/cfdi3:Traslado', NS) or \
                        impuestos.findall('.//Traslado')
            for t in traslados:
                if t.get('Impuesto', '') == '002':
                    iva_trasladado += float(t.get('Importe', '0') or 0)

            # Retenciones
            retenciones = impuestos.findall('cfdi:Retenciones/cfdi:Retencion', NS) or \
                          impuestos.findall('cfdi3:Retenciones/cfdi3:Retencion', NS) or \
                          impuestos.findall('.//Retencion')
            for r in retenciones:
                if r.get('Impuesto', '') == '002':
                    iva_retenido += float(r.get('Importe', '0') or 0)

        # Estatus básico (luego puedes enriquecerlo)
        estatus = 'Emitida'

        # Formato fecha dd/mm/aa
        try:
            fecha_dt = pd.to_datetime(fecha, errors='coerce')
            fecha_fmt = fecha_dt.strftime('%d/%m/%y') if pd.notnull(fecha_dt) else fecha
        except Exception:
            fecha_fmt = fecha

        return {
            'FECHA DD/MM/AA': fecha_fmt,
            'CLIENTE': cliente_nombre,
            'RFC': cliente_rfc,
            'No FACTURA': no_factura,
            'ESTATUS': estatus,
            'Subtotal': round(subtotal, 2),
            'OTRO (DESCUENTO)': round(descuento, 2),
            'IVA': round(iva_trasladado, 2),
            'RET IVA': round(iva_retenido, 2),
            'TOTAL': round(total, 2),
        }
    except Exception:
        return None

# ============= PROCESADORES DE ARCHIVOS =============

def process_invoice_files(uploaded_files):
    """Procesa múltiples archivos XML de facturas"""
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

    if all_invoices:
        df = pd.DataFrame(all_invoices)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.sort_values('Fecha').reset_index(drop=True)
        df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return df, errors

    return None, errors

def process_payment_files(uploaded_files):
    """Procesa múltiples archivos XML de pagos"""
    all_payments = []
    errors = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            xml_content = uploaded_file.read().decode('utf-8', errors='ignore')
            payments = parse_xml_payment(xml_content)

            if payments:
                all_payments.extend(payments)
                status_text.text(f"Procesado: {uploaded_file.name} ({len(payments)} pago(s))")
            else:
                errors.append(f"{uploaded_file.name}: No se encontraron pagos")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        except Exception as e:
            errors.append(f"{uploaded_file.name}: {str(e)}")

    progress_bar.empty()
    status_text.empty()

    if all_payments:
        df = pd.DataFrame(all_payments)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.sort_values('Fecha').reset_index(drop=True)

        # Agregar mes según la fecha
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        df['Mes'] = df['Fecha'].dt.month.map(meses)

        # Convertir fecha a string
        df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Reordenar columnas: Receptor, Fecha, Mes, RFC Receptor, ...
        columnas_ordenadas = ['Receptor', 'Fecha', 'Mes', 'RFC Receptor', 'Folio Pago', 'Folio Documento', 'Monto Pagado']
        df = df[columnas_ordenadas]

        return df, errors

    return None, errors

def process_emitted_invoice_files(uploaded_files):
    """Procesa múltiples archivos XML de facturas emitidas"""
    all_rows = []
    errors = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            xml_content = uploaded_file.read().decode('utf-8', errors='ignore')
            row = parse_xml_emitted_invoice(xml_content)

            if row:
                all_rows.append(row)
                status_text.text(f"Procesado: {uploaded_file.name}")
            else:
                errors.append(f"{uploaded_file.name}: No se pudo extraer información")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        except Exception as e:
            errors.append(f"{uploaded_file.name}: {str(e)}")

    progress_bar.empty()
    status_text.empty()

    if all_rows:
        df = pd.DataFrame(all_rows)
        # Ordenar por fecha si se pudo parsear
        try:
            df['_fecha_sort'] = pd.to_datetime(df['FECHA DD/MM/AA'], dayfirst=True, errors='coerce')
            df = df.sort_values('_fecha_sort').drop(columns=['_fecha_sort'])
        except Exception:
            pass
        df = df.reset_index(drop=True)
        return df, errors

    return None, errors

# ============= UI CON PESTAÑAS =============

tab1, tab2, tab3 = st.tabs(["📄 Facturas Recibidas", "💰 Pagos", "📤 Facturas emitidas"])

# ============= PESTAÑA 1: FACTURAS (RECIBIDAS) =============

with tab1:
    st.markdown("### Procesar Facturas XML")

    uploaded_files_inv = st.file_uploader(
        "Seleccionar archivos XML (Facturas)",
        type=['xml'],
        accept_multiple_files=True,
        key="invoices",
        help="Arrastra o selecciona múltiples archivos XML"
    )

    if uploaded_files_inv:
        st.markdown(f'<div class="status-info">{len(uploaded_files_inv)} archivo(s) seleccionado(s)</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 2])

        with col1:
            process_btn = st.button('Procesar y Descargar', type="primary", use_container_width=True, key="proc_inv")

        with col2:
            preview_btn = st.button('Vista Previa', type="secondary", use_container_width=True, key="prev_inv")

        if process_btn:
            with st.spinner('Procesando facturas...'):
                df, errors = process_invoice_files(uploaded_files_inv)

            if df is not None and len(df) > 0:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Facturas', index=False)

                    worksheet = writer.sheets['Facturas']
                    column_widths = {
                        'UUID': 40, 'Fecha': 20, 'Tipo': 8, 'RFC Emisor': 15,
                        'Emisor': 35, 'Descripcion': 60, 'Cantidad': 12,
                        'Importe': 12, 'IVA': 12, 'ISR Retenido': 15,
                        'IVA Retenido': 15, 'IEPS': 12, 'Subtotal': 12,
                        'Total': 12, 'Moneda': 10
                    }

                    for idx, col in enumerate(df.columns):
                        width = column_widths.get(col, 20)
                        col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                        worksheet.column_dimensions[col_letter].width = width

                output.seek(0)

                st.markdown(f'<div class="status-success">{len(df)} factura(s) procesada(s) y ordenada(s) cronológicamente</div>', unsafe_allow_html=True)

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
            df, errors = process_invoice_files(uploaded_files_inv)

            if df is not None and len(df) > 0:
                st.markdown("### Vista Previa (Ordenada cronológicamente)")
                st.dataframe(df.head(10), use_container_width=True, height=400)
                st.caption(f"Mostrando primeros 10 de {len(df)} facturas")

                if errors:
                    with st.expander("Advertencias"):
                        for error in errors:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">Error al procesar archivos</div>', unsafe_allow_html=True)

# ============= PESTAÑA 2: PAGOS =============

with tab2:
    st.markdown("### Procesar Pagos XML")

    uploaded_files_pay = st.file_uploader(
        "Seleccionar archivos XML (Pagos)",
        type=['xml'],
        accept_multiple_files=True,
        key="payments",
        help="Arrastra o selecciona múltiples archivos XML de pagos"
    )

    if uploaded_files_pay:
        st.markdown(f'<div class="status-info">{len(uploaded_files_pay)} archivo(s) seleccionado(s)</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 2])

        with col1:
            process_btn_pay = st.button('Procesar y Descargar', type="primary", use_container_width=True, key="proc_pay")

        with col2:
            preview_btn_pay = st.button('Vista Previa', type="secondary", use_container_width=True, key="prev_pay")

        if process_btn_pay:
            with st.spinner('Procesando pagos...'):
                df_pay, errors_pay = process_payment_files(uploaded_files_pay)

            if df_pay is not None and len(df_pay) > 0:
                output_pay = BytesIO()
                with pd.ExcelWriter(output_pay, engine='openpyxl') as writer:
                    df_pay.to_excel(writer, sheet_name='Pagos', index=False)

                    worksheet = writer.sheets['Pagos']
                    column_widths = {
                        'Receptor': 35, 'Fecha': 20, 'Mes': 12, 'RFC Receptor': 15,
                        'Folio Pago': 15, 'Folio Documento': 15, 'Monto Pagado': 15
                    }

                    for idx, col in enumerate(df_pay.columns):
                        width = column_widths.get(col, 20)
                        col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                        worksheet.column_dimensions[col_letter].width = width

                output_pay.seek(0)

                st.markdown(f'<div class="status-success">{len(df_pay)} pago(s) procesado(s) y ordenado(s) cronológicamente</div>', unsafe_allow_html=True)

                st.download_button(
                    label="Descargar Excel",
                    data=output_pay.getvalue(),
                    file_name=f"Pagos_SAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                if errors_pay:
                    st.markdown(f'<div class="status-warning">Advertencias: {len(errors_pay)} archivo(s) con problemas</div>', unsafe_allow_html=True)
                    with st.expander("Ver detalles"):
                        for error in errors_pay:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">No se encontraron pagos válidos</div>', unsafe_allow_html=True)
                if errors_pay:
                    for error in errors_pay:
                        st.error(error)

        if preview_btn_pay:
            df_pay, errors_pay = process_payment_files(uploaded_files_pay)

            if df_pay is not None and len(df_pay) > 0:
                st.markdown("### Vista Previa (Ordenada cronológicamente)")
                st.dataframe(df_pay.head(15), use_container_width=True, height=400)
                st.caption(f"Mostrando primeros 15 de {len(df_pay)} pagos")

                if errors_pay:
                    with st.expander("Advertencias"):
                        for error in errors_pay:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">Error al procesar archivos</div>', unsafe_allow_html=True)

# ============= PESTAÑA 3: FACTURAS EMITIDAS =============

with tab3:
    st.markdown("### Procesar Facturas Emitidas XML")

    uploaded_files_emit = st.file_uploader(
        "Seleccionar archivos XML (Facturas emitidas)",
        type=['xml'],
        accept_multiple_files=True,
        key="emitted_invoices",
        help="Arrastra o selecciona múltiples archivos XML emitidos"
    )

    if uploaded_files_emit:
        st.markdown(
            f'<div class="status-info">{len(uploaded_files_emit)} archivo(s) seleccionado(s)</div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([2, 2])

        with col1:
            process_btn_emit = st.button(
                'Procesar y Descargar',
                type="primary",
                use_container_width=True,
                key="proc_emit"
            )

        with col2:
            preview_btn_emit = st.button(
                'Vista Previa',
                type="secondary",
                use_container_width=True,
                key="prev_emit"
            )

        if process_btn_emit:
            with st.spinner('Procesando facturas emitidas...'):
                df_emit, errors_emit = process_emitted_invoice_files(uploaded_files_emit)

            if df_emit is not None and len(df_emit) > 0:
                output_emit = BytesIO()
                with pd.ExcelWriter(output_emit, engine='openpyxl') as writer:
                    df_emit.to_excel(writer, sheet_name='Facturas emitidas', index=False)

                    worksheet = writer.sheets['Facturas emitidas']
                    column_widths = {
                        'FECHA DD/MM/AA': 18,
                        'CLIENTE': 35,
                        'RFC': 15,
                        'No FACTURA': 15,
                        'ESTATUS': 12,
                        'Subtotal': 14,
                        'OTRO (DESCUENTO)': 18,
                        'IVA': 12,
                        'RET IVA': 12,
                        'TOTAL': 14,
                    }
                    for idx, col in enumerate(df_emit.columns):
                        width = column_widths.get(col, 20)
                        col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx // 26 - 1) + chr(65 + idx % 26)
                        worksheet.column_dimensions[col_letter].width = width

                output_emit.seek(0)

                st.markdown(
                    f'<div class="status-success">{len(df_emit)} factura(s) emitida(s) procesada(s)</div>',
                    unsafe_allow_html=True
                )

                st.download_button(
                    label="Descargar Excel",
                    data=output_emit.getvalue(),
                    file_name=f"Facturas_emitidas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                if errors_emit:
                    st.markdown(
                        f'<div class="status-warning">Advertencias: {len(errors_emit)} archivo(s) con problemas</div>',
                        unsafe_allow_html=True
                    )
                    with st.expander("Ver detalles"):
                        for error in errors_emit:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">No se encontraron facturas emitidas válidas</div>', unsafe_allow_html=True)
                if errors_emit:
                    for error in errors_emit:
                        st.error(error)

        if preview_btn_emit:
            df_emit, errors_emit = process_emitted_invoice_files(uploaded_files_emit)

            if df_emit is not None and len(df_emit) > 0:
                st.markdown("### Vista Previa")
                st.dataframe(df_emit.head(20), use_container_width=True, height=400)
                st.caption(f"Mostrando primeras {min(20, len(df_emit))} de {len(df_emit)} facturas emitidas")

                if errors_emit:
                    with st.expander("Advertencias"):
                        for error in errors_emit:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">Error al procesar archivos</div>', unsafe_allow_html=True)
