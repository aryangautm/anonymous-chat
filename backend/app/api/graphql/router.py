"""GraphQL router for FastAPI."""

from fastapi import Request, Depends
from strawberry.fastapi import GraphQLRouter as StrawberryGraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.graphql.schema import schema
from app.api.graphql.context import GraphQLContext
from app.api.deps import get_db, get_current_user_optional
from app.models.user import User


async def get_graphql_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> GraphQLContext:
    """Create GraphQL context with dependencies."""
    return GraphQLContext(request=request, db=db, current_user=current_user)


# Create the GraphQL router
graphql_router = StrawberryGraphQLRouter(
    schema, context_getter=get_graphql_context, path="/graphql"
)
