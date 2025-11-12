from fastapi import APIRouter
from app.services.example_service import service
from app.common.logging.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/hello")
def hello():
    logger.info("hello endpoint called")
    return service.fetch()
