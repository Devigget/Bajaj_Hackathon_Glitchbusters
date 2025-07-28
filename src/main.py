from fastapi import FastAPI
from src.api.hackrx import router

app = FastAPI()
app.include_router(router)
