from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from strawberry.fastapi import BaseContext

from app.models.user import User


class GraphQLContext(BaseContext):
    """Context passed to all GraphQL resolvers."""

    def __init__(
        self,
        request: Request,
        db: AsyncSession,
        current_user: User | None = None,
    ):
        super().__init__()
        self.request = request
        self.db = db
        self.current_user = current_user
