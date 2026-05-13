from fastapi import APIRouter

from routes import auth, chat, food, notifications, profile, programs, weight, workouts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(weight.router)
api_router.include_router(food.router)
api_router.include_router(programs.router)
api_router.include_router(workouts.router)
api_router.include_router(chat.router)
api_router.include_router(notifications.router)
