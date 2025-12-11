#!/bin/bash

echo "🚀 Instalando SAT XML to Excel Extractor..."

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ ¡Instalación completada!"
echo "🎯 Para ejecutar la app:"
echo "   streamlit run app_sat_extractor.py"
