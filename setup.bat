@echo off
echo 🚀 Instalando SAT XML to Excel Extractor...

REM Crear entorno virtual
python -m venv venv

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Instalar dependencias
echo 📦 Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ ¡Instalación completada!
echo 🎯 Para ejecutar la app:
echo    streamlit run app_sat_extractor.py
pause
