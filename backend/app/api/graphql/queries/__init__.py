"""GraphQL queries root."""

import strawberry
from app.api.graphql.queries import knowledge


@strawberry.type
class Query:
    """Root query type combining all query modules."""

    # Knowledge queries
    knowledge_modules = knowledge.knowledge_modules
    knowledge_module = knowledge.knowledge_module
