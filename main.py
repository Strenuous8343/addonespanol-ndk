import asyncio
import json
import os
import re
import shutil
import time
from datetime import datetime
import asyncio

import fakeredis
import httpx
from aiocron import crontab
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette import status

from debrid.get_debrid_service import get_debrid_service
from metadata.tmdb import TMDB
from utils.actualizarbd import actualizarbasesdatos
from utils.bd import (setup_index, getGood1fichierlink,
                      search_movies, search_tv_shows)
from utils.cargarbd import check_and_download
from utils.detection import detect_quality, post_process_results
from utils.fichier import get_file_info
from utils.filter_results import filter_items
from utils.logger import setup_logger
from utils.parse_config import parse_config
from utils.stremio_parser import parse_to_debrid_stream
from utils.string_encoding import decodeb64, encodeb64

from config import (
    VERSION,
    IS_DEV,
    IS_COMMUNITY_VERSION,
    ROOT_PATH,
    DB_ENCRYPTED_PATH,
    DB_DECRYPTED_PATH,
    UPDATE_LOG_FILE,
    VERSION_FILE,
    PING_URL,
    RENDER_API_URL,
    RENDER_AUTH_HEADER,
    DEBRID_API_KEY,
    ADMIN_PATH_DB_ENCRYPTED,
    ADMIN_PATH_DB_DECRYPTED,
    ADMIN_PATH_RESTART
)

# --- Inicialización ---
logger = setup_logger(__name__)
redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
# OPTIMIZADO: Crear un cliente httpx para reutilizar conexiones
http_client = httpx.AsyncClient(timeout=30)

FICHIER_STATUS_KEY = "rd_1fichier_status"

async def check_real_debrid_1fichier_availability():
    if not DEBRID_API_KEY:
        logger.warning("No se ha configurado DEBRID_API_KEY en .env.")
        return

    url = "https://api.real-debrid.com/rest/1.0/hosts/status"
    headers = {"Authorization": f"Bearer {DEBRID_API_KEY}"}
    status = "up"
    try:
        response = await http_client.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        hosts_status = response.json()
        
        for host_domain, info in hosts_status.items():
            if "1fichier" in host_domain.lower():
                if info.get("status", "").lower() != "up":
                    status = "down"
                break
    except Exception as e:
        logger.error(f"Error al comprobar estado de hosts de RD: {e}")
    finally:
        await redis_client.set(FICHIER_STATUS_KEY, status, ex=1800)
        logger.info(f"Estado de 1fichier en Real-Debrid actualizado a: '{status}'")

@crontab("*/15 * * * *", start=not IS_DEV)
async def scheduled_fichier_check():
    await check_real_debrid_1fichier_availability()

async def lifespan(app: FastAPI):
    """
    Realiza tareas de inicialización al arrancar la aplicación.
    Descarga, descifra y prepara la base de datos para su uso.
    """
    logger.info("Iniciando tareas de arranque...")

    await redis_client.set(FICHIER_STATUS_KEY, "up")
    logger.info(f"Estado inicial de 1fichier establecido a 'up' por defecto.")

    logger.info("Descargando base de datos...")
    if check_and_download():
        setup_index(DB_DECRYPTED_PATH)
        logger.info("Tareas de arranque completadas.")
    else:
        logger.error("No se pudo descargar la base de datos.")
    yield
    logger.info("La aplicación se está cerrando.")

# Configuración de la aplicación FastAPI
app = FastAPI(root_path=f"/{ROOT_PATH}" if ROOT_PATH and not ROOT_PATH.startswith("/") else ROOT_PATH, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LogFilterMiddleware:
    """Filtra datos sensibles de las URLs en los logs."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            path = request.url.path
            # Oculta configuraciones codificadas en la URL para no exponerlas en logs
            re.sub(r'/ey.*?/', '/<SENSITIVE_DATA>/', path)
        await self.app(scope, receive, send)


if not IS_DEV:
    app.add_middleware(LogFilterMiddleware)

templates = Jinja2Templates(directory="templates")


# --- Endpoints de la Interfaz y Manifiesto ---


@app.get("/", include_in_schema=False)
async def root():
    """Redirige a la página de configuración."""
    return RedirectResponse(url="/configure")


@app.get("/configure")
@app.get("/{config}/configure")
async def configure(request: Request):
    """Sirve la página de configuración del addon."""
    context = {
        "request": request,
        "isCommunityVersion": IS_COMMUNITY_VERSION,
        "version": VERSION
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/static/{file_path:path}", include_in_schema=False)
async def static_files(file_path: str):
    """Sirve archivos estáticos para la interfaz web."""
    return FileResponse(f"templates/{file_path}")


@app.get("/manifest.json")
@app.get("/{config}/manifest.json")
async def get_manifest():
    """
    Proporciona el manifiesto del addon a Stremio.
    Define las capacidades y metadatos del addon.
    """
    addon_name = f"NDK {' Community' if IS_COMMUNITY_VERSION else ''}{' (Dev)' if IS_DEV else ''}"
    return {
        "id": "test.streamioaddon.ndk",
        "icon": "https://i.ibb.co/zGmkQZm/ndk.jpg",
        "version": VERSION,
        "catalogs": [],
        "resources": ["stream"],
        "types": ["movie", "series"],
        "name": addon_name,
        "description": "El mejor AddOn para ver contenido en español. El contenido es obtenido de fuentes de terceros.",
        "behaviorHints": {"configurable": True},
    }


# --- Lógica Principal del Addon ---


async def _get_unrestricted_link(debrid_service, original_link: str, file_name=None) -> str | None:
    """
    Obtiene el enlace de descarga directa (sin restricciones) de un servicio Debrid.
    """
    debrid_name = type(debrid_service).__name__
    link_to_unrestrict = original_link

    try:
        if debrid_name == "RealDebrid":
            link_to_unrestrict = await getGood1fichierlink(http_client, original_link, file_name)
        unrestricted_data = await debrid_service.unrestrict_link(link_to_unrestrict)

        if not unrestricted_data:
            return None
        if debrid_name == "RealDebrid":
            return unrestricted_data.get('download')
        if debrid_name == "AllDebrid":
            return unrestricted_data.get('data', {}).get('link')
        return original_link
    except Exception as e:
        logger.error(f"Error al desrestringir el enlace {original_link} con {debrid_name}: {e}")
        return None


async def _process_and_cache_links(results_data: list, config: dict, debrid_service):
    """
    Procesa en segundo plano los enlaces, los desrestringe y los guarda en caché.
    """
    valid_results = []
    for link, data in results_data:
        filesize_gb = data.get('filesize', 0) / (1024 ** 3)
        if 'maxSize' in config and filesize_gb > int(config['maxSize']):
            continue
        if "selectedQualityExclusion" in config and data.get("quality") in config["selectedQualityExclusion"]:
            continue
        valid_results.append((link, data))

    valid_results.sort(key=lambda x: x[1].get('filesize', 0), reverse=True)

    for link, data in valid_results:
        file_name = data.get('nombre_fichero', 'unknown')
        final_link = await _get_unrestricted_link(debrid_service, link, file_name)
        if final_link:
            entry = {
                "config": config,
                "link": link,
                "final_link": final_link,
                "filesize": data.get('filesize'),
            }
            encoded_link = encodeb64(link)
            await redis_client.hset("final_links", encoded_link, json.dumps(entry))
        await asyncio.sleep(0)


@app.get("/{config_str}/stream/{stream_type}/{stream_id}")
async def get_results(config_str: str, stream_type: str, stream_id: str):
    """
    Busca y devuelve los streams disponibles para un item (película o serie).
    """
    start_time = time.time()
    stream_id = stream_id.replace(".json", "")
    config = parse_config(config_str)

    metadata_provider = TMDB(config, http_client)
    media = await metadata_provider.get_metadata(stream_id, stream_type)

    debrid_service = get_debrid_service(config, http_client)
    debrid_name = type(debrid_service).__name__

    fichier_status_rd = await redis_client.get(FICHIER_STATUS_KEY) or "up"

    if media.type == "movie":
        search_results = await search_movies(media.id)
    else:
        search_results = await search_tv_shows(media.id, media.season, media.episode)

    if not search_results:
        logger.info(f"No se encontraron resultados para {media.type} {stream_id}. Tiempo total: {time.time() - start_time:.2f}s")
        return {"streams": []}

    tasks = [get_file_info(http_client, link) for link in search_results if '1fichier' in link]
    file_infos = await asyncio.gather(*tasks, return_exceptions=True)

    info_map = {info[2]: info for info in file_infos if not isinstance(info, BaseException)}

    results_data = []
    for link in search_results:
        data = {'link': link, 'filesize': 0, 'quality': ''}
        if '1fichier' in link:
            info_result = info_map.get(link)
            if info_result:
                _, info_data, _ = info_result
                if info_data:
                    data['filesize'] = info_data.get('size', 0)
                    data['nombre_fichero'] = info_data.get('filename', '')
                    data['quality'] = detect_quality(data['nombre_fichero'])
            else:
                logger.warning(f"No se pudo obtener información de 1fichier para: {link}")
        results_data.append((link, data))

    asyncio.create_task(
        _process_and_cache_links(results_data, config, debrid_service)
    )

    streams_unfiltered = []
    for link, data in results_data:
        encoded_link = encodeb64(link)
        encoded_file_name = encodeb64(data.get('nombre_fichero', 'unknown'))
        playback_url = f"{config['addonHost']}/playback/{config_str}/{encoded_file_name}/{encoded_link}"
        stream = post_process_results(link, media, debrid_name, playback_url, data)
        streams_unfiltered.append(stream)

    streams = filter_items(streams_unfiltered, media, config=config)
    parse_to_debrid_stream(streams, config, media, debrid_name, fichier_is_up=(fichier_status_rd == "up"))

    logger.info(f"Resultados encontrados. Tiempo total: {time.time() - start_time:.2f}s")
    return {"streams": streams}


async def _handle_playback(config_str: str, query: str, file_name) -> str:
    """
    Lógica compartida para manejar las peticiones de reproducción.
    """
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query requerido.")

    config = parse_config(config_str)
    start_time = time.time()

    cached_data_json = await redis_client.hget("final_links", query)
    if cached_data_json:
        cached_data = json.loads(cached_data_json)
        if cached_data.get("config") == config:
            logger.info(f"Playback desde caché de Redis. Tiempo: {time.time() - start_time:.2f}s")
            return cached_data["final_link"]

    logger.info("Playback no encontrado en caché, desrestringiendo en tiempo real...")
    decoded_query = decodeb64(query)
    decoded_file_name = decodeb64(file_name)
    debrid_service = get_debrid_service(config, http_client)

    final_link = await _get_unrestricted_link(debrid_service, decoded_query, decoded_file_name)

    if final_link:
        logger.info(f"Enlace desrestringido. Tiempo total: {time.time() - start_time:.2f}s")
        return final_link

    logger.error(f"No se pudo obtener el enlace final para la consulta: {query}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo procesar el enlace.")


@app.get("/playback/{config_str}/{file_name}/{query}")
async def get_playback(config_str: str, file_name, query: str):
    """Redirige al stream final (GET)."""
    final_url = await _handle_playback(config_str, query, file_name)
    return RedirectResponse(url=final_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)


# TODO: Implementar HEAD para playback
@app.head("/playback/{config_str}/{query}")
async def head_playback():
    return Response(status_code=200)


# --- Tareas Programadas (Crons) y Rutas de Administración ---

@crontab("*/5 * * * *", start=not IS_DEV)
async def actualizar_bd():
    """Tarea programada para actualizar la base de datos cada 5 minutos."""
    if await actualizarbasesdatos():
        with open(UPDATE_LOG_FILE, 'a') as file:
            file.write(f"{datetime.now()}: Actualizando contenido...\n")

@crontab("* * * * *", start=not IS_DEV)
async def ping_service():
    """Mantiene el servicio activo en plataformas como Render haciendo un ping cada minuto."""
    try:
        async with httpx.AsyncClient() as client:
            await client.get(PING_URL)
    except httpx.RequestError as e:
        logger.error(f"Fallo en el ping al servicio: {e}")

@app.get("/fecha")
async def fecha_actualizacion():
    """Devuelve la fecha de la última actualización de la base de datos."""
    try:
        with open(UPDATE_LOG_FILE, 'r') as file:
            lines = file.readlines()
        return {"ultima_actualizacion": lines[-1].strip() if lines else "No hay registros."}
    except FileNotFoundError:
        return {"error": f"El archivo {UPDATE_LOG_FILE} no existe."}

@app.get("/version")
async def version_actualizacion():
    """Devuelve el contenido del archivo de versión."""
    try:
        with open(VERSION_FILE, 'r') as file:
            return {"version_info": file.readlines()}
    except FileNotFoundError:
        return {"error": f"El archivo {VERSION_FILE} no existe."}

# --- Endpoints de Administración (URLs ofuscadas) ---

@app.get(ADMIN_PATH_DB_ENCRYPTED)
async def coger_basedatos_encrypted():
    """Permite descargar el archivo de la base de datos encriptada."""
    if not os.path.exists(DB_ENCRYPTED_PATH):
        raise HTTPException(status_code=404, detail="Archivo no disponible.")
    return FileResponse(DB_ENCRYPTED_PATH, media_type='application/octet-stream')

@app.get(ADMIN_PATH_DB_DECRYPTED)
async def coger_basedatos_decrypted():
    """Permite descargar el archivo de la base de datos descifrada."""
    if not os.path.exists(DB_DECRYPTED_PATH):
        raise HTTPException(status_code=404, detail="Archivo no disponible.")
    return FileResponse(DB_DECRYPTED_PATH, media_type='application/octet-stream')

@app.get(ADMIN_PATH_RESTART)
async def reiniciar_servicio():
    """
    Reinicia el servicio en Render.com a través de su API.
    Requiere una variable de entorno RENDER_API_KEY.
    """
    headers = {
        "accept": "application/json",
        "authorization": RENDER_AUTH_HEADER,
        "content-type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(RENDER_API_URL, json={"clearCache": "clear"}, headers=headers)
            response.raise_for_status() # Lanza excepción para respuestas 4xx/5xx
            return {"status": "Servicio reiniciado exitosamente", "data": response.json()}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error de red al contactar Render: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)