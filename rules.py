from dataclasses import dataclass
from typing import Optional

from tree_sitter import Node

# TODO:
# - should you only store the contents (bytes) for some nodes (eg. name?)
# - cut the prefix from members here
# - find a way to codegen the types and ctors for you

_MultiRules = dict[str, list[Node]]


def _one(rules: _MultiRules, name: str) -> Node:
    assert len(rules[name]) == 1
    return rules[name][0]


@dataclass
class FuncRules:
    root: Node
    function_docs: Optional[Node]
    function_name: Node
    function_decl: Node
    function_return: Node
    function_return_ptr: Optional[Node]  # if present, the function returns a pointer
    function_params: (
        Node  # TODO: do you ever need the whole node or just the named children?
    )


def _func_rules(rules: _MultiRules) -> FuncRules:
    return FuncRules(
        root=_one(rules, "function"),
        function_docs=rules.get("function.docs", [None])[0],
        function_name=_one(rules, "function.name"),
        function_decl=_one(rules, "function.decl"),
        function_return=_one(rules, "function.return"),
        function_return_ptr=rules.get("function.return_ptr", [None])[0],
        function_params=_one(rules, "function.params"),
    )


@dataclass
class CallbackRules:
    root: Node
    callback_name: Node
    callback_params: Node
    callback_return: Node
    callback_return_ptr: Optional[Node]


def _callback_rules(rules: _MultiRules) -> CallbackRules:
    return CallbackRules(
        root=_one(rules, "callback"),
        callback_name=_one(rules, "callback.name"),
        callback_params=_one(rules, "callback.params"),
        callback_return=_one(rules, "callback.return"),
        callback_return_ptr=rules.get("callback.return_ptr", [None])[0],
    )


@dataclass
class FnMacroRules:
    root: Node
    fn_macro_name: Node
    fn_macro_params: Node
    fn_macro_body: Node


def _fn_macro_rules(rules: _MultiRules) -> FnMacroRules:
    return FnMacroRules(
        root=_one(rules, "fn_macro"),
        fn_macro_name=_one(rules, "fn_macro.name"),
        fn_macro_params=_one(rules, "fn_macro.params"),
        fn_macro_body=_one(rules, "fn_macro.body"),
    )


@dataclass
class BitflagRules:
    root: Node
    bitflag_name: Node
    bitflag_type: Node
    flags: list[Node]


def _bitflag_rules(rules: _MultiRules) -> BitflagRules:
    return BitflagRules(
        root=_one(rules, "bitflag"),
        bitflag_name=_one(rules, "bitflag.name"),
        bitflag_type=_one(rules, "bitflag.type"),
        flags=rules["flag"],
    )


@dataclass
class EnumRules:
    root: Node
    enum_name: Node
    enum_entries: Node


def _enum_rules(rules: _MultiRules) -> EnumRules:
    return EnumRules(
        root=_one(rules, "enum"),
        enum_name=_one(rules, "enum.name"),
        enum_entries=_one(rules, "enum.entries"),
    )


@dataclass
class OpaqueRules:
    root: Node
    opaque_name: Node


def _opaque_rules(rules: _MultiRules) -> OpaqueRules:
    return OpaqueRules(
        root=_one(rules, "opaque"),
        opaque_name=_one(rules, "opaque.name"),
    )


@dataclass
class StructRules:
    root: Node
    struct_name: Node
    struct_members: Node


def _struct_rules(rules: _MultiRules) -> StructRules:
    return StructRules(
        root=_one(rules, "struct"),
        struct_name=_one(rules, "struct.name"),
        struct_members=_one(rules, "struct.members"),
    )


@dataclass
class UnionRules:
    root: Node
    union_name: Node
    union_members: Node


def _union_rules(rules: _MultiRules) -> UnionRules:
    return UnionRules(
        root=_one(rules, "union"),
        union_name=_one(rules, "union.name"),
        union_members=_one(rules, "union.members"),
    )


@dataclass
class AliasRules:
    root: Node
    alias_name: Node
    alias_type: Node


def _alias_rules(rules: _MultiRules) -> AliasRules:
    return AliasRules(
        root=_one(rules, "alias"),
        alias_name=_one(rules, "alias.name"),
        alias_type=_one(rules, "alias.type"),
    )


@dataclass
class ConstRules:
    root: Node
    const_name: Node
    const_value: Node


def _const_rules(rules: _MultiRules) -> ConstRules:
    return ConstRules(
        root=_one(rules, "const"),
        const_name=_one(rules, "const.name"),
        const_value=_one(rules, "const.value"),
    )


@dataclass
class CondRules:
    root: Node
    cond_text: Node


def _cond_rules(rules: _MultiRules) -> CondRules:
    return CondRules(
        root=_one(rules, "cond"),
        cond_text=_one(rules, "cond.text"),
    )


Rules = (
    FuncRules
    | BitflagRules
    | EnumRules
    | OpaqueRules
    | StructRules
    | UnionRules
    | AliasRules
    | CallbackRules
    | FnMacroRules
    | ConstRules
    | CondRules
)


# rule: any type from this file
def _platform_id(rule: Rules, platform_id: Optional[int]) -> Optional[int]:
    if platform_id:
        cursor = rule.root
        while (
            cursor.parent
            and cursor.parent.parent
            and cursor.parent.parent.type != "translation_unit"
        ):
            cursor = cursor.parent

        if cursor.id != platform_id:
            platform_id = None

    return platform_id


# TODO: inline calls
def _parse_rules(rules: _MultiRules) -> Rules:
    if "function" in rules:
        return _func_rules(rules)
    elif "bitflag" in rules:
        return _bitflag_rules(rules)
    elif "enum" in rules:
        return _enum_rules(rules)
    elif "opaque" in rules:
        return _opaque_rules(rules)
    elif "struct" in rules:
        return _struct_rules(rules)
    elif "union" in rules:
        return _union_rules(rules)
    elif "alias" in rules:
        return _alias_rules(rules)
    elif "callback" in rules:
        return _callback_rules(rules)
    elif "fn_macro" in rules:
        return _fn_macro_rules(rules)
    elif "const" in rules:
        return _const_rules(rules)
    elif "cond" in rules:
        return _cond_rules(rules)

    assert False, "Unknown rule"
