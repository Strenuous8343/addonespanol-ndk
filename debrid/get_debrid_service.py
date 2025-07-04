from fastapi.exceptions import HTTPException
from debrid.alldebrid import AllDebrid
from debrid.realdebrid import RealDebrid
import httpx

def get_debrid_service(config, http_client: httpx.AsyncClient):
    service_name = config['service']
    if service_name == "realdebrid":
        debrid_service = RealDebrid(config, http_client)
    elif service_name == "alldebrid":
        debrid_service = AllDebrid(config, http_client)
    else:
        raise HTTPException(status_code=500, detail="Invalid service configuration.")

    return debrid_service