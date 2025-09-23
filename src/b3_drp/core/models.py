"""Pydantic models for config and matdb validation."""

from pydantic import BaseModel, RootModel
from typing import List, Dict, Optional, Union


class Datum(BaseModel):
    base: str
    values: List[List[float]]


class Condition(BaseModel):
    field: str
    operator: str
    operand: Union[float, str, List[float]]


class Ply(BaseModel):
    mat: str
    angle: float
    thickness: Union[float, str]
    parent: str
    conditions: List[Condition]
    key: int


class Config(BaseModel):
    datums: Optional[Dict[str, Datum]] = {}
    plies: List[Ply]


class Material(BaseModel):
    id: int
    # Add other fields if needed


class MatDB(RootModel[Dict[str, Material]]):
    pass
