"""GraphQL mutations root."""

import strawberry
from app.api.graphql.mutations import knowledge


@strawberry.type
class Mutation:
    """Root mutation type combining all mutation modules."""

    # Knowledge mutations
    add_knowledge_module = knowledge.add_knowledge_module
    update_knowledge_module = knowledge.update_knowledge_module
    delete_knowledge_module = knowledge.delete_knowledge_module
