from fastapi import APIRouter

from app.routes import (
    auth,
    chat,
    exercises,
    food,
    notifications,
    photos,
    profile,
    programs,
    weight,
    workouts,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(weight.router)
api_router.include_router(food.router)
api_router.include_router(programs.router)
api_router.include_router(workouts.router)
api_router.include_router(chat.router)
api_router.include_router(notifications.router)
api_router.include_router(photos.router)
api_router.include_router(exercises.router)
