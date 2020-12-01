from typing import Optional, List
from pydantic import BaseModel, create_model, Field, PrivateAttr
from devtools import debug
from jsonpointer import resolve_pointer

from schema_registry.models import Event
from schema_registry.client import SchemaRegistry


def reflect_event(event_dict: dict) -> BaseModel:
    event: Event = Event.parse_obj(event_dict)

    registry: SchemaRegistry = SchemaRegistry(event.schema_registry)
    schema = registry.get_schema(event.schema_name)
    version = schema.get(version=event.schema_version)
    reflector = SchemaReflector(version.content_dict)
    model = reflector.create_model_for_jsonschema()
    setattr(model, "__detail_type__", event_dict.get("detail-type"))
    return model.parse_obj(event_dict.get("detail"))


class _ReflectedModel(BaseModel):
    __detail_type__: str = PrivateAttr()

    @property
    def detail_type(self) -> Optional[str]:
        return self.__detail_type__ or None

    class Config:
        alias_generator = lambda x: "fields_" if x == "fields" else x


class SchemaReflector:
    def __init__(self, schema, registry=None):
        self.schema = schema
        self.fields = {}
        self.references = {}
        self.definitions = {}
        self.registry = registry

    def _resolve_reference(self, ref_value):
        if ref_value.startswith("#"):
            return resolve_pointer(self.__dict__, ref_value.split("#")[1])

        raise TypeError(
            "Cannot resolve a reference that's not a json pointer. (Reference value {})".format(
                ref_value
            )
        )

    def _resolve_array(self, property_info, required) -> tuple:
        items = property_info.get("items")
        item_type, item_value = next(iter(items.items()))

        if item_type == "$ref":
            referenced_type = self._resolve_reference(item_value)
            return (referenced_type, ... if required else None)

        raise NotImplementedError("Cannot reflect type: {}".format(item_type))

    def _resolve_property(self, name, property_info, required=True) -> tuple:
        if "type" in property_info:
            type_ = property_info.get("type")

            if type_ == "string":
                return (str, ... if required else None)

            elif type_ == "boolean":
                return (bool, ... if required else None)

            elif type_ in ("number", "integer"):
                return (int, ... if required else None)

            elif type_ == "array":
                return self._resolve_array(property_info, required)
        else:
            if "$ref" in property_info:
                return (
                    self._resolve_reference(property_info["$ref"]),
                    ... if required else None,
                )

        raise NotImplementedError(f"Not able to reflect the type: {property_info}")

    def _resolve_properties(self):
        if "properties" not in self.schema:
            raise TypeError("No properties are defined for this schema")

        required_fields = self.schema.get("required")

        for name, info in self.schema.get("properties").items():
            self.fields[name] = self._resolve_property(
                name, info, required=name in required_fields
            )

    def _resolve_definition(self, d_name, d_info):
        if d_info["type"] != "object":
            raise TypeError("Cannot reflect a non-object")

        model = SchemaReflector(d_info).create_model_for_jsonschema()
        self.references[d_name] = model
        self.definitions[d_name] = model

    def create_model_for_jsonschema(self):
        if "title" not in self.schema:
            raise TypeError("Schema needs a title field")

        if "type" not in self.schema:
            raise TypeError("Schema needs a type field")

        self.root_model_name = self.schema.get("title")

        if "definitions" in self.schema:
            for name, d_info in self.schema.get("definitions").items():
                self._resolve_definition(name, d_info)

        self._resolve_properties()

        return create_model(
            self.root_model_name, __base__=_ReflectedModel, **self.fields
        )
