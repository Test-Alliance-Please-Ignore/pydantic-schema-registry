from typing import Optional

import pytest
import boto3

from typing import List
from schema_registry import SchemaRegistry
from pydantic import BaseModel

import logging

logging.basicConfig()
log = logging.getLogger("schema_registry")
log.setLevel(logging.DEBUG)
log.propagate = True


@pytest.fixture(scope="module")
def named_registry():
    _registry = SchemaRegistry(registry_name="TAPI-TEST")
    yield _registry


@pytest.fixture(scope="module")
def dynamic_registry():
    _registry = SchemaRegistry()
    yield _registry


@pytest.fixture(scope="module")
def test_model():
    class TestingModel(BaseModel):
        name: str
        description: Optional[str]

    yield TestingModel


@pytest.fixture(scope="module")
def nullable_model():
    class NullableModel(BaseModel):
        name: str
        description: Optional[str] = None

    yield NullableModel


@pytest.fixture(scope="module")
def complex_model():
    class Group(BaseModel):
        id: int
        name: str

    class ComplexModel(BaseModel):
        name: str
        description: Optional[str]
        groups: List[Group]

    yield ComplexModel


@pytest.fixture(scope="module")
def complex_model_with_references():
    class ReferencedGroup(BaseModel):
        id: int
        name: str

    class ComplexReferencedModel(BaseModel):

        name: str
        description: Optional[str]
        group: ReferencedGroup

    yield ComplexReferencedModel


def test_load_named_schemas(test_model, named_registry):
    pass


def test_schema_registration(test_model, named_registry):
    schema_info = named_registry.register_model("schema_registry.test", test_model)


def test_registered_model(test_model, named_registry):
    model_info = named_registry.schema_for_model(test_model)


def test_complex_model(complex_model, named_registry):
    named_registry.register_model("schema_registry.test", complex_model)


def test_nullable_model(nullable_model, named_registry):
    named_registry.register_model("schema_registry.test", nullable_model)


def test_complex_model_with_references(complex_model_with_references, named_registry):
    named_registry.register_model("schema_registry.test", complex_model_with_references)


def test_send_simple_message(test_model, named_registry):
    instance = test_model(name="Test", description="Hello!")
    log.debug(instance)
    named_registry.send_event("auth-dev", "schema_registry.test", instance)
