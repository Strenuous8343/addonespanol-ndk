import asyncio
import requests
from utils.cargarbd import check_and_download
from utils.bd import setup_index

from utils.logger import setup_logger

from config import (
    IS_DEV,
)

logger = setup_logger(__name__)
lock = asyncio.Lock()


async def actualizarbasesdatos():
    logger.info("Comprobando actualizaciones")
    if check_and_download():
        setup_index()
        if not IS_DEV:
            requests.get('https://ndkcatalogs.myblacknass.synology.me/getData')
        logger.info("Tareas de actualización completadas.")
        return True
    else:
        logger.error("No se pudo actualizar la base de datos.")
        return False
        
    
