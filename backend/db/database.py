import os
import ssl
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Convert postgres:// → postgresql+asyncpg://
ASYNC_URL = (
    DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("postgres://", "postgresql+asyncpg://")
)

# asyncpg does not accept 'sslmode' as a query param — strip it and use connect_args
parsed = urlparse(ASYNC_URL)
params = parse_qs(parsed.query, keep_blank_values=True)
ssl_mode = params.pop("sslmode", ["disable"])[0]
new_query = urlencode({k: v[0] for k, v in params.items()})
ASYNC_URL = urlunparse(parsed._replace(query=new_query))

connect_args: dict = {}
if ssl_mode in ("require", "verify-ca", "verify-full"):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_ctx

engine = create_async_engine(ASYNC_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
