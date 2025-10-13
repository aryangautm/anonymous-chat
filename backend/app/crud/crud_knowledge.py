from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeModule, KnowledgeChunk
from app.schemas.knowledge import KnowledgeModuleCreate, KnowledgeModuleUpdate


class CRUDKnowledgeModule:
    """CRUD operations for knowledge modules."""

    async def create(
        self, db: AsyncSession, persona_id: UUID, obj_in: KnowledgeModuleCreate
    ) -> KnowledgeModule:
        """Create new knowledge module."""
        db_obj = KnowledgeModule(
            persona_id=persona_id,
            module_type=obj_in.module_type,
            title=obj_in.title,
            content=obj_in.content,
            priority=obj_in.priority,
            is_active=obj_in.is_active,
            metadata=obj_in.metadata,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, module_id: UUID) -> Optional[KnowledgeModule]:
        """Get knowledge module by ID."""
        stmt = select(KnowledgeModule).where(KnowledgeModule.id == module_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_persona(
        self, db: AsyncSession, persona_id: UUID, include_inactive: bool = False
    ) -> List[KnowledgeModule]:
        """Get all knowledge modules for a persona."""
        conditions = [KnowledgeModule.persona_id == persona_id]
        if not include_inactive:
            conditions.append(KnowledgeModule.is_active == True)

        stmt = (
            select(KnowledgeModule)
            .where(and_(*conditions))
            .order_by(KnowledgeModule.priority.desc())
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, db: AsyncSession, module_id: UUID, obj_in: KnowledgeModuleUpdate
    ) -> Optional[KnowledgeModule]:
        """Update knowledge module."""
        db_obj = await self.get(db, module_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, module_id: UUID) -> bool:
        """Delete knowledge module."""
        db_obj = await self.get(db, module_id)
        if not db_obj:
            return False

        await db.delete(db_obj)
        await db.commit()
        return True


class CRUDKnowledgeChunk:
    """CRUD operations for knowledge chunks."""

    async def create_bulk(
        self, db: AsyncSession, module_id: UUID, chunks: List[dict]
    ) -> List[KnowledgeChunk]:
        """
        Create multiple chunks at once.

        Args:
            db: Database session
            module_id: Parent module ID
            chunks: List of chunk data dicts with keys:
                    'chunk_text', 'chunk_index', 'token_count', 'metadata'
        """
        db_objs = []
        for chunk_data in chunks:
            db_obj = KnowledgeChunk(
                module_id=module_id,
                chunk_text=chunk_data["chunk_text"],
                chunk_index=chunk_data["chunk_index"],
                embedding=None,  # Will be set later by background task
                token_count=chunk_data.get("token_count"),
                metadata=chunk_data.get("metadata"),
            )
            db_objs.append(db_obj)

        db.add_all(db_objs)
        await db.commit()

        for obj in db_objs:
            await db.refresh(obj)

        return db_objs

    async def update_embedding(
        self, db: AsyncSession, chunk_id: UUID, embedding: List[float]
    ) -> bool:
        """Update chunk embedding."""
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id)
        result = await db.execute(stmt)
        chunk = result.scalar_one_or_none()

        if not chunk:
            return False

        chunk.embedding = embedding
        await db.commit()
        return True

    async def get_by_module(
        self, db: AsyncSession, module_id: UUID
    ) -> List[KnowledgeChunk]:
        """Get all chunks for a module."""
        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.module_id == module_id)
            .order_by(KnowledgeChunk.chunk_index)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())


knowledge_module_crud = CRUDKnowledgeModule()
knowledge_chunk_crud = CRUDKnowledgeChunk()
