"""
Database query helpers for soft delete functionality
"""
from typing import TypeVar, Type, Optional, List
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.base import Base, SoftDeleteMixin

T = TypeVar('T', bound=Base)


class QueryBuilder:
    """Helper class for building queries with soft delete support"""

    @staticmethod
    def active_only(query: Select, model: Type[SoftDeleteMixin]) -> Select:
        """
        Filter query to exclude soft-deleted records

        Args:
            query: SQLAlchemy select query
            model: Model class with SoftDeleteMixin

        Returns:
            Modified query excluding deleted records
        """
        return query.where(model.deleted_at.is_(None))

    @staticmethod
    def deleted_only(query: Select, model: Type[SoftDeleteMixin]) -> Select:
        """
        Filter query to include only soft-deleted records

        Args:
            query: SQLAlchemy select query
            model: Model class with SoftDeleteMixin

        Returns:
            Modified query including only deleted records
        """
        return query.where(model.deleted_at.isnot(None))

    @staticmethod
    def include_deleted(query: Select) -> Select:
        """
        Return query as-is (includes both active and deleted)

        Args:
            query: SQLAlchemy select query

        Returns:
            Unmodified query
        """
        return query


class SoftDeleteRepository:
    """Generic repository with soft delete support"""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
        self.has_soft_delete = issubclass(model, SoftDeleteMixin)

    async def get_by_id(
        self,
        id: UUID,
        include_deleted: bool = False
    ) -> Optional[T]:
        """
        Get record by ID

        Args:
            id: Record UUID
            include_deleted: Whether to include soft-deleted records

        Returns:
            Record if found, None otherwise
        """
        query = select(self.model).where(self.model.id == id)

        if self.has_soft_delete and not include_deleted:
            query = QueryBuilder.active_only(query, self.model)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all records

        Args:
            include_deleted: Whether to include soft-deleted records
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of records
        """
        query = select(self.model)

        if self.has_soft_delete and not include_deleted:
            query = QueryBuilder.active_only(query, self.model)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, id: UUID) -> bool:
        """
        Soft delete a record

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found or already deleted
        """
        if not self.has_soft_delete:
            raise ValueError(f"{self.model.__name__} does not support soft delete")

        record = await self.get_by_id(id, include_deleted=False)
        if not record:
            return False

        record.soft_delete()
        await self.session.commit()
        return True

    async def restore(self, id: UUID) -> bool:
        """
        Restore a soft-deleted record

        Args:
            id: Record UUID

        Returns:
            True if restored, False if not found or not deleted
        """
        if not self.has_soft_delete:
            raise ValueError(f"{self.model.__name__} does not support soft delete")

        record = await self.get_by_id(id, include_deleted=True)
        if not record or not record.is_deleted:
            return False

        record.restore()
        await self.session.commit()
        return True

    async def hard_delete(self, id: UUID) -> bool:
        """
        Permanently delete a record

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        record = await self.get_by_id(id, include_deleted=True)
        if not record:
            return False

        await self.session.delete(record)
        await self.session.commit()
        return True

    async def count(self, include_deleted: bool = False) -> int:
        """
        Count records

        Args:
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        if self.has_soft_delete and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar() or 0


# Usage examples in comments
"""
Example usage:

from app.db.conn import get_session
from app.models import User, Client
from app.db.helpers import SoftDeleteRepository

async def example_usage():
    async with get_session() as session:
        # Create repository
        user_repo = SoftDeleteRepository(session, User)

        # Get active user
        user = await user_repo.get_by_id(user_id)

        # Get all users (active only)
        users = await user_repo.get_all()

        # Get all users including deleted
        all_users = await user_repo.get_all(include_deleted=True)

        # Soft delete
        deleted = await user_repo.soft_delete(user_id)

        # Restore
        restored = await user_repo.restore(user_id)

        # Hard delete (permanent)
        hard_deleted = await user_repo.hard_delete(user_id)

        # Count active users
        count = await user_repo.count()

        # Count all users including deleted
        total_count = await user_repo.count(include_deleted=True)
"""
