import strawberry
from app.api.graphql.scalars import UUID, DateTime


@strawberry.type
class KnowledgeModuleType:
    """Knowledge module GraphQL type."""

    id: UUID
    persona_id: UUID
    module_type: str
    title: str | None
    content: strawberry.scalars.JSON
    priority: int
    is_active: bool
    metadata: strawberry.scalars.JSON | None
    created_at: DateTime
    updated_at: DateTime


@strawberry.input
class KnowledgeModuleInput:
    """Input for creating/updating knowledge module."""

    module_type: str
    title: str | None = None
    content: strawberry.scalars.JSON = strawberry.field(
        description="Module-specific content structure"
    )
    priority: int = 1
    is_active: bool = True
    metadata: strawberry.scalars.JSON | None = None
