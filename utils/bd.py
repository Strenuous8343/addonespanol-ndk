import sqlite3
import aiosqlite
import httpx
from contextlib import asynccontextmanager
from utils.fichier import copy_file
from utils.logger import setup_logger
from config import DB_DECRYPTED_PATH, DB_ENCRYPTED_PATH


logger = setup_logger(__name__)


@asynccontextmanager
async def get_cursor():
    """
    Proporciona un cursor de base de datos asíncrono gestionando la conexión.

    Yields:
        aiosqlite.Cursor: Un cursor para ejecutar operaciones en la base de datos.
    """
    connection = None
    try:
        connection = await aiosqlite.connect(DB_DECRYPTED_PATH)
        cursor = await connection.cursor()
        yield cursor
        await connection.commit()
    finally:
        if connection:
            await connection.close()

def setup_index(db_path=DB_DECRYPTED_PATH):
    """
    Prepara la base de datos: crea columnas necesarias y los índices para optimizar búsquedas.
    Se ejecuta de forma segura, usando 'IF NOT EXISTS' para no duplicar.
    """
    logger.info("Configurando la base de datos: comprobando columnas e índices...")
    logger.info(f"Ruta de la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:        
        # --- Creación de Índices para acelerar búsquedas ---
        logger.info("Creando índices para mejorar el rendimiento de las búsquedas...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_pelis_tmdb ON enlaces_pelis(tmdb);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_pelis_link ON enlaces_pelis(link);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_series_tmdb_season_episode ON enlaces_series(tmdb, temporada, episodio);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_series_link ON enlaces_series(link);")
        
        conn.commit()
        logger.info("La configuración de la base de datos ha finalizado con éxito.")
    finally:
        conn.close()


def add_flag(db_path=DB_ENCRYPTED_PATH):
    """
    Prepara la base de datos: crea columnas necesarias y los índices para optimizar búsquedas.
    Se ejecuta de forma segura, usando 'IF NOT EXISTS' para no duplicar.
    """
    logger.info("Configurando la base de datos: comprobando columnas e índices...")
    logger.info(f"Ruta de la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # --- Creación de columnas necesarias ---
        for table in ['enlaces_pelis', 'enlaces_series']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [column[1] for column in cursor.fetchall()]
            if 'FLAG' not in columns:
                logger.info(f"Creando columna 'FLAG' en la tabla '{table}'.")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN FLAG INTEGER DEFAULT 0")
            if 'enlace_modificado' not in columns:
                logger.info(f"Creando columna 'enlace_modificado' en la tabla '{table}'.")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN enlace_modificado TEXT DEFAULT ''")
        
        
        conn.commit()
        logger.info("La adición de columnas FLAG ha finalizado con éxito.")
    finally:
        conn.close()


async def update_db_movies(url, new_link):
    """
    Actualiza la tabla 'enlaces_pelis' con el nuevo enlace y marca el FLAG como 1.

    Args:
        url (str): El enlace original que sirve como identificador.
        new_link (str): El nuevo enlace modificado a guardar.
    """
    async with get_cursor() as cursor:
        await cursor.execute("UPDATE enlaces_pelis SET enlace_modificado = ?, FLAG = 1 WHERE link = ?", (new_link, url))

async def update_db_series(url, new_link):
    """
    Actualiza la tabla 'enlaces_series' con el nuevo enlace y marca el FLAG como 1.

    Args:
        url (str): El enlace original que sirve como identificador.
        new_link (str): El nuevo enlace modificado a guardar.
    """
    async with get_cursor() as cursor:
        await cursor.execute("UPDATE enlaces_series SET enlace_modificado = ?, FLAG = 1 WHERE link = ?", (new_link, url))

async def getGood1fichierlink(http_client: httpx.AsyncClient, link, file_name):
    """
    Obtiene un enlace válido de 1fichier.
    """
    if "1fichier" not in link:
        return link

    async with get_cursor() as cursor:
        for table in ("enlaces_pelis", "enlaces_series"):
            await cursor.execute(f"SELECT FLAG, enlace_modificado FROM {table} WHERE link = ?", (link,))
            row = await cursor.fetchone()
            if row:
                flag, enlace_modificado = row
                if flag == 1 and enlace_modificado:
                    return enlace_modificado
                
                result = await copy_file(http_client, link, file_name)
                if result:
                    from_url, to_url = result
                    if table == "enlaces_pelis":
                        await update_db_movies(from_url, to_url)
                    else:
                        await update_db_series(from_url, to_url)
                    return to_url
                break
    return link

async def search_movies(id):
    """
    Busca enlaces de películas en la base de datos por su ID de TMDB.

    Args:
        id (str or int): El ID de TMDB de la película.

    Returns:
        list: Una lista de enlaces (str) asociados a la película.
    """
    async with get_cursor() as cursor:
        await cursor.execute("SELECT link FROM enlaces_pelis WHERE tmdb = ?", (id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def search_tv_shows(id, season, episode):
    """
    Busca enlaces de episodios de series por ID de TMDB, temporada y episodio.

    Args:
        id (str or int): El ID de TMDB de la serie.
        season (str or int): El número de la temporada.
        episode (str or int): El número del episodio.

    Returns:
        list: Una lista de enlaces (str) asociados al episodio.
    """
    async with get_cursor() as cursor:
        await cursor.execute(
            "SELECT link FROM enlaces_series WHERE tmdb = ? AND temporada = ? AND episodio = ?",
            (id, season, episode)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

def getMetadata(link, media_type):
    """
    Obtiene metadatos (calidad, audio, info) para un enlace específico.

    Args:
        link (str): El enlace cuyos metadatos se desean obtener.
        media_type (str): El tipo de medio ('movie' o 'series').

    Returns:
        str: Una cadena de texto representando los metadatos encontrados.
    """
    conn = sqlite3.connect(DB_DECRYPTED_PATH)
    cursor = conn.cursor()
    try:
        table = "enlaces_pelis" if media_type == "movie" else "enlaces_series"
        cursor.execute(f"SELECT calidad, audio, info FROM {table} WHERE link = ?", (link,))
        metadata = cursor.fetchone()
        return str(metadata) if metadata else ""
    finally:
        conn.close()