from debrid.base_debrid import BaseDebrid
from utils.logger import setup_logger
import httpx
import re
from urllib.parse import unquote, urljoin

logger = setup_logger(__name__)

class RealDebrid(BaseDebrid):
    def __init__(self, config, http_client: httpx.AsyncClient):
        super().__init__(config, http_client)
        self.base_url = "https://api.real-debrid.com"
        self.headers = {"Authorization": f"Bearer {self.config['debridKey']}"}

    async def unrestrict_link(self, link):
        url = f"{self.base_url}/rest/1.0/unrestrict/link"
        data = {"link": link}
        return await self.get_json_response(url, method='post', headers=self.headers, data=data)

    async def find_link_in_folder(self, http_folder_url, filename):
        """
        Busca en la carpeta HTTP de Real-Debrid para encontrar el enlace de descarga directa.
        La comparación se realiza usando el ID único al final del nombre del archivo.
        """
        if not http_folder_url or not http_folder_url.startswith("https://my.real-debrid.com/"):
            self.logger.warning("La URL de la carpeta HTTP de Real-Debrid no es válida o no está configurada.")
            return None

        links_folder_url = f"{http_folder_url.rstrip('/')}/links/"
        self.logger.info(f"Iniciando búsqueda por ID único para: '{filename}'")

        # 1. Extraer el ID del nombre de archivo de la API
        try:
            api_id_start_index = filename.rfind(')') + 1
            api_id = filename[api_id_start_index:] if api_id_start_index > 0 else None
        except:
            api_id = None

        if not api_id:
            self.logger.warning(f"No se pudo extraer el ID del filename de la API: '{filename}'. Cancelando búsqueda.")
            return None
            

        try:
            response = await self.http_client.get(links_folder_url, follow_redirects=True)
            response.raise_for_status()
            html_content = response.text
            
            hrefs = re.findall(r'<a href="([^"]+)">[^<]*<\/a>', html_content)

            for href in hrefs:
                if "Parent Directory" in href or href == "../":
                    continue
                
                decoded_href = unquote(href)
                
                # 2. Extraer el ID del nombre del archivo en el href
                try:
                    href_id_start_index = decoded_href.rfind(')') + 1
                    href_id = decoded_href[href_id_start_index:] if href_id_start_index > 0 else None
                except:
                    href_id = None
                
                # 3. Comparar los IDs
                if href_id and api_id == href_id:
                    full_link_url = urljoin(links_folder_url, href)
                    self.logger.info(f"✅ Coincidencia por ID único encontrada! URL: {full_link_url}")
                    return full_link_url

            self.logger.warning(f"No se pudo encontrar en la carpeta un enlace con el ID '{api_id}'.")
            return None

        except Exception as e:
            self.logger.error(f"Error al buscar en la carpeta de Real-Debrid {links_folder_url}: {e}")
            return None