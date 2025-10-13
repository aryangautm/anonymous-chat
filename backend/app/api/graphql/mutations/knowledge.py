import strawberry
from sqlalchemy import select

from app.api.graphql.context import GraphQLContext
from app.api.graphql.types.knowledge import KnowledgeModuleType, KnowledgeModuleInput
from app.api.graphql.scalars import UUID as UUIDScalar
from app.crud.crud_knowledge import knowledge_module_crud
from app.schemas.knowledge import KnowledgeModuleCreate, KnowledgeModuleUpdate
from app.models.persona import Persona

# from app.tasks.knowledge_tasks import process_knowledge_module_task


@strawberry.mutation
async def add_knowledge_module(
    info: strawberry.Info[GraphQLContext],
    persona_id: UUIDScalar,
    input: KnowledgeModuleInput,
) -> KnowledgeModuleType:
    """Add a knowledge module to a persona."""
    # Verify ownership first
    stmt = select(Persona).where(Persona.id == persona_id)
    result = await info.context.db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise ValueError("Persona not found")

    if not info.context.current_user:
        raise PermissionError("Authentication required")

    if persona.user_id != info.context.current_user.id:
        raise PermissionError("Access denied")

    # Convert GraphQL input to Pydantic schema
    module_create = KnowledgeModuleCreate(
        module_type=input.module_type,
        title=input.title,
        content=input.content,
        priority=input.priority,
        is_active=input.is_active,
        metadata=input.metadata,
    )

    # Create module using CRUD
    module = await knowledge_module_crud.create(
        db=info.context.db, persona_id=persona_id, obj_in=module_create
    )

    # TODO: celery
    # Queue background task to process and generate embeddings
    # process_knowledge_module_task.delay(str(module.id))

    return KnowledgeModuleType(
        id=module.id,
        persona_id=module.persona_id,
        module_type=module.module_type,
        title=module.title,
        content=module.content,
        priority=module.priority,
        is_active=module.is_active,
        metadata=module.module_metadata,  # Note: model uses module_metadata
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@strawberry.mutation
async def update_knowledge_module(
    info: strawberry.Info[GraphQLContext],
    module_id: UUIDScalar,
    input: KnowledgeModuleInput,
) -> KnowledgeModuleType:
    """Update a knowledge module."""
    # First get the module to verify ownership
    module = await knowledge_module_crud.get(db=info.context.db, module_id=module_id)

    if not module:
        raise ValueError("Module not found")

    # Verify ownership
    stmt = select(Persona).where(Persona.id == module.persona_id)
    result = await info.context.db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise ValueError("Persona not found")

    if not info.context.current_user:
        raise PermissionError("Authentication required")

    if persona.user_id != info.context.current_user.id:
        raise PermissionError("Access denied")

    # Convert GraphQL input to Pydantic schema
    module_update = KnowledgeModuleUpdate(
        module_type=input.module_type,
        title=input.title,
        content=input.content,
        priority=input.priority,
        is_active=input.is_active,
        metadata=input.metadata,
    )

    # Update module
    updated_module = await knowledge_module_crud.update(
        db=info.context.db, module_id=module_id, obj_in=module_update
    )

    if not updated_module:
        raise ValueError("Failed to update module")

    # TODO: celery
    # Re-process if content changed
    # if input.content:
    # process_knowledge_module_task.delay(str(module.id))

    return KnowledgeModuleType(
        id=updated_module.id,
        persona_id=updated_module.persona_id,
        module_type=updated_module.module_type,
        title=updated_module.title,
        content=updated_module.content,
        priority=updated_module.priority,
        is_active=updated_module.is_active,
        metadata=updated_module.module_metadata,
        created_at=updated_module.created_at,
        updated_at=updated_module.updated_at,
    )


@strawberry.mutation
async def delete_knowledge_module(
    info: strawberry.Info[GraphQLContext],
    module_id: UUIDScalar,
) -> bool:
    """Delete a knowledge module."""
    # First get the module to verify ownership
    module = await knowledge_module_crud.get(db=info.context.db, module_id=module_id)

    if not module:
        return False

    # Verify ownership
    stmt = select(Persona).where(Persona.id == module.persona_id)
    result = await info.context.db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        return False

    if not info.context.current_user:
        raise PermissionError("Authentication required")

    if persona.user_id != info.context.current_user.id:
        raise PermissionError("Access denied")

    # Delete module
    success = await knowledge_module_crud.delete(
        db=info.context.db, module_id=module_id
    )
    return success
