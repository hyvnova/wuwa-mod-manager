#!/usr/bin/env python3
"""
bysex.py – *BiSex* builder
==========================
*Python → TypeScript types*

---

# This file is the type diplomat: it negotiates peace between Python and TypeScript,
# so your backend and frontend always speak the same language (and you never get bit by a type mismatch).

Usage reminder (unchanged)
```python
bisex = BiSex(py_types="bisextypes.py")
...
bisex.perform()  # (formerly .build())
```
"""


from __future__ import annotations

import ast
import inspect
import json
import types
from pathlib import Path
from typing import Any, Final, List, get_args, get_origin

from constants import WEBAPP_PATH

# -------------------------  PRIMITIVE MAP  -------------------------
# This is the Rosetta Stone: it translates Python primitives to TypeScript, so types always match.
PY_PRIMITIVE_TO_TS: Final[dict[str, str]] = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "NoneType": "null",
    "None": "null",
    "Any": "any",
}

# --------------------  AST‑LEVEL HELPERS  --------------------


def _map_primitive(name: str) -> str:
    # This is the universal translator: it maps Python type names to their TS equivalents.
    return PY_PRIMITIVE_TO_TS.get(name, name)


def _ts_from_ast(expr: ast.AST) -> str:
    """Translate a *type expression* (AST) into a TS type string."""
    # This function is the heart of the type wizardry: it recursively turns Python type ASTs into TS type strings.

    match expr:
        case ast.Name(id=name):
            return _map_primitive(name)

        case ast.BinOp(left=l, op=ast.BitOr(), right=r):  # A | B
            return f"{_ts_from_ast(l)} | {_ts_from_ast(r)}"

        # For < py3.9 where slice wrapped in ast.Index
        case ast.Index(value=v):  # type: ignore[attr-defined]
            return _ts_from_ast(v)

        # List[...] or typing.List[...]
        case ast.Subscript(value=ast.Name(id=("List" | "list")), slice=s):
            return f"({_ts_from_ast(s)})[]"
        case ast.Subscript(value=ast.Attribute(attr="List"), slice=s):
            return f"({_ts_from_ast(s)})[]"

        # Dict[K, V]
        case ast.Subscript(value=ast.Name(id=("Dict" | "dict")), slice=s):
            if isinstance(s, ast.Tuple) and len(s.elts) == 2:
                k, v = s.elts
            else:
                k = v = ast.Name(id="Any")
            return f"Record<{_ts_from_ast(k)}, {_ts_from_ast(v)}>"
        case ast.Subscript(value=ast.Attribute(attr="Dict"), slice=s):
            if isinstance(s, ast.Tuple) and len(s.elts) == 2:
                k, v = s.elts
            else:
                k = v = ast.Name(id="Any")
            return f"Record<{_ts_from_ast(k)}, {_ts_from_ast(v)}>"

        # typing.Union[A, B]
        case ast.Subscript(value=ast.Name(id="Union"), slice=ast.Tuple(elts=types_)):
            return " | ".join(_ts_from_ast(t) for t in types_)
        case ast.Subscript(
            value=ast.Attribute(attr="Union"), slice=ast.Tuple(elts=types_)
        ):
            return " | ".join(_ts_from_ast(t) for t in types_)

        case ast.Attribute(attr=attr):
            return _map_primitive(attr)

        case _:
            return "any"


# --------------------  RUNTIME‑ANNOTATION → TS  --------------------


def _anno_to_ts(anno: Any) -> str:
    """
    Translate a *runtime* annotation (or a simple name string) into
    a TypeScript type string.
    """
    # This is the runtime type whisperer: it figures out what a Python annotation means, and says it in TypeScript.
    # ---- simple cases --------------------------------------------------
    if isinstance(anno, str):  # bare name
        return _map_primitive(anno)

    if isinstance(anno, ast.Name):
        return _map_primitive(anno.id)

    # Type[Type]
    if isinstance(anno, ast.Subscript):
        return f"({_anno_to_ts(anno.slice)})[]"

    # Type | Type
    if isinstance(anno, ast.BinOp) and isinstance(anno.op, ast.BitOr):
        return f"{_anno_to_ts(anno.left)} | {_anno_to_ts(anno.right)}"

    # Constant
    if isinstance(anno, ast.Constant):
        return _anno_to_ts(anno.value)

    if anno is None or anno is type(None):  # noqa: E721
        return "null"
    if anno is inspect._empty:  # no annotation
        return "any"

    # ---- typing / PEP-604 unions --------------------------------------
    origin = get_origin(anno)
    if origin in {types.UnionType, getattr(__import__("typing"), "Union", object())}:
        return " | ".join(_anno_to_ts(a) for a in get_args(anno))

    # ---- collection generics ------------------------------------------
    if origin in {list, List}:  # List[T]  /  list[T]
        (sub,) = get_args(anno) or (Any,)
        return f"{_anno_to_ts(sub)}[]"

    if origin is dict:  # Dict[K, V]
        k, v = (get_args(anno) + (Any, Any))[:2]
        return f"Record<{_anno_to_ts(k)}, {_anno_to_ts(v)}>"

    # ---- catch-alls ----------------------------------------------------
    if isinstance(anno, type):
        return _map_primitive(anno.__name__)
    if hasattr(anno, "__name__"):
        return _map_primitive(anno.__name__) # type: ignore
    return "any"

# --------------------  CONVERTERS  --------------------


def _convert_enum(node: ast.ClassDef) -> str:
    # This turns Python enums into TS enums, so you can switch on actions in both worlds.
    lines = [f"export enum {node.name} {{"]
    for assign in (n for n in node.body if isinstance(n, ast.Assign)):
        key = assign.targets[0].id  # type: ignore[arg-type]
        value = (
            json.dumps(assign.value.value)
            if isinstance(assign.value, ast.Constant)
            else json.dumps(key)
        )
        lines.append(f"  {key} = {value},")
    lines.append("}")
    return "\n".join(lines)


def _convert_dataclass(node: ast.ClassDef) -> str:
    # This turns Python dataclasses into TS interfaces, so your data is always shaped right.
    annos = {
        n.target.id: n.annotation
        for n in node.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    }
    body = "\n".join(
        f"  {field}: {_anno_to_ts(anno)};" for field, anno in annos.items()
    )
    return f"export interface {node.name} {{\n{body}\n}}"


def _convert_typealias(node: Any) -> str:  # ast.TypeAlias
    # This turns Python type aliases into TS type aliases, for max code reuse.
    name = node.name.id  # type: ignore[attr-defined]
    rhs = _ts_from_ast(node.value)  # type: ignore[attr-defined]
    return f"export type {name} = {rhs};"


# --------------------  UTILS  --------------------


def _base_is_enum(base: ast.expr) -> bool:
    # This checks if a class is an Enum, so we know how to convert it.
    return (isinstance(base, ast.Name) and base.id == "Enum") or (
        isinstance(base, ast.Attribute) and base.attr == "Enum"
    )


# --------------------  PY → TS  --------------------


def _python_file_to_ts(path: Path) -> str:
    # This is the big spell: it reads a Python file and spits out TypeScript types.
    if not path.exists():
        return ""
    tree = ast.parse(path.read_text("utf-8"))
    parts: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            parts.append(
                _convert_enum(node)
                if any(_base_is_enum(b) for b in node.bases)
                else _convert_dataclass(node)
            )
        elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
            parts.append(_convert_typealias(node))
    return "\n\n".join(parts)


# --------------------  BiSex  --------------------


class BiSex:
    """Collect decorator‑captured functions and static types → single TS file."""
    # This class is the type ambassador: it collects all the types and exposed functions, and writes them to TS.

    def __init__(
        self,
        *,
        py_types: str | Path = "bisextypes.py",
        js_types: str | Path | None = None,
    ):
        self._py_types_path = Path(py_types)
        if not self._py_types_path.exists():
            raise ValueError(f"path '{self._py_types_path}' does not exist")
        self._js_types_path = (
            Path(js_types)
            if js_types is not None
            else WEBAPP_PATH / "src" / "lib" / "bisextypes.ts"
        )
        self._interfaces: dict[str, list[dict[str, Any]]] = {}

    # decorator
    def raw_fuck(self, interface: str | type):  # noqa: N802
        """
        A decorator to register a function as a handler for a specific interface.
        Meaning, the signature of the function will be translated as a field in a specific interface.

        # Usage
        ```python
        @bisex.raw_fuck("Nyasu")
        def my_handler(arg1: str, arg2: int) -> None:
            pass
        ```
        Translates to
        ```typescript
        export interface Nyasu {
          my_handler: (arg1: string, arg2: number) => null;
        }
        ```
        """
        iface = interface if isinstance(interface, str) else interface.__name__

        def deco(func):
            self._register(iface, func)
            return func

        return deco

    # capture func sig
    def _register(self, iface: str, func: Any):
        sig = inspect.signature(func)
        hints = getattr(func, "__annotations__", {})
        params = [
            (name or f"arg{idx}", _anno_to_ts(hints.get(name, inspect._empty)))
            for idx, (name, _) in enumerate(sig.parameters.items())
        ]
        ret = _anno_to_ts(hints.get("return"))
        self._interfaces.setdefault(iface, []).append(
            {"name": func.__name__, "params": params, "ret": ret}
        )

    # build
    def perform(self) -> Path:
        sections: list[str] = [
            "// This file is auto‑generated by BiSex.",
            "// Do not edit manually.",
        ]
        static_ts = _python_file_to_ts(self._py_types_path)
        if static_ts:
            sections.append(static_ts)
        for iface, funcs in self._interfaces.items():
            body = "\n".join(
                f"  {f['name']}: ({', '.join(f'{n}: {t}' for n, t in f['params'])}) => () => Promise<{f['ret']}>;"
                for f in funcs
            )
            sections.append(f"export interface {iface} {{\n{body}\n}}")
        self._js_types_path.write_text("\n\n".join(sections).rstrip() + "\n", "utf-8")
        return self._js_types_path


if __name__ == "__main__":
    bisex = BiSex(
        py_types="bisextypes.py",  
        js_types=WEBAPP_PATH / "src" / "lib" / "bisextypes.ts",
    )
    bisex.perform()  
