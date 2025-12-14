import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Extractor SAT XML → Excel",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        margin-bottom: 30px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0c5460;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>📊 Extractor SAT XML → Excel</h1><p>Convierte tus facturas XML del SAT a un archivo Excel con desglose de impuestos</p></div>', unsafe_allow_html=True)

def parse_xml_invoice(xml_text):
    """Parsea un archivo XML de factura SAT y extrae los datos incluyendo impuestos"""
    try:
        root = ET.fromstring(xml_text)

        # Namespaces para CFDI v3.3 y v4.0
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'cfdi3': 'http://www.sat.gob.mx/cfd/3',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }

        # Datos principales del comprobante
        fecha = root.get('Fecha', '')
        total = root.get('Total', '0')
        subtotal = root.get('SubTotal', '0')
        moneda = root.get('Moneda', 'MXN')
        tipo_comprobante = root.get('TipoDeComprobante', '')

        # Extraer UUID del TimbreFiscalDigital
        timbre = root.find('.//tfd:TimbreFiscalDigital', ns)
        uuid = timbre.get('UUID', '') if timbre is not None else ''

        # Emisor
        emisor = root.find('cfdi:Emisor', ns)
        if emisor is None:
            emisor = root.find('cfdi3:Emisor', ns)
        if emisor is None:
            emisor = root.find('Emisor')

        emisor_rfc = emisor.get('Rfc', '') if emisor is not None else ''
        emisor_nombre = emisor.get('Nombre', '') if emisor is not None else ''

        # Conceptos (líneas de factura)
        conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', ns)

        if not conceptos:
            conceptos = root.findall('cfdi3:Conceptos/cfdi3:Concepto', ns)

        if not conceptos:
            conceptos = root.findall('.//Concepto')

        invoices = []

        if len(conceptos) == 0:
            # Si no hay conceptos, crear un registro único
            invoices.append({
                'UUID': uuid,
                'Fecha': fecha,
                'Tipo': tipo_comprobante,
                'RFC Emisor': emisor_rfc,
                'Emisor': emisor_nombre,
                'Descripción': '',
                'Cantidad': '',
                'Precio Unitario': '',
                'Importe': '',
                'IVA': '',
                'ISR Retenido': '',
                'IVA Retenido': '',
                'IEPS': '',
                'Subtotal': subtotal,
                'Total': total,
                'Moneda': moneda
            })
        else:
            # Un registro por cada concepto
            for concepto in conceptos:
                cantidad = concepto.get('Cantidad', '1')

                # CFDI 4.0 usa ValorUnitario, CFDI 3.3 usa PrecioUnitario
                precio_unitario = concepto.get('ValorUnitario', '')
                if not precio_unitario:
                    precio_unitario = concepto.get('PrecioUnitario', '0')

                importe = concepto.get('Importe', '0')
                descripcion = concepto.get('Descripcion', '')

                # Extraer impuestos del concepto
                iva_traslado = 0.0
                isr_retenido = 0.0
                iva_retenido = 0.0
                ieps = 0.0

                impuestos_concepto = concepto.find('cfdi:Impuestos', ns)
                if impuestos_concepto is None:
                    impuestos_concepto = concepto.find('cfdi3:Impuestos', ns)
                if impuestos_concepto is None:
                    impuestos_concepto = concepto.find('Impuestos')

                if impuestos_concepto is not None:
                    # Traslados (IVA, IEPS)
                    traslados = impuestos_concepto.findall('cfdi:Traslados/cfdi:Traslado', ns)
                    if not traslados:
                        traslados = impuestos_concepto.findall('cfdi3:Traslados/cfdi3:Traslado', ns)
                    if not traslados:
                        traslados = impuestos_concepto.findall('.//Traslado')

                    for traslado in traslados:
                        impuesto_tipo = traslado.get('Impuesto', '')
                        importe_imp = float(traslado.get('Importe', '0'))

                        if impuesto_tipo == '002':  # IVA
                            iva_traslado += importe_imp
                        elif impuesto_tipo == '003':  # IEPS
                            ieps += importe_imp

                    # Retenciones (ISR, IVA)
                    retenciones = impuestos_concepto.findall('cfdi:Retenciones/cfdi:Retencion', ns)
                    if not retenciones:
                        retenciones = impuestos_concepto.findall('cfdi3:Retenciones/cfdi3:Retencion', ns)
                    if not retenciones:
                        retenciones = impuestos_concepto.findall('.//Retencion')

                    for retencion in retenciones:
                        impuesto_tipo = retencion.get('Impuesto', '')
                        importe_imp = float(retencion.get('Importe', '0'))

                        if impuesto_tipo == '001':  # ISR
                            isr_retenido += importe_imp
                        elif impuesto_tipo == '002':  # IVA
                            iva_retenido += importe_imp

                invoices.append({
                    'UUID': uuid,
                    'Fecha': fecha,
                    'Tipo': tipo_comprobante,
                    'RFC Emisor': emisor_rfc,
                    'Emisor': emisor_nombre,
                    'Descripción': descripcion,
                    'Cantidad': cantidad,
                    'Precio Unitario': precio_unitario,
                    'Importe': importe,
                    'IVA': f"{iva_traslado:.2f}" if iva_traslado > 0 else '0.00',
                    'ISR Retenido': f"{isr_retenido:.2f}" if isr_retenido > 0 else '0.00',
                    'IVA Retenido': f"{iva_retenido:.2f}" if iva_retenido > 0 else '0.00',
                    'IEPS': f"{ieps:.2f}" if ieps > 0 else '0.00',
                    'Subtotal': subtotal,
                    'Total': total,
                    'Moneda': moneda
                })

        return invoices

    except ET.ParseError as e:
        st.error(f"Error al parsear XML: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        return None

def process_files(uploaded_files):
    """Procesa múltiples archivos XML y retorna un DataFrame consolidado"""
    all_invoices = []
    errors = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            xml_content = uploaded_file.read().decode('utf-8')
            invoices = parse_xml_invoice(xml_content)

            if invoices:
                all_invoices.extend(invoices)
                status_text.text(f"✅ Procesado: {uploaded_file.name}")
            else:
                errors.append(f"⚠️ {uploaded_file.name}: No se pudo extraer información")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        except Exception as e:
            errors.append(f"❌ {uploaded_file.name}: {str(e)}")

    progress_bar.empty()
    status_text.empty()

    return pd.DataFrame(all_invoices) if all_invoices else None, errors

# Interfaz principal
uploaded_files = st.file_uploader(
    "📁 Sube tus archivos XML del SAT",
    type=['xml'],
    accept_multiple_files=True,
    help="Selecciona uno o más archivos XML de facturas"
)

if uploaded_files:
    st.markdown(f'<div class="info-box">📦 {len(uploaded_files)} archivo(s) seleccionado(s)</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        process_btn = st.button('🔄 Procesar y Descargar', use_container_width=True)

    with col2:
        preview_btn = st.button('👁️ Vista Previa', use_container_width=True)

    if process_btn:
        with st.spinner('⏳ Procesando archivos...'):
            df, errors = process_files(uploaded_files)

        if df is not None and len(df) > 0:
            # Descargar Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Facturas', index=False)

                # Ajustar ancho de columnas
                worksheet = writer.sheets['Facturas']
                column_widths = {
                    'UUID': 40,
                    'Fecha': 20,
                    'Tipo': 8,
                    'RFC Emisor': 15,
                    'Emisor': 30,
                    'Descripción': 50,
                    'Cantidad': 10,
                    'Precio Unitario': 15,
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

            st.markdown(f'<div class="success-box">✅ Éxito: {len(df)} registros procesados de {df["UUID"].nunique()} facturas</div>', unsafe_allow_html=True)

            st.download_button(
                label="📥 Descargar Excel",
                data=output.getvalue(),
                file_name=f"Facturas_SAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            if errors:
                st.warning("⚠️ Algunos archivos tuvieron problemas:")
                for error in errors:
                    st.text(error)
        else:
            st.markdown('<div class="error-box">❌ No se encontraron facturas válidas en los archivos</div>', unsafe_allow_html=True)
            if errors:
                for error in errors:
                    st.error(error)

    if preview_btn:
        df, errors = process_files(uploaded_files)

        if df is not None and len(df) > 0:
            st.markdown("### 👁️ Vista Previa (primeros 5 registros)")
            st.dataframe(df.head(), use_container_width=True)
            st.markdown(f"**Total de registros:** {len(df)} | **Facturas únicas:** {df['UUID'].nunique()}")

            if errors:
                st.warning("⚠️ Advertencias:")
                for error in errors:
                    st.text(error)
        else:
            st.markdown('<div class="error-box">❌ Error al procesar archivos</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    ### 🚀 Cómo usar:

    1. **Carga tus XMLs**: Haz clic en el área de carga o arrastra tus archivos XML
    2. **Procesa**: Click en "Procesar y Descargar" para generar el Excel
    3. **Descarga**: El archivo Excel se descargará automáticamente

    ### ✨ Características:
    - ✅ Procesa múltiples archivos XML simultáneamente
    - ✅ Soporta CFDI v3.3 y v4.0
    - ✅ **Desglose completo de impuestos** (IVA, ISR, IEPS)
    - ✅ Extrae información esencial
    - ✅ Genera Excel con formato profesional
    - ✅ Vista previa de los datos antes de descargar
    - ✅ Manejo automático de errores

    ### 📋 Información extraída:
    - **UUID** - Identificador único fiscal
    - **Fecha** - Fecha de emisión
    - **Tipo** - Tipo de comprobante (I, E, P, N)
    - **RFC Emisor** y **Emisor** - Quien emite
    - **Descripción** - Detalle del concepto
    - **Cantidad**, **Precio Unitario**, **Importe**
    - **IVA** - IVA trasladado (16%)
    - **ISR Retenido** - ISR retenido si aplica
    - **IVA Retenido** - IVA retenido si aplica
    - **IEPS** - Impuesto especial si aplica
    - **Subtotal**, **Total**, **Moneda**

    ### 💡 Tipos de impuestos:
    - **Traslados**: IVA (16%), IEPS
    - **Retenciones**: ISR (10%), IVA Retenido (10.67%)
    """)