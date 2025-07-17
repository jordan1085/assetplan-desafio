import os
from fastapi import APIRouter, HTTPException
from src.schemas.chroma import Response
from src.services.load_data_service import load_data_service
from src.core.logging import logger

def load_data_router() -> APIRouter:
    router = APIRouter(prefix="/load-deptos", tags=["Document Management"])

    @router.post("/", response_model=Response, status_code=200)
    async def load_deptos_endpoint(
        deptos: dict
    ):
        try:
            data = await load_data_service.load_deptos(deptos)

            return Response(
                data=data,
            )
        except Exception as e:
            logger.error(f"Error in load data endpoint: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
    return router