from typing import Optional
import json

import pytest
import boto3


from typing import List
from schema_registry import SchemaRegistry, Event, reflect_event
from pydantic import BaseModel

import logging

from devtools import debug

logging.basicConfig()
log = logging.getLogger("schema_registry")
log.setLevel(logging.WARNING)
log.propagate = True


@pytest.fixture(scope="session")
def named_registry():
    _registry = SchemaRegistry(registry_name="TAPI-TEST")
    yield _registry


@pytest.fixture(scope="session")
def empty_model():
    item = {"title": "RoleAddedEvent", "type": "object", "properties": {}}
    yield item


@pytest.fixture(scope="session")
def simple_model():
    item = {
        "title": "TestingModel",
        "type": "object",
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "description": {"title": "Description", "type": "string"},
        },
        "required": ["name"],
    }
    return item


@pytest.fixture(scope="session")
def complex_model():
    item = {
        "title": "ComplexModel",
        "description": "Hi mom",
        "type": "object",
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "description": {"title": "Description", "type": "string"},
            "groups": {
                "title": "Groups",
                "type": "array",
                "items": {"$ref": "#/definitions/Group"},
            },
        },
        "required": ["name", "groups"],
        "definitions": {
            "Group": {
                "title": "Group",
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["id", "name"],
            }
        },
    }
    yield item


@pytest.fixture(scope="session")
def complex_model_blank_array():
    item = {
        "title": "ComplexModel",
        "description": "Hi mom",
        "type": "object",
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "description": {"title": "Description", "type": "string"},
            "groups": {
                "title": "Groups",
                "type": "array",
                "items": {},
            },
        },
        "required": ["name", "groups"],
        "definitions": {
            "Group": {
                "title": "Group",
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["id", "name"],
            }
        },
    }
    yield item


@pytest.fixture(scope="session")
def complex_referenced_model():
    item = {
        "title": "ComplexReferencedModel",
        "description": "Hi mom",
        "type": "object",
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "description": {"title": "Description", "type": "string"},
            "group": {"$ref": "#/definitions/ReferencedGroup"},
        },
        "required": ["name", "group"],
        "definitions": {
            "ReferencedGroup": {
                "title": "ReferencedGroup",
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["id", "name"],
            },
            "ReferencedGroup2": {
                "title": "ReferencedGroup2",
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["id", "name"],
            },
        },
    }
    yield item


@pytest.fixture(scope="session")
def reflected_empty_model(empty_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(empty_model).create_model_for_jsonschema()
    named_registry.register_model("com.pleaseignore.tvm.test.reflection", model)
    yield model


@pytest.fixture(scope="session")
def reflected_simple_model(simple_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(simple_model).create_model_for_jsonschema()
    named_registry.register_model("com.pleaseignore.tvm.test.reflection", model)
    yield model


@pytest.fixture(scope="session")
def reflected_complex_model(complex_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(complex_model).create_model_for_jsonschema()
    named_registry.register_model("com.pleaseignore.tvm.test.reflection", model)
    yield model


@pytest.fixture(scope="session")
def reflected_complex_model_blank_array(complex_model_blank_array, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(complex_model_blank_array).create_model_for_jsonschema()
    named_registry.register_model("com.pleaseignore.tvm.test.reflection", model)
    yield model


@pytest.fixture(scope="session")
def reflected_complex_referenced_model(complex_referenced_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(complex_referenced_model).create_model_for_jsonschema()
    named_registry.register_model("com.pleaseignore.tvm.test.reflection", model)
    yield model


def test_empty_reflection(reflected_empty_model):
    pass


def test_simple_reflection(reflected_simple_model):
    pass


def test_complex_reflection(reflected_complex_model):
    pass


def test_complex_referenced_model_reflection(reflected_complex_referenced_model):
    pass


def test_simple_reflection_registration(reflected_simple_model, named_registry):
    named_registry.schema_for_model(reflected_simple_model)


def test_event_reflection():
    event_json = '{"version": "0", "id": "d944d595-b186-4b86-43fe-b096d7e13bb3", "detail-type": "TAPI-TEST/schema_registry.test.TestingModel:1", "source": "com.pleaseignore.tvm.test", "account": "740218546536", "time": "2020-11-27T16:53:00Z", "region": "eu-west-1", "resources": ["pydantic-schema-registry"], "detail": {"name": "ozzeh", "description": "big willy johnston"}}'
    event = Event.parse_raw(event_json)
    model = reflect_event(json.loads(event_json))



def test_notification_reflection():
    event_data = {
        "version": "0",
        "id": "044c0eb6-c449-c274-b0a6-45474db730f8",
        "detail-type": "TAPI/auth.notifications.StructureFuelAlert:1",
        "source": "com.pleaseignore.auth",
        "account": "740218546536",
        "time": "2020-12-21T20:34:26Z",
        "region": "eu-west-1",
        "resources": [
            "pydantic-schema-registry",
        ],
        "detail": {
            "is_read": None,
            "notification_id": 1352212309,
            "sender_id": 1000137,
            "sender_type": "corporation",
            "timestamp": "2020-12-21T19:52:00+00:00",
            "type": "StructureFuelAlert",
            "listOfTypesAndQty": [
                [
                    308,
                    4247,
                ],
            ],
            "solarsystemID": 30003146,
            "structureID": 1025844785540,
            "structureShowInfoData": [
                "showinfo",
                35835,
                1025844785540,
            ],
            "structureTypeID": 35835,
        },
    }
    model = reflect_event(event_data)