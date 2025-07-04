import httpx # OPTIMIZADO
from metadata.metadata_provider_base import MetadataProvider
from models.movie import Movie
from models.series import Series

class TMDB(MetadataProvider):
    def __init__(self, config, http_client: httpx.AsyncClient):
        super().__init__(config)
        self.http_client = http_client

    async def get_metadata(self, id, type):
        self.logger.info("Getting metadata for " + type + " with id " + id)

        full_id = id.split(":")
        self.logger.debug("Full id: " + str(full_id))
        
        url = f"https://api.themoviedb.org/3/find/{full_id[0]}?api_key={self.config['tmdbApi']}&external_source=imdb_id&language=es-ES"
        
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            self.logger.error(f"Error requesting TMDB metadata: {e}")
            return None # O lanzar una excepción
        except httpx.HTTPStatusError as e:
            self.logger.error(f"TMDB request failed with status {e.response.status_code}")
            return None # O lanzar una excepción

        result = None
        if type == "movie" and data.get("movie_results"):
            result = Movie(
                id=data["movie_results"][0]["id"],
                titles=[self.replace_weird_characters(data["movie_results"][0]["title"])],
                year=data["movie_results"][0]["release_date"][:4],
                languages='es-ES'
            )
        elif type == "series" and data.get("tv_results"):
            result = Series(
                id=data["tv_results"][0]["id"],
                titles=[self.replace_weird_characters(data["tv_results"][0]["name"])],
                season=int(full_id[1]),
                episode=int(full_id[2]),
                languages='es-ES'
            )
        
        if result:
            self.logger.info("Got metadata for " + type + " with id " + id)
        else:
            self.logger.warning("Could not find metadata for " + type + " with id " + id)

        return result