from dataclasses import dataclass
from .Geometry import Geometry
from uuid import UUID


@dataclass(frozen=True)
class Room:
    sign: str
    outputs: list[UUID]
    id: UUID
    name: str
    area: float
    sizeZ: float
    zLevel: float
    xy: list[Geometry]

    # def __init__(
    #     self,
    #     sign: str,
    #     outputs: list[UUID],
    #     id: UUID,
    #     name: str,
    #     area: float,
    #     sizeZ: float,
    #     zLevel: float,
    #     xy: list[Geometry],
    # ):
    #     self.sign = sign
    #     self.outputs = outputs
    #     self.id = id
    #     self.name = name
    #     self.area = area
    #     self.sizeZ = sizeZ
    #     self.zLevel = zLevel
    #     self.xy = xy
