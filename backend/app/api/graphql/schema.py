import strawberry
from app.api.graphql.queries import Query
from app.api.graphql.mutations import Mutation


schema = strawberry.Schema(query=Query, mutation=Mutation)
