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
def complex_model():
    class Group(BaseModel):
        id: int
        name: str

    class ComplexModel(BaseModel):
        """Hi mom"""

        name: str
        description: Optional[str]
        groups: List[Group]

    yield ComplexModel


def test_load_named_schemas(test_model, named_registry):
    pass


def test_schema_registration(test_model, named_registry):
    schema_info = named_registry.register_model("com.pleaseignore.tvm.test", test_model)


def test_registered_model(test_model, named_registry):
    model_info = named_registry.schema_for_model(test_model)


def test_complex_mode(complex_model, named_registry):
    named_registry.register_model("com.pleaseignore.tvm.test", complex_model)


def test_send_simple_message(test_model, named_registry):
    instance = test_model(name="Test", description="Hello!")
    log.debug(instance)
    named_registry.send_event("auth-dev", "com.pleaseignore.tvm.test", instance)
