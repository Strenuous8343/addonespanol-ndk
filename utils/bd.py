# utils/bd.py
import aiosqlite
import httpx
from utils.fichier import copy_file
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def setup_index(conn: aiosqlite.Connection):
    """Crea los índices necesarios en la base de datos en memoria."""
    logger.info("Creando índices en la base de datos en memoria...")
    async with conn.cursor() as cursor:
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_pelis_tmdb ON enlaces_pelis(tmdb);")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_pelis_link ON enlaces_pelis(link);")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_series_tmdb_season_episode ON enlaces_series(tmdb, temporada, episodio);")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_enlaces_series_link ON enlaces_series(link);")
    await conn.commit()
    logger.info("Índices creados con éxito.")

async def update_db_movies(conn: aiosqlite.Connection, url: str, new_link: str):
    """Actualiza la tabla 'enlaces_pelis' con el nuevo enlace y marca el FLAG."""
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE enlaces_pelis SET enlace_modificado = ?, FLAG = 1 WHERE link = ?", (new_link, url))
    await conn.commit()

async def update_db_series(conn: aiosqlite.Connection, url: str, new_link: str):
    """Actualiza la tabla 'enlaces_series' con el nuevo enlace y marca el FLAG."""
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE enlaces_series SET enlace_modificado = ?, FLAG = 1 WHERE link = ?", (new_link, url))
    await conn.commit()

async def getGood1fichierlink(http_client: httpx.AsyncClient, conn: aiosqlite.Connection, link: str, file_name: str):
    """Obtiene un enlace válido de 1fichier, actualizando la BD si es necesario."""
    if "1fichier" not in link:
        return link

    async with conn.cursor() as cursor:
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
                        await update_db_movies(conn, from_url, to_url)
                    else:
                        await update_db_series(conn, from_url, to_url)
                    return to_url
                break
    return link

async def search_movies(conn: aiosqlite.Connection, id: str):
    """Busca enlaces de películas por su ID de TMDB."""
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT link FROM enlaces_pelis WHERE tmdb = ?", (id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def search_tv_shows(conn: aiosqlite.Connection, id: str, season: int, episode: int):
    """Busca enlaces de episodios de series."""
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT link FROM enlaces_series WHERE tmdb = ? AND temporada = ? AND episodio = ?",
            (id, season, episode)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def getMetadata(conn: aiosqlite.Connection, link: str, media_type: str):
    """Obtiene metadatos (calidad, audio, info) para un enlace específico."""
    table = "enlaces_pelis" if media_type == "movie" else "enlaces_series"
    async with conn.cursor() as cursor:
        await cursor.execute(f"SELECT calidad, audio, info FROM {table} WHERE link = ?", (link,))
        metadata = await cursor.fetchone()
        return str(metadata) if metadata else ""