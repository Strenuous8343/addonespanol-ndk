from debrid.base_debrid import BaseDebrid
from utils.logger import setup_logger
import httpx

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