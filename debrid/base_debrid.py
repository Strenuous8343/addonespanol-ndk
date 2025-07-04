import httpx # OPTIMIZADO: Importar httpx
from utils.logger import setup_logger

class BaseDebrid:
    def __init__(self, config, http_client: httpx.AsyncClient): # OPTIMIZADO: Recibir el cliente http
        self.config = config
        self.logger = setup_logger(__name__)
        self.http_client = http_client # OPTIMIZADO: Usar el cliente http asíncrono

    async def get_json_response(self, url, method='get', data=None, headers=None, files=None): # OPTIMIZADO: Convertir a async
        try:
            if method == 'get':
                response = await self.http_client.get(url, headers=headers)
            elif method == 'post':
                response = await self.http_client.post(url, data=data, headers=headers, files=files)
            elif method == 'put':
                response = await self.http_client.put(url, data=data, headers=headers)
            elif method == 'delete':
                response = await self.http_client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Lanza una excepción para códigos de error 4xx/5xx
            return response.json()

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Request failed with status code {e.response.status_code} and response: {e.response.text}")
            return None
        except httpx.RequestError as e:
            self.logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
            return None
        except ValueError:
            self.logger.error(f"Failed to parse response as JSON: {response.text}")
            return None