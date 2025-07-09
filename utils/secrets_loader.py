import os
from dotenv import load_dotenv

def load_secrets():
    """
    Carga las variables de entorno desde el archivo .env al entorno del sistema.
    """
    load_dotenv()
    print("✅ Variables de entorno cargadas desde .env")

def get_secret(key, default=None):
    """
    Obtiene un secreto directamente de las variables de entorno.
    """
    return os.getenv(key, default)