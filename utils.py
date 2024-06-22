from tree_sitter import Language, Node, Parser, Query
import tree_sitter_c as tsc


C_LANGUAGE = Language(tsc.language())

_PARSER = Parser(C_LANGUAGE)


def parser():
    return _PARSER


def query(text: str) -> Query:
    return Query(C_LANGUAGE, text)


def only(ty: str, node: Node):
    """
    Get children of a node that are of a certain type. This is a lazy filter.
    """
    return filter(lambda n: n.type == ty, node.named_children)


def split_type_name(node: Node) -> tuple[str, str]:
    """
    Split a type and a name from a node.
    Can be used in parameters, members, and even functions to get return type and name.
    """
    ty = node.child_by_field_name("type")
    decl = node.child_by_field_name("declarator")

    if ty.type == "struct_specifier":
        ty = ty.child_by_field_name("name")

    ty = ty.text

    if decl is None:
        return ty.decode(), ""

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

            case "array_declarator":
                ty += decl.text[decl.text.find(b"[") :]
                decl = decl.child_by_field_name("declarator")

            case _:
                break

    return ty.decode(), decl.text.decode()
