import sqlalchemy
import asyncpg
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
import datetime
from sqlalchemy import BigInteger, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError, OperationalError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import Optional
from core.config import DATABASE_URL

class Base(DeclarativeBase):
    pass

class ServiceProvider(Base):
    __tablename__ = 'service_providers'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reviews: Mapped[list["Review"]] = relationship(back_populates="provider")

class Review(Base):
    __tablename__ = 'reviews'

    review_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("service_providers.user_id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_username: Mapped[str] = mapped_column(String, nullable=True)
    review_text: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    provider: Mapped["ServiceProvider"] = relationship(back_populates="reviews")


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=2,
    max_overflow=3
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Initializes the database by creating all defined tables.
# Args: None
# Returns: None
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)




# Adds a new service provider.
# Args: session (AsyncSession), provider_id (int), username (Optional[str]), display_name (str), category (str)
# Returns: ServiceProvider
async def add_service_provider(
    session: AsyncSession,
    provider_id: int,
    username: Optional[str],
    display_name: str,
    category: str
) -> ServiceProvider:
    new_provider = ServiceProvider(
        user_id=provider_id,
        username=username,
        display_name=display_name,
        category=category
    )
    session.add(new_provider)
    
    try:
        await session.commit()
        return new_provider
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Provider with ID {provider_id} already exists.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost.")
    except Exception:
        await session.rollback()
        raise



# Retrieves active service providers filtered by category.
# Args: session (AsyncSession), category (str)
# Returns: list[ServiceProvider]
async def get_active_providers_by_category(
    session: AsyncSession,
    category: str
) -> list[ServiceProvider]:
    try:
        stmt = select(ServiceProvider).where(
            ServiceProvider.category.ilike(category), 
            ServiceProvider.is_active == True
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        raise ConnectionError("Database connection lost.")
    except Exception:
        raise



# Retrieves a single service provider by ID or username.
# Args: session (AsyncSession), user_id (Optional[int]), username (Optional[str])
# Returns: Optional[ServiceProvider]
async def get_service_provider(
    session: AsyncSession,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> Optional[ServiceProvider]:
    conditions = []
    if user_id is not None:
        conditions.append(ServiceProvider.user_id == user_id)
        
    if username is not None:
        conditions.append(ServiceProvider.username == username)
        
    if not conditions:
        return None
        
    try:
        stmt = select(ServiceProvider).where(or_(*conditions))
        result = await session.execute(stmt)
        return result.scalars().first()
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        raise ConnectionError("Database connection lost.")



# Updates the display name of a specific service provider.
# Args: session (AsyncSession), new_display_name (str), user_id (Optional[int]), username (Optional[str])
# Returns: bool (True if updated, False if provider not found)
async def update_provider_display_name(
    session: AsyncSession,
    new_display_name: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> bool:
    try:
        provider = await get_service_provider(session, user_id, username)
        if provider is None:
            return False
            
        provider.display_name = new_display_name
        await session.commit()
        return True
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost or transaction locked.")



# Updates the category of a specific service provider.
# Args: session (AsyncSession), new_category (str), user_id (Optional[int]), username (Optional[str])
# Returns: bool (True if updated, False if provider not found)
async def update_provider_category(
    session: AsyncSession,
    new_category: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> bool:
    try:
        provider = await get_service_provider(session, user_id, username)
        if provider is None:
            return False
            
        provider.category = new_category
        await session.commit()
        return True
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost or transaction locked.")



# Toggles the active status (is_active) of a service provider for soft deletion/restoration.
# Args: session (AsyncSession), user_id (Optional[int]), username (Optional[str])
# Returns: bool (True if updated, False if provider not found)
async def toggle_provider_active_status(
    session: AsyncSession,
    user_id: Optional[int] = None,
    username: Optional[str] = None
) -> bool:
    try:
        provider = await get_service_provider(session, user_id, username)
        if provider is None:
            return False
            
        provider.is_active = not provider.is_active
        await session.commit()
        return True
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost or transaction locked.")



# Adds a new review for a service provider with a default "PENDING" status.
# Args: session (AsyncSession), provider_id (int), sender_id (int), sender_username (Optional[str]), review_text (str)
# Returns: Review
async def add_review(
    session: AsyncSession,
    provider_id: int,
    sender_id: int,
    sender_username: Optional[str],
    review_text: str
) -> Review:
    new_review = Review(
        provider_id=provider_id,
        sender_id=sender_id,
        sender_username=sender_username,
        review_text=review_text
    )
    session.add(new_review)
    
    try:
        await session.commit()
        return new_review
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Provider with ID {provider_id} does not exist or invalid data provided.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost.")



# Retrieves all approved reviews for a specific service provider.
# Args: session (AsyncSession), provider_id (int)
# Returns: list[Review]
async def get_approved_reviews(
    session: AsyncSession,
    provider_id: int
) -> list[Review]:
    try:
        stmt = select(Review).where(Review.provider_id == provider_id, Review.status == "APPROVED")
        result = await session.execute(stmt)
        return list(result.scalars().all())
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        raise ConnectionError("Database connection lost.")



# Retrieves the oldest review that is currently waiting for admin approval ("PENDING" status).
# Args: session (AsyncSession)
# Returns: Optional[Review]
async def get_oldest_pending_review(
    session: AsyncSession
) -> Optional[Review]:
    try:
        stmt = select(Review).where(Review.status == "PENDING").order_by(Review.created_at)
        result = await session.execute(stmt)
        return result.scalars().first()
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        raise ConnectionError("Database connection lost.")



# Updates the status of a specific review (e.g., to "APPROVED" or "REJECTED").
# Args: session (AsyncSession), review_id (int), new_status (str)
# Returns: bool (True if updated, False if review not found)
async def update_review_status(
    session: AsyncSession,
    review_id: int,
    new_status: str
) -> bool:
    try:
        stmt = select(Review).where(Review.review_id == review_id)
        result = await session.execute(stmt)
        review = result.scalars().first()
        
        if review is None:
            return False
            
        review.status = new_status
        await session.commit()
        return True
    except PendingRollbackError:
        await session.rollback()
        raise RuntimeError("Session state is invalid. Rollback executed.")
    except OperationalError:
        await session.rollback()
        raise ConnectionError("Database connection lost or transaction locked.")
