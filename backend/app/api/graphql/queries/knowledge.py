"""GraphQL queries for knowledge modules."""

import strawberry
from typing import List
from sqlalchemy import select

from app.api.graphql.context import GraphQLContext
from app.api.graphql.types.knowledge import KnowledgeModuleType
from app.api.graphql.scalars import UUID
from app.models.persona import Persona
from app.crud.crud_knowledge import knowledge_module_crud


@strawberry.field
async def knowledge_modules(
    info: strawberry.Info[GraphQLContext],
    persona_id: UUID,
) -> List[KnowledgeModuleType]:
    """Get all knowledge modules for a persona."""
    # Verify ownership
    stmt = select(Persona).where(Persona.id == persona_id)
    result = await info.context.db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise ValueError("Persona not found")

    if not info.context.current_user:
        raise PermissionError("Authentication required")

    if persona.user_id != info.context.current_user.id:
        raise PermissionError("Access denied")

    # Fetch modules using CRUD
    modules = await knowledge_module_crud.get_by_persona(
        db=info.context.db,
        persona_id=persona_id,
        include_inactive=True,  # Owner can see inactive modules
    )

    # Convert to GraphQL types
    return [
        KnowledgeModuleType(
            id=m.id,
            persona_id=m.persona_id,
            module_type=m.module_type,
            title=m.title,
            content=m.content,
            priority=m.priority,
            is_active=m.is_active,
            metadata=m.module_metadata,  # Note: model uses module_metadata
            processing_status=m.processing_status.value,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in modules
    ]


@strawberry.field
async def knowledge_module(
    info: strawberry.Info[GraphQLContext],
    module_id: UUID,
) -> KnowledgeModuleType | None:
    """Get a single knowledge module by ID."""
    # Fetch module
    module = await knowledge_module_crud.get(db=info.context.db, module_id=module_id)

    if not module:
        return None

    # Verify ownership
    stmt = select(Persona).where(Persona.id == module.persona_id)
    result = await info.context.db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        return None

    if not info.context.current_user:
        raise PermissionError("Authentication required")

    if persona.user_id != info.context.current_user.id:
        raise PermissionError("Access denied")

    # Convert to GraphQL type
    return KnowledgeModuleType(
        id=module.id,
        persona_id=module.persona_id,
        module_type=module.module_type,
        title=module.title,
        content=module.content,
        priority=module.priority,
        is_active=module.is_active,
        metadata=module.module_metadata,
        processing_status=module.processing_status.value,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )
