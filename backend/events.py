from enum import Enum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel


class EventType(str, Enum):
    LOAD = "load"
    CLICK = "click"
    INPUT = "input"
    VULNERABILITY = "vulnerability"
    ERROR = "error"
    INFO = "info"


# Specific event detail classes
class LoadEventDetails(BaseModel):
    url: str


class ClickEventDetails(BaseModel):
    element: str


class InputEventDetails(BaseModel):
    field: str
    test_value: str


class Vulnerability(BaseModel):
    severity: str
    type: str
    title: str
    description: str


class GenericEventDetails(BaseModel):
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Union type for all possible event details
EventDetails = Union[
    LoadEventDetails,
    ClickEventDetails,
    InputEventDetails,
    Vulnerability,
    GenericEventDetails,
]
