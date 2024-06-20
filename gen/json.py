from tree_sitter import Node
from visitor import visitor

import json

# TODO:
# strip `struct` from members


def _split_type_name(node: Node) -> tuple[bytes, bytes]:
    ty = node.child_by_field_name("type").text
    decl = node.child_by_field_name("declarator")

    if decl is None:
        return ty, b""

    for n in node.children:
        if n.type == "type_qualifier":
            ty = n.text + b" " + ty
            break  # logically there should be only one type_qualifier

    while not decl.type == "identifier":
        match decl.type:
            case "pointer_declarator":
                decl = decl.child_by_field_name("declarator")
                ty += b"*"

            case "function_declarator":
                decl = decl.child_by_field_name("declarator")

            case _:
                break

    return ty.decode(), decl.text.decode()


def _name_value(entry: Node):
    name = entry.child_by_field_name("name").text.decode()
    if (val := entry.child_by_field_name("value")) is not None:
        return name, val.text.decode()
    else:
        return name, "<default>"


def _only(ty: str, node: Node):
    return filter(lambda n: n.type == ty, node.named_children)


@visitor
class JsonVisitor:
    def __init__(self, unit: str) -> None:
        self._data = {}
        self._unit = unit
        pass

    def __del__(self) -> None:
        with open(f"out/json/{self._unit}.g.json", "w") as f:
            json.dump(self._data, f, indent=4)

    def visit_function(self, rules: dict[str, Node | list[Node]]):
        ty, name = _split_type_name(rules["function.decl"])

        self._data[name] = {
            "type": "function",
            "return": ty,
            "params": [
                _split_type_name(param)
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
                for entry in _only("enumerator", rules["enum.entries"])
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
                _split_type_name(member)
                for member in rules["struct.members"].named_children
                if member.child_by_field_name("declarator") is not None
            ],
        }

    def visit_union(self, rules: dict[str, Node | list[Node]]):
        name = rules["union.name"].text.decode()

        self._data[name] = {
            "type": "union",
            "members": [
                _split_type_name(member)
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
        ty, name = _split_type_name(rules["alias"])

        self._data[name] = {
            "type": "alias",
            "alias": ty,
        }

    def visit_callback(self, rules: dict[str, Node | list[Node]]):
        ty, _ = _split_type_name(rules["callback"])
        name = rules["callback.name"].text.decode()

        self._data[name] = {
            "type": "callback",
            "return": ty,
            "params": [
                _split_type_name(param)
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
