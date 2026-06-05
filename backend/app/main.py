from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import repository_router, graph_router, search_router, documentation_router

app = FastAPI(title="CodeAtlas Repository Intelligence Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router.router, prefix="/api/v1")
app.include_router(graph_router.router, prefix="/api/v1")
app.include_router(search_router.router, prefix="/api/v1")
app.include_router(documentation_router.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeAtlas API"}
