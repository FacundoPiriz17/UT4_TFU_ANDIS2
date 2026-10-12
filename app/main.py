import os
import socket
from fastapi import FastAPI, HTTPException

from app.routers import audit, auth, compras, juegos, personas

app = FastAPI(
    title="ADAII TFU3 - API de Juegos",
    version=os.getenv("API_VERSION", "dev"),
)

app.include_router(auth.router)
app.include_router(personas.router)
app.include_router(juegos.router)
app.include_router(compras.router)
app.include_router(audit.router)


@app.middleware("http")
async def identificar_instancia(request, call_next):
    response = await call_next(request)
    response.headers["X-Instance-ID"] = os.getenv("INSTANCE_NAME", socket.gethostname())
    return response


@app.get("/")
def root():
    return {
        "message": "API funcionando",
        "version": os.getenv("API_VERSION", "dev"),
    }


@app.get("/health")
def health():
    if os.getenv("FORCE_UNHEALTHY", "false").lower() == "true":
        raise HTTPException(
            status_code=503,
            detail="Version marcada como defectuosa para demostrar rollback",
        )

    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "version": os.getenv("API_VERSION", "dev"),
        "force_unhealthy": os.getenv("FORCE_UNHEALTHY", "false").lower() == "true",
    }
@app.get("/instance")
def instance():
    return {
        "instance": os.getenv("INSTANCE_NAME", socket.gethostname()),
        "version": os.getenv("API_VERSION", "dev"),
    }
