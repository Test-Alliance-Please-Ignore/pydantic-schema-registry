import boto3

from schema_registry import SchemaRegistry, Schema, SchemaReflector
from devtools import debug


def test_loading_schemas():
    registry = SchemaRegistry("TAPI-TEST")
    schema: Schema = registry._schemas["schema_registry.test.TestingModel"]
    debug(schema.get())
    reflector: SchemaReflector = schema.reflect()
    model = reflector.create_model_for_jsonschema()
    debug(model.__fields__)
    instance = model(name="ozzeh", description="big willy johnston")
    registry.register_model("schema_registry.test", model)
    registry.send_event("auth-dev", "com.pleaseignore.tvm.test", instance)
