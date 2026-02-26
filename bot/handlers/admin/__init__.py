# Admin handlers package
from bot.handlers.admin.menu import router as menu_router
from bot.handlers.admin.create_prediction import router as create_router

__all__ = ["menu_router", "create_router"]
