from typing import List, Optional, Dict, Literal
from datetime import datetime

from pydantic import create_model, BaseModel, Field, PrivateAttr, Json

from .utils import camel_generator

import json


class _AWSResponseModel(BaseModel):
    class Config:
        alias_generator = camel_generator


class _SchemaCreateUpdateModel(_AWSResponseModel):
    description: Optional[str]
    last_modified: datetime
    schema_arn: str
    schema_name: str
    schema_version: str
    tags: Dict[str, str]
    type_: Literal["OpenApi3", "JSONSchemaDraft4"] = Field(..., alias="Type")
    version_created_date: datetime


class _SchemaContentModel(_SchemaCreateUpdateModel):
    content: str
    _content: dict = PrivateAttr({})

    @property
    def content_dict(self):
        if not self._content:
            self._content = json.loads(self.content)

        return self._content


class _SchemaVersionModel(_AWSResponseModel):
    schema_arn: str
    schema_name: str
    schema_version: str
    type_: Literal["OpenApi3", "JSONSchemaDraft4"] = Field(..., alias="Type")


class _SchemaModel(_AWSResponseModel):
    last_modified: datetime
    schema_arn: str
    schema_name: str
    tags: Dict[str, str]
    version_count: int


class _SchemaVersionsPageModel(_AWSResponseModel):
    schema_versions: List[_SchemaVersionModel]


class _SchemaPageModel(_AWSResponseModel):
    schemas: List[_SchemaModel]


class Event(BaseModel):
    event_version: str = Field(..., alias="version")
    id: str

    detail_type: str = Field(..., alias="detail-type")
    detail: dict
    source: str

    account: str
    region: str

    time: datetime
    resources: List[str]

    @property
    def schema_registry(self) -> str:
        return self.detail_type.split("/", 1)[0]

    @property
    def schema_version(self) -> str:
        return self.detail_type.split(":")[1]

    @property
    def schema_name(self) -> str:
        return self.detail_type.split("/")[1].split(":")[0]
