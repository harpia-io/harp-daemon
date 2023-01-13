from logger.logging import service_logger
from fastapi import APIRouter
import harp_daemon.settings as settings

log = service_logger()

router = APIRouter(prefix=settings.URL_PREFIX)


@router.get('/health')
async def health():
    """
        Return general health check result
    """

    return {"msg": "Healthy"}
