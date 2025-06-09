from ast import Delete
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from typing import Any, List


# ----------------------------
#  Data shapes
# ----------------------------
class TypeOfItem(str, Enum): # weird name becasue of confusion with `Item` type
    MOD = "mod"
    GROUP = "group"

    def __str__(self) -> str:  # keeps old behaviour
        return self.value

    @classmethod
    def from_str(cls, value: str) -> "TypeOfItem":
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Invalid TypeOfItem: {value}") from exc


# ------------------------- ModObject -------------------------
@dataclass
class ModObject:
    name: str
    enabled: bool = False
    path: List[str] = field(default_factory=list)
    date: int = 0  # Unix epoch seconds
    gb_id: str | None = None
    type: TypeOfItem = field(
        default=TypeOfItem.MOD,
        init=False,  # never passed by user
        repr=False,
    )

    # ---- collection protocol --------------------------------
    def __len__(self) -> int:
        return len(self.path)

    # ---- (de)serialisation ----------------------------------
    def to_dict(self) -> dict:
        data = asdict(self)
        data["type"] = self.type.value  # Enum  -> str
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ModObject":
        return cls(
            name=data["name"],
            enabled=data.get("enabled", False),
            path=list(data.get("path", [])),
            date=int(data.get("date", 0)),
            gb_id=data.get("gb_id"),
        )

    # Optional convenience wrappers around json.dumps/loads
    def to_json(self, **json_kw: Any) -> str:
        return json.dumps(self.to_dict(), **json_kw)

    @classmethod
    def from_json(cls, raw: str | bytes) -> "ModObject":
        return cls.from_dict(json.loads(raw))


# ------------------------ GroupObject ------------------------
@dataclass
class GroupObject:
    name: str
    enabled: bool = False
    members: List[ModObject] = field(default_factory=list)
    type: TypeOfItem = field(
        default=TypeOfItem.GROUP,
        init=False,
        repr=False,
    )

    # ---- collection protocol --------------------------------
    def __len__(self) -> int:
        return len(self.members)

    # ---- (de)serialisation ----------------------------------
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "enabled": self.enabled,
            "members": [m.to_dict() for m in self.members],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupObject":
        return cls(
            name=data["name"],
            enabled=data.get("enabled", False),
            members=[ModObject.from_dict(m) for m in data.get("members", [])],
        )

    def to_json(self, **json_kw: Any) -> str:
        return json.dumps(self.to_dict(), **json_kw)

    @classmethod
    def from_json(cls, raw: str | bytes) -> "GroupObject":
        return cls.from_dict(json.loads(raw))

type Item = ModObject | GroupObject  # Union of ModObject and GroupObject
type ModList = list[Item]  # List of ModObjects or GroupObjects


# ---------------------------- Mods Resources ----------------------------
@dataclass
class ModResource:
    thumb: list[str] = field(default_factory=list)  # List of image paths

    @classmethod
    def from_dict(cls, data: dict) -> "ModResource":
        return cls(
            thumb=list(data.get("thumb", [])),
        )

    def to_dict(self) -> dict:
        return {
            "thumb": self.thumb,
        }

type ModResources = dict[str, ModResource]  # Dict of mod name → ModResource

class Handler(Enum):
    """
    Enum for handler names.
    This is used to call the correct handler function from the Svelte frontend.
    """
    Rebuild = "rebuild_handler"


class Action(Enum):
    """
    Enum for possible actions when selecting a single mod or group or multiple mods. 
    This is used to call the correct action function from the Svelte frontend.
    """
    Rename = "rename"

    Delete = "delete"
    Toggle = "toggle"

    Enable = "enable" # toggle all enabled
    Disable = "disable" # toggle all disabled
    CreateGroup = "create_group"


    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)
    
    def __ne__(self, value: object) -> bool:
        return super().__ne__(value)
    
    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str) -> "Action":
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Invalid Action: {value}") from exc
        