import json
import sys
import logging
import json

from typing import List, Optional, Dict, Type
from datetime import datetime

import boto3

from pydantic import BaseModel

from devtools import debug

from schema_registry.models import (
    Event,
    _SchemaPageModel,
    _SchemaVersionsPageModel,
    _SchemaVersionModel,
    _SchemaContentModel,
    _SchemaCreateUpdateModel,
)

from schema_registry.errors import SchemaRegistryError, ModelNotRegisteredError

logger = logging.getLogger("schema_registry")


class Schema:
    def __init__(self, client, registry_name, schema_name):
        self.schema_client = client
        self.registry_name: str = registry_name
        self.schema_name = schema_name

        self._versions: Dict[str, _SchemaContentModel] = {}
        self.default_version: int = 0

        self._load_versions()

        self.default_version = sorted(self._versions.items(), reverse=True)[0][0]

    def _load_versions(self):
        paginator = self.schema_client.get_paginator("list_schema_versions")
        page_options = dict(
            RegistryName=self.registry_name, SchemaName=self.schema_name
        )
        for raw_page in paginator.paginate(**page_options):
            schema_versions: _SchemaVersionsPageModel = (
                _SchemaVersionsPageModel.parse_obj(raw_page)
            )
            for version in schema_versions.schema_versions:
                self._versions[
                    version.schema_version
                ] = self._get_schema_version_content(version)

    def _get_schema_version_content(
        self, schema_version: _SchemaVersionModel
    ) -> _SchemaContentModel:
        describe_opts = dict(
            RegistryName=self.registry_name,
            SchemaName=self.schema_name,
            SchemaVersion=schema_version.schema_version,
        )
        response = self.schema_client.describe_schema(**describe_opts)
        content: _SchemaContentModel = _SchemaContentModel.parse_obj(response)
        return content

    def get(self, version=None) -> _SchemaContentModel:
        if not version:
            return self._versions[self.default_version]
        else:
            return self._versions[version]

    def __repr__(self):
        return f"Schema<{self.schema_name}, versions: {len(self._versions)}, default version: {self.default_version}>"


class SchemaRegistry:
    standard_resources = [
        "pydantic-schema-registry",
    ]

    def __init__(
        self, registry_name: Optional[str] = None, *, prefix: str = None, **boto_opts
    ):
        self.registry_name: str = registry_name or "discovered-schemas"
        self.session = boto3.Session(**boto_opts)
        self.schema_client = self.session.client("schemas")
        self.prefix = prefix
        self._schemas: Dict[str, Schema] = {}
        self._model_schemas: Dict[Type[BaseModel], _SchemaCreateUpdateModel] = {}

    def load_schemas(self):
        paginator = self.schema_client.get_paginator("list_schemas")
        page_options = dict(RegistryName=self.registry_name)
        if self.prefix:
            page_options["SchemaNamePrefix"] = self.prefix

        for raw_page in paginator.paginate(**page_options):
            schema_page: _SchemaPageModel = _SchemaPageModel.parse_obj(raw_page)
            for schema in schema_page.schemas:
                self._schemas[schema.schema_name] = Schema(
                    self.schema_client, self.registry_name, schema.schema_name
                )

    def get_schema(self, name) -> Schema:
        schema = Schema(self.schema_client, self.registry_name, name)
        return schema

    def _get_schema_content_for_model(self, schema_name, model: Type[BaseModel]) -> _SchemaCreateUpdateModel:
        opts = dict(RegistryName=self.registry_name, SchemaName=schema_name)
        response = self.schema_client.describe_schema(**opts)
        schema_info = _SchemaCreateUpdateModel.parse_obj(response)
        self._model_schemas[model] = schema_info
        return schema_info 

    def _create_schema_for_model(self, schema_name: str, model: Type[BaseModel]):
        opts = dict(
            Content=model.schema_json(),
            RegistryName=self.registry_name,
            SchemaName=schema_name,
            Type="JSONSchemaDraft4",
        )
        response = self.schema_client.create_schema(**opts)
        schema_info = _SchemaCreateUpdateModel.parse_obj(response)
        self._model_schemas[model] = schema_info
        return schema_info

    def _update_schema_for_model(self, schema_name: str, model: Type[BaseModel]):
        opts = dict(
            Content=model.schema_json(),
            RegistryName=self.registry_name,
            SchemaName=schema_name,
            Type="JSONSchemaDraft4",
        )
        try:
            response = self.schema_client.update_schema(**opts)
            schema_info = _SchemaCreateUpdateModel.parse_obj(response)
            self._model_schemas[model] = schema_info
            return schema_info
        except self.schema_client.exceptions.ConflictException as e:
            return self._get_schema_content_for_model(schema_name, model)

    def _schema_exists(self, schema_name: str) -> bool:
        try:
            response = self.schema_client.describe_schema(
                RegistryName=self.registry_name, SchemaName=schema_name
            )
            return True
        except self.schema_client.exceptions.NotFoundException:
            return False
        except:
            raise

    def register_reflected_model(
        self, namespace, model: Type[BaseModel]
    ) -> _SchemaCreateUpdateModel:
        schema_name = "{}.{}".format(namespace, model.__name__)
        exists = self._schema_exists(schema_name)
        if not exists:
            schema = self._create_schema_for_model(schema_name, model)
        else:
            schema = self._update_schema_for_model(schema_name, model)

        return schema

    def register_model(
        self, namespace, model: Type[BaseModel]
    ) -> _SchemaCreateUpdateModel:
        schema_name = "{}.{}".format(namespace, model.__name__)

        schema_info = self.register_reflected_model(namespace, model)
        self._model_schemas[model] = schema_info

        return schema_info

    def schema_for_model(self, model: Type[BaseModel]) -> dict:
        if model not in self._model_schemas:
            raise ModelNotRegisteredError(model)

        return self._model_schemas[model].dict(
            include={"schema_arn", "schema_name", "schema_version"}
        )

    def send_event(
        self, event_bus, sender, model: BaseModel, extra_resources: List[str] = None
    ):
        cls = model.__class__

        if cls not in self._model_schemas:
            raise ValueError(
                f"Model {model.__class__.__name__} must be registered before it can be sent"
            )

        schema_info: _SchemaCreateUpdateModel = self._model_schemas[cls]

        resources = self.standard_resources
        if extra_resources:
            resources += extra_resources

        event_data = {
            "schema": schema_info.dict(
                include={"schema_arn", "schema_name", "schema_version"}
            ),
            "event": model.dict(by_alias=True),
        }

        detail_type_formatted = "{}:{}".format(
            event_data["schema"]["schema_arn"].split("/", 1)[1],
            event_data["schema"]["schema_version"],
        )

        entry = dict(
            Source=sender,
            Detail=model.json(by_alias=True),
            Resources=resources,
            DetailType=detail_type_formatted,
            EventBusName=event_bus,
        )
        response = self.session.client("events").put_events(
            Entries=[
                entry,
            ]
        )
