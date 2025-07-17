from fastapi import APIRouter
from . import user, load_data

def create_api_router() -> APIRouter:
    main_router = APIRouter()
    
    main_router.include_router(user.create_users_router())
    main_router.include_router(load_data.load_data_router())

    return main_router