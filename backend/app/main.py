from fastapi import FastAPI

from .routers import auth as auth_router
from .routers import journal as journal_router
from .store import JournalStore, create_seeded_store


def create_app(store: JournalStore | None = None) -> FastAPI:
    if store is None:
        store, demo_username, demo_password = create_seeded_store()
    else:
        demo_username = demo_password = None

    app = FastAPI(title="Weekly Growth Journal API", version="1.0.0")
    app.state.store = store
    app.state.demo_username = demo_username
    app.state.demo_password = demo_password

    app.include_router(auth_router.router, prefix="/api")
    app.include_router(journal_router.router, prefix="/api")
    return app


app = create_app()
