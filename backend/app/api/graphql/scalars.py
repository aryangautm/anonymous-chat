import strawberry
from uuid import UUID as PythonUUID
from datetime import datetime as PythonDatetime


UUID = strawberry.scalar(
    PythonUUID,
    serialize=lambda v: str(v),
    parse_value=lambda v: PythonUUID(v),
    description="UUID scalar type",
)

DateTime = strawberry.scalar(
    PythonDatetime,
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: PythonDatetime.fromisoformat(v),
    description="DateTime scalar type",
)
