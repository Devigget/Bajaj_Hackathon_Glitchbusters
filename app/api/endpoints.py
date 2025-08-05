from fastapi import APIRouter
import sys
import os

# Add the parent directory to the path to import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.api.hackrx import router as hackrx_router

# Re-export the router from src for compatibility
router = hackrx_router
