from typing import Optional

import pytest
import boto3

from typing import List
from schema_registry import SchemaRegistry
from pydantic import BaseModel

import logging

from devtools import debug

logging.basicConfig()
log = logging.getLogger("schema_registry")
log.setLevel(logging.WARNING)
log.propagate = True


@pytest.fixture(scope="module")
def named_registry():
    _registry = SchemaRegistry(registry_name="TAPI-TEST")
    yield _registry


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
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
            }
        },
    }
    yield item


@pytest.fixture(scope="module")
def reflected_simple_model(simple_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(simple_model).create_model_for_jsonschema()
    debug(model.__fields__)
    named_registry.register_model("com.pleaseignore.tvm.test", model)
    yield model


@pytest.fixture(scope="module")
def reflected_complex_model(complex_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(complex_model).create_model_for_jsonschema()
    debug(model.__fields__)
    named_registry.register_model("com.pleaseignore.tvm.test", model)
    yield model


@pytest.fixture(scope="module")
def reflected_complex_referenced_model(complex_referenced_model, named_registry):
    from schema_registry.reflection import SchemaReflector

    model = SchemaReflector(complex_referenced_model).create_model_for_jsonschema()
    debug(model.__fields__)
    named_registry.register_model("com.pleaseignore.tvm.test", model)
    yield model


def test_simple_reflection(reflected_simple_model):
    pass


def test_complex_reflection(reflected_complex_model):
    pass

def test_complex_referenced_model_reflection(reflected_complex_referenced_model):
    pass



def test_simple_reflection_registration(reflected_simple_model, named_registry):
    debug(named_registry.schema_for_model(reflected_simple_model))
