import asyncio

from fastapi import FastAPI

from films import main as main_module


class FakeEngine:
    def __init__(self) -> None:
        self.disposed = False

    async def dispose(self) -> None:
        self.disposed = True


def test_lifespan_exposes_mongo_database_and_disposes_resources(monkeypatch) -> None:
    fake_engine = FakeEngine()
    closed = []

    async def fake_connect_mongo():
        return None

    monkeypatch.setattr(main_module, "engine", fake_engine)
    monkeypatch.setattr(main_module, "connect_mongo", fake_connect_mongo)
    monkeypatch.setattr(main_module, "close_mongo", closed.append)

    async def run_lifespan() -> None:
        test_app = FastAPI()
        async with main_module.lifespan(test_app):
            assert test_app.state.mongo_db is None

    asyncio.run(run_lifespan())

    assert closed == [None]
    assert fake_engine.disposed is True
