from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from core.config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_ECHO
from database.models import Base

engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Initializes the database by creating all defined tables.
# Args: None
# Returns: None
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

