from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.config import POSTGRES_URL

sync_conninfo = f"postgresql+psycopg2://{POSTGRES_URL}"
async_conninfo = f"postgresql+asyncpg://{POSTGRES_URL}"

pool_size = 10
pool_timeout = 30
max_overflow = 5
pool_recycle = 1800
pool_pre_ping = True
echo = False

sync_engine = create_engine(
    sync_conninfo,
    pool_size=pool_size,
    pool_timeout=pool_timeout,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_pre_ping=pool_pre_ping,
    echo=echo,
)

async_engine = create_async_engine(
    async_conninfo,
    pool_size=pool_size,
    pool_timeout=pool_timeout,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_pre_ping=pool_pre_ping,
    echo=echo,
)

SyncSessionFactory = sessionmaker(bind=sync_engine, expire_on_commit=False)
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# For dependency injection in FastAPI
async def get_async_session():
    async with AsyncSessionFactory() as session:
        yield session