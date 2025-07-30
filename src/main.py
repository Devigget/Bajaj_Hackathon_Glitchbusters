from fastapi import FastAPI
from src.api.hackrx import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# More specific CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        "http://localhost:8000",  # Same origin
        "http://127.0.0.1:8000",  # Same origin
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(router)
