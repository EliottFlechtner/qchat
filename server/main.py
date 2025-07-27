from fastapi import FastAPI
from server.routes import router, register_user
from shared.models import RegisterRequest

app = FastAPI(title="Post-Quantum Chat Server")
app.include_router(router)
