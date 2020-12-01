import boto3

from schema_registry import SchemaRegistry, Schema, SchemaReflector
from devtools import debug


def test_loading_schemas():
    registry = SchemaRegistry("TAPI-TEST")
    schema: Schema = registry._schemas["schema_registry.test.TestingModel"]
    debug(schema.get())
    reflector: SchemaReflector = SchemaReflector(schema.get().content_dict)
