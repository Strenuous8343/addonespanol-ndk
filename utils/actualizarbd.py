# utils/actualizarbd.py

import httpx
import os
import xml.etree.ElementTree as ET
from utils.logger import setup_logger

from config import (
    WORKING_PATH
)

logger = setup_logger(__name__)

# --- Constantes para el CONTENIDO (Base de Datos)
CONTENIDO_TIMESTAMP_FILE = os.path.join(WORKING_PATH,'contenido_last_update.txt')
CONTENIDO_REPO_URL = "https://github.com/Maniac2017/Mipal2025/commits/main.atom"

# --- Constantes para el ADDON (Código)
ADDON_TIMESTAMP_FILE = os.path.join(WORKING_PATH,'addon_last_update.txt')
ADDON_REPO_URL = "https://github.com/Strenuous8343/addonespanol-ndk/commits/deploy_pc.atom"

async def _comprobar_remoto(url_atom, fichero_timestamp, tipo_contenido):
    """Función genérica para comprobar un repositorio y su fichero de timestamp."""
    logger.info(f"Comprobando actualizaciones del {tipo_contenido}...")
    
    last_local_timestamp = ""
    if os.path.exists(fichero_timestamp):
        with open(fichero_timestamp, 'r') as f:
            last_local_timestamp = f.read().strip()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_atom, timeout=30)
            response.raise_for_status()
        
        root = ET.fromstring(response.text)
        namespace = '{http://www.w3.org/2005/Atom}'
        latest_entry = root.find(f'{namespace}entry')
        if latest_entry is None:
            logger.warning(f"No se encontró 'entry' en el feed de commits para {tipo_contenido}.")
            return False

        latest_remote_timestamp = latest_entry.find(f'{namespace}updated').text.strip()
        
    except Exception as e:
        logger.error(f"No se pudo comprobar la actualización para {tipo_contenido}: {e}")
        return False

    logger.info(f"Versión local {tipo_contenido}: {last_local_timestamp or 'Ninguna'}")
    logger.info(f"Versión remota {tipo_contenido}: {latest_remote_timestamp}")

    if latest_remote_timestamp != last_local_timestamp:
        logger.info(f"¡Nueva actualización de {tipo_contenido} detectada!")
        with open(fichero_timestamp, 'w') as f:
            f.write(latest_remote_timestamp)
        return True
    
    return False

async def comprobar_actualizacion_contenido():
    """Comprueba si hay actualizaciones en el repositorio de contenido."""
    return await _comprobar_remoto(CONTENIDO_REPO_URL, CONTENIDO_TIMESTAMP_FILE, "CONTENIDO")

async def comprobar_actualizacion_addon():
    """Comprueba si hay actualizaciones en el repositorio del código del addon."""
    return await _comprobar_remoto(ADDON_REPO_URL, ADDON_TIMESTAMP_FILE, "ADDON")