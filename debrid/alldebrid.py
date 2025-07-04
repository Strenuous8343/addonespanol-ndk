from debrid.base_debrid import BaseDebrid
from utils.logger import setup_logger
import httpx

logger = setup_logger(__name__)

class AllDebrid(BaseDebrid):
    def __init__(self, config, http_client: httpx.AsyncClient):
        super().__init__(config, http_client)
        self.base_url = "https://api.alldebrid.com/v4/"

    async def unrestrict_link(self, link):
        url = f"{self.base_url}link/unlock?agent=jackett&apikey={self.config['debridKey']}&link={link}"
        return await self.get_json_response(url)