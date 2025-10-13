from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.models.user import User


@dataclass
class GraphQLContext:
    """Context passed to all GraphQL resolvers."""

    request: Request
    db: AsyncSession
    current_user: User | None = None
