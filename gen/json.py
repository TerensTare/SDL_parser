from tree_sitter import Node

import json

from visitor import visitor
from utils import only, split_type_name

# TODO:
# strip `struct` from members


def _name_value(entry: Node) -> tuple[str, str]:
    name = entry.child_by_field_name("name").text.decode()
    if (val := entry.child_by_field_name("value")) is not None:
        return name, val.text.decode()
    else:
        return name, "<default>"


def _parse_doc(docs: str, data: tuple[str, str]) -> dict[str, str]:
    ty, name = data

    n = 0
    while (n := docs.find("\\param", n)) != -1:
        f = docs.find("\\", n + 1)
        if f == -1:
            f = len(docs)

        brace_e = docs.find("]", n, f)
        brace_e = max(brace_e, n + len("\\param")) + 1

        if (
            not docs[brace_e:].strip().startswith(name)
            or docs[brace_e:].strip()[len(name)] != " "
        ):
            n = f
            continue

        brace_s = docs.find("[", n, brace_e)

        if brace_s == -1:
            space = docs.find(".", n + len("\\param") + 1, f)

            return {
                "type": ty,
                "name": name,
                # The token is '\n * ' because of the way the docs are formatted
                "docs": docs[space + 1 : f - 4].strip(),
            }

        # if docs.find("inout", brace_s + 1, brace_e) != -1:
        #     ref = REF
        #     pass
        # elif docs.find("out", brace_s + 1, brace_e) != -1:
        #     ref = OUT
        # elif docs.find("in", brace_s + 1, brace_e) != -1:
        #     if ty not in self._callbacks:
        #         ref = REF

        # opt = docs.find("opt", brace_s + 1, brace_e) != -1
        # own = docs.find("own", brace_s + 1, brace_e) != -1

        space = docs.find(" ", brace_e + 1, f)

        return {
            "type": ty,
            "name": name,
            # The token is '\n * ' because of the way the docs are formatted
            "docs": docs[space + 1 : f - 4].strip(),
        }


def _parse_return_docs(docs: str) -> str | None:
    n = docs.find("\\returns")
    if n == -1:
        return None

    f = docs.find("\n", n + 1)
    if f == -1:
        f = len(docs)

    b = docs.find("[", n, f)
    if b == -1:
        return docs[n + len("\\returns") + 1 : f].strip()

    e = docs.find("]", b, f)
    return docs[e + 1 : f].strip()


@visitor
class JsonVisitor:
    def __init__(self, unit: str) -> None:
        self._data = {}
        self._unit = unit
        pass

    def __del__(self) -> None:
        name = "SDL" if self._unit == "SDL" else f"SDL_{self._unit}"

        with open(f"out/json/{name}.g.json", "w") as f:
            json.dump(self._data, f, indent=4)

    def visit_function(self, rules: dict[str, Node | list[Node]]):
        ty, name = split_type_name(rules["function.decl"])
        docs = rules["function.docs"].text.decode()

        self._data[name] = {
            "type": "function",
            "return": ty,
            "docs": _parse_return_docs(docs) or "",
            "params": [
                _parse_doc(docs, split_type_name(param))
                for param in rules["function.params"].named_children
                if param.child_by_field_name("declarator") is not None
            ],
        }

    def visit_enum(self, rules: dict[str, Node | list[Node]]):
        name = rules["enum.name"].text.decode()

        self._data[name] = {
            "type": "enum",
            "members": dict(
                _name_value(entry)
                for entry in only("enumerator", rules["enum.entries"])
            ),
        }

    def visit_opaque(self, rules: dict[str, Node | list[Node]]):
        name = rules["opaque.name"].text.decode()

        self._data[name] = {
            "type": "opaque",
        }

    def visit_struct(self, rules: dict[str, Node | list[Node]]):
        name = rules["struct.name"].text.decode()

        self._data[name] = {
            "type": "struct",
            "members": [
                split_type_name(member)
                for member in rules["struct.members"].named_children
                if member.child_by_field_name("declarator") is not None
            ],
        }

    def visit_union(self, rules: dict[str, Node | list[Node]]):
        name = rules["union.name"].text.decode()

        self._data[name] = {
            "type": "union",
            "members": [
                split_type_name(member)
                for member in rules["union.members"].named_children
                if member.child_by_field_name("declarator") is not None
            ],
        }

    def visit_bitflag(self, rules: dict[str, Node | list[Node]]):
        name = rules["bitflag.name"].text.decode()

        self._data[name] = {
            "type": "bitflag",
            "flags": dict(
                _name_value(flag)
                for flag in filter(lambda x: x.type == "preproc_def", rules["flag"])
            ),
        }

    def visit_alias(self, rules: dict[str, Node | list[Node]]):
        ty, name = split_type_name(rules["alias"])

        self._data[name] = {
            "type": "alias",
            "alias": ty,
        }

    def visit_callback(self, rules: dict[str, Node | list[Node]]):
        ty, _ = split_type_name(rules["callback"])
        name = rules["callback.name"].text.decode()

        self._data[name] = {
            "type": "callback",
            "return": ty,
            "params": [
                split_type_name(param)
                for param in rules["callback.params"].named_children
                if param.child_by_field_name("declarator") is not None
            ],
        }

    def visit_fn_macro(self, rules: dict[str, Node | list[Node]]):
        pass

    def visit_const(self, rules: dict[str, Node | list[Node]]):
        name = rules["const.name"].text.decode()
        value = rules["const.value"].text.decode()

        # these are macros that alias to other functions, we don't need them
        # so just skip them
        if any(c for c in name if c.islower()):
            return

        # these values are supposed to be private or C-specific (eg. __FILE__ and __LINE__)
        if value.find("__") != -1:
            return

        self._data[name] = {
            "type": "const",
            "value": value,
        }
