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
        <p class="subtitle">Convierte tus facturas y pagos XML a Excel (con Estado vía metadata SAT)</p>
    </div>
""", unsafe_allow_html=True)

NS = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'cfdi3': 'http://www.sat.gob.mx/cfd/3',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20'
}

# ============= UTILIDADES =============

def safe_find_first(elem, paths, ns):
    for p in paths:
        found = elem.find(p, ns)
        if found is not None:
            return found
    return None

def extract_uuid(root):
    timbre = root.find('.//tfd:TimbreFiscalDigital', NS)
    if timbre is None:
        # fallback sin namespaces (por si viene plano)
        timbre = root.find('.//TimbreFiscalDigital')
    return timbre.get('UUID', '') if timbre is not None else ''


def parse_sat_metadata(file_bytes: bytes) -> pd.DataFrame:
    """Lee el TXT de metadata del SAT.

    Nota: El SAT suele entregar metadata como archivo TXT con valores separados por '|' y una fila por CFDI.
    Los encabezados pueden variar. Esta función intenta detectar columnas clave.
    """
    text = file_bytes.decode('utf-8', errors='ignore')
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Remover posibles líneas de encabezado vacías/no-data
    # Detectar delimitador
    delim = '|' if any('|' in ln for ln in lines[:5]) else ','

    # Construir filas
    rows = []
    for ln in lines:
        if delim == '|':
            parts = [p.strip() for p in ln.split('|')]
        else:
            parts = [p.strip() for p in ln.split(',')]
        rows.append(parts)

    # Heurística: si la primera fila parece header (tiene palabras) úsala
    header = rows[0]
    is_header = any(any(ch.isalpha() for ch in cell) for cell in header)

    if is_header:
        df = pd.DataFrame(rows[1:], columns=header)
    else:
        # Si no hay header, asignar columnas genéricas
        maxlen = max(len(r) for r in rows)
        cols = [f'col_{i+1}' for i in range(maxlen)]
        df = pd.DataFrame([r + [''] * (maxlen - len(r)) for r in rows], columns=cols)

    # Normalizar nombres de columnas
    df.columns = [c.strip() for c in df.columns]

    # Buscar UUID
    uuid_col = None
    for c in df.columns:
        if c.strip().lower() in ('uuid', 'foliofiscal', 'folio fiscal', 'folfiscal'):
            uuid_col = c
            break

    # Algunos metadatos vienen con nombres distintos
    if uuid_col is None:
        for c in df.columns:
            if 'uuid' in c.lower() or 'folio' in c.lower():
                uuid_col = c
                break

    if uuid_col is None:
        raise ValueError('No se pudo detectar la columna UUID/Folio Fiscal en la metadata.')

    # Buscar Estatus
    estatus_col = None
    for c in df.columns:
        cl = c.lower()
        if 'estatus' in cl or 'estado' in cl or 'situacion' in cl:
            estatus_col = c
            break

    # Algunas metadata no traen estatus; si no viene, dejar vacío
    if estatus_col is None:
        df['EstatusDetectado'] = ''
        estatus_col = 'EstatusDetectado'

    out = df[[uuid_col, estatus_col]].copy()
    out.columns = ['UUID', 'Estado']

    # Normalizar UUID
    out['UUID'] = out['UUID'].astype(str).str.strip().str.upper()
    out['Estado'] = out['Estado'].astype(str).str.strip()

    # Eliminar duplicados por UUID dejando el último
    out = out.drop_duplicates(subset=['UUID'], keep='last').reset_index(drop=True)
    return out


def apply_metadata_estado(df: pd.DataFrame, meta_df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if meta_df is None or meta_df.empty:
        # si no hay metadata, asegurar columna Estado
        if 'Estado' not in df.columns:
            df['Estado'] = ''
        return df

    # Normalizar UUID de df
    if 'UUID' in df.columns:
        df2 = df.copy()
        df2['UUID'] = df2['UUID'].astype(str).str.strip().str.upper()
        merged = df2.merge(meta_df, on='UUID', how='left', suffixes=('', '_meta'))
        # Si ya existe Estado (por otra fuente), preferir metadata cuando exista
        if 'Estado_meta' in merged.columns:
            if 'Estado' in df2.columns:
                merged['Estado'] = merged['Estado_meta'].where(merged['Estado_meta'].notna() & (merged['Estado_meta'] != ''), merged['Estado'])
                merged = merged.drop(columns=['Estado_meta'])
            else:
                merged = merged.rename(columns={'Estado_meta': 'Estado'})
        return merged

    # Si no hay UUID en df, no se puede cruzar
    df2 = df.copy()
    df2['Estado'] = ''
    return df2

# ============= PARSERS PARA FACTURAS =============

def parse_xml_invoice_one_row(xml_text):
    """Parsea un XML de factura y devuelve UNA fila por factura"""
    try:
        root = ET.fromstring(xml_text)

        fecha = root.get('Fecha', '')
        total = float(root.get('Total', '0') or 0)
        subtotal = float(root.get('SubTotal', '0') or 0)
        moneda = root.get('Moneda', 'MXN')
        tipo_comprobante = root.get('TipoDeComprobante', '')

        uuid = extract_uuid(root)

        # Emisor
        emisor = safe_find_first(root, ['cfdi:Emisor', 'cfdi3:Emisor', 'Emisor'], NS)

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

            impuestos_concepto = safe_find_first(concepto, ['cfdi:Impuestos', 'cfdi3:Impuestos', 'Impuestos'], NS)

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
            'Moneda': moneda,
            'Estado': ''
        }

    except Exception:
        return None

# ============= PARSERS PARA PAGOS =============

def parse_xml_payment(xml_text):
    """Parsea un XML de pago (Comprobante de Pago con complemento pago20)"""
    try:
        root = ET.fromstring(xml_text)

        # Datos principales del comprobante
        fecha_comprobante = root.get('Fecha', '')
        folio_comprobante = root.get('Folio', '')
        uuid = extract_uuid(root)

        # Receptor
        receptor = safe_find_first(root, ['cfdi:Receptor', 'Receptor'], NS)

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
            pago_list = pagos.findall('pago20:Pago', NS)
            if not pago_list:
                pago_list = pagos.findall('.//Pago')

            for pago in pago_list:
                monto_pago = float(pago.get('Monto', '0') or 0)

                doc_relacionados = pago.findall('pago20:DoctoRelacionado', NS)
                if not doc_relacionados:
                    doc_relacionados = pago.findall('.//DoctoRelacionado')

                if doc_relacionados:
                    for docto in doc_relacionados:
                        folio_docto = docto.get('Folio', '')
                        monto_docto = float(
                            docto.get('ImpPagado', '0') or
                            docto.get('ImPagado', '0') or
                            docto.get('MontoPagado', '0') or
                            docto.get('MontoPagedo', '0') or
                            0
                        )

                        rows.append({
                            'UUID': uuid,
                            'Receptor': receptor_nombre,
                            'Fecha': fecha_comprobante,
                            'Mes': '',
                            'RFC Receptor': receptor_rfc,
                            'Folio Pago': folio_comprobante,
                            'Folio Documento': folio_docto,
                            'Monto Pagado': round(monto_docto, 2),
                            'Estado': ''
                        })
                else:
                    rows.append({
                        'UUID': uuid,
                        'Receptor': receptor_nombre,
                        'Fecha': fecha_comprobante,
                        'Mes': '',
                        'RFC Receptor': receptor_rfc,
                        'Folio Pago': folio_comprobante,
                        'Folio Documento': '',
                        'Monto Pagado': round(monto_pago, 2),
                        'Estado': ''
                    })

        return rows

    except Exception:
        return []

# ============= PROCESADORES DE ARCHIVOS =============

def process_invoice_files(uploaded_files):
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

        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        df['Mes'] = df['Fecha'].dt.month.map(meses)

        df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')

        columnas_ordenadas = ['Receptor', 'Fecha', 'Mes', 'RFC Receptor', 'Folio Pago', 'Folio Documento', 'Monto Pagado', 'Estado', 'UUID']
        # mantener UUID al final (por si quieres cruzar/depurar); luego lo quitamos en export si no lo quieres
        df = df[columnas_ordenadas]
        return df, errors

    return None, errors


# ============= UI CON PESTAÑAS =============

tab1, tab2 = st.tabs(["📄 Facturas", "💰 Pagos"])

# ============= PESTAÑA 1: FACTURAS =============

with tab1:
    st.markdown("### Procesar Facturas XML")

    meta_file = st.file_uploader(
        "(Opcional) Subir Metadata del SAT (.txt) para llenar Estado (Vigente/Cancelado)",
        type=['txt'],
        accept_multiple_files=False,
        key="meta_inv",
        help="Descarga el archivo de metadatos desde SAT > Emitidas > Descargar Metadatos"
    )

    meta_df = None
    if meta_file is not None:
        try:
            meta_df = parse_sat_metadata(meta_file.getvalue())
            st.markdown(f'<div class="status-success">Metadata cargada: {len(meta_df)} UUID(s)</div>', unsafe_allow_html=True)
            with st.expander("Vista previa metadata"):
                st.dataframe(meta_df.head(15), use_container_width=True)
        except Exception as e:
            st.markdown(f'<div class="status-error">No se pudo leer la metadata: {str(e)}</div>', unsafe_allow_html=True)

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
                if df is not None:
                    df = apply_metadata_estado(df, meta_df)

            if df is not None and len(df) > 0:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Si no quieres mostrar UUID, puedes quitarlo aquí (pero lo dejo porque es clave)
                    df.to_excel(writer, sheet_name='Facturas', index=False)

                    worksheet = writer.sheets['Facturas']
                    column_widths = {
                        'UUID': 40, 'Fecha': 20, 'Tipo': 8, 'RFC Emisor': 15,
                        'Emisor': 35, 'Descripcion': 60, 'Cantidad': 12,
                        'Importe': 12, 'IVA': 12, 'ISR Retenido': 15,
                        'IVA Retenido': 15, 'IEPS': 12, 'Subtotal': 12,
                        'Total': 12, 'Moneda': 10, 'Estado': 14
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
            if df is not None:
                df = apply_metadata_estado(df, meta_df)

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

    meta_file_pay = st.file_uploader(
        "(Opcional) Subir Metadata del SAT (.txt) para llenar Estado (Vigente/Cancelado)",
        type=['txt'],
        accept_multiple_files=False,
        key="meta_pay",
        help="Descarga el archivo de metadatos desde SAT > Emitidas > Descargar Metadatos"
    )

    meta_df_pay = None
    if meta_file_pay is not None:
        try:
            meta_df_pay = parse_sat_metadata(meta_file_pay.getvalue())
            st.markdown(f'<div class="status-success">Metadata cargada: {len(meta_df_pay)} UUID(s)</div>', unsafe_allow_html=True)
            with st.expander("Vista previa metadata"):
                st.dataframe(meta_df_pay.head(15), use_container_width=True)
        except Exception as e:
            st.markdown(f'<div class="status-error">No se pudo leer la metadata: {str(e)}</div>', unsafe_allow_html=True)

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
                if df_pay is not None:
                    # para pagos, el UUID lo dejamos en df (al final) y aplicamos metadata
                    df_pay = apply_metadata_estado(df_pay, meta_df_pay)

            if df_pay is not None and len(df_pay) > 0:
                # Quitar UUID del export si no lo quieres en Excel
                export_pay = df_pay.copy()
                if 'UUID' in export_pay.columns:
                    export_pay = export_pay.drop(columns=['UUID'])

                output_pay = BytesIO()
                with pd.ExcelWriter(output_pay, engine='openpyxl') as writer:
                    export_pay.to_excel(writer, sheet_name='Pagos', index=False)

                    worksheet = writer.sheets['Pagos']
                    column_widths = {
                        'Receptor': 35, 'Fecha': 20, 'Mes': 12, 'RFC Receptor': 15,
                        'Folio Pago': 15, 'Folio Documento': 15, 'Monto Pagado': 15, 'Estado': 14
                    }

                    for idx, col in enumerate(export_pay.columns):
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
            if df_pay is not None:
                df_pay = apply_metadata_estado(df_pay, meta_df_pay)

            if df_pay is not None and len(df_pay) > 0:
                st.markdown("### Vista Previa (Ordenada cronológicamente)")
                # en preview sí mostramos UUID para depurar
                st.dataframe(df_pay.head(15), use_container_width=True, height=400)
                st.caption(f"Mostrando primeros 15 de {len(df_pay)} pagos")

                if errors_pay:
                    with st.expander("Advertencias"):
                        for error in errors_pay:
                            st.text(error)
            else:
                st.markdown('<div class="status-error">Error al procesar archivos</div>', unsafe_allow_html=True)
