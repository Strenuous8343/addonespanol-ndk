import os
import httpx
import random
import string
from utils.logger import setup_logger
from config import FICHIER_API_KEY

logger = setup_logger(__name__)

def generate_guid(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def get_file_info(http_client: httpx.AsyncClient, url: str):
    info_url = "https://api.1fichier.com/v1/file/info.cgi"
    api_key = FICHIER_API_KEY
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"url": url}

    try:
        response = await http_client.post(info_url, headers=headers, json=data)
        response.raise_for_status()
        file_info = response.json()
        return file_info.get('filename'), file_info, url
    except httpx.RequestError as e:
        logger.error(f"Error al obtener la información del archivo desde {url}: {e}")
        return None, None, url

async def copy_file(http_client: httpx.AsyncClient, url: str, rename=None, _retry=False):
    cp_url = "https://api.1fichier.com/v1/file/cp.cgi"
    api_key = FICHIER_API_KEY
    new_filename = rename[:rename.rfind('.')] + generate_guid() if rename else generate_guid()
    
    logger.debug(f"Nuevo nombre de archivo: {new_filename}")
    data = {"urls": [url], "rename": new_filename}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = await http_client.post(cp_url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200 and 'urls' in response_json:
            logger.info(f"Archivo copiado exitosamente: {new_filename}")
            urls_data = response_json['urls'][0]
            from_url = urls_data.get('from_url')
            to_url = urls_data.get('to_url')
            if from_url and to_url:
                return from_url, to_url
        
        if (response_json.get("status") == "KO" and "Bad filename characters" in response_json.get("message", "") and rename is not None and not _retry):
            logger.debug("Reintentando sin rename por error de caracteres inválidos.")
            return await copy_file(http_client, url, rename=None, _retry=True)
        
        logger.debug(f"Error en la respuesta de la API al copiar: {response_json}")
        return None, None
        
    except httpx.RequestError as e:
        logger.error(f"Excepción de red al copiar el archivo: {e}")
        return None, None
    except (KeyError, IndexError) as e:
        logger.error(f"Error al procesar la respuesta JSON de la API: {e}")
        return None, None