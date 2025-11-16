Instrucciones rápidas para ejecutar el servicio SOAP:

1) Crear/activar tu entorno virtual (recomendado):

# macOS / zsh
python3 -m venv .venv
source .venv/bin/activate

2) Instalar dependencias:

pip install -r requirements.txt

3) Ejecutar el servicio:

python3 app.py

- El servidor escuchará en http://localhost:8000/ y el WSDL estará en http://localhost:8000/?wsdl

Notas:
- Si usas un gestor de paquetes distinto o un entorno global, ajusta los comandos según corresponda.
- Si no puedes conectarte a la base de datos remota, revisa la variable DATABASE_URL en `app.py`.
