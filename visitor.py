import re
from abc import ABCMeta, abstractmethod

from rules import (
    AliasRules,
    BitflagRules,
    CallbackRules,
    CondRules,
    ConstRules,
    EnumRules,
    FnMacroRules,
    FuncRules,
    OpaqueRules,
    Rules,
    StructRules,
    UnionRules,
    _MultiRules,
    _parse_rules,
    _platform_id,
)

# TODO:
# special handling for properties


_BITFLAG_FILTER = {"preproc_def", "preproc_function_def"}

_PLATFORM_REGEX = re.compile(r"\bSDL_PLATFORM_\w+\b")


class VisitorBase(metaclass=ABCMeta):
    def __init__(self, unit: str) -> None:
        # The `unit` parameter is there just to tell you that's all you have
        pass

    @abstractmethod
    def start_platform_code(self, platforms: list[str]):
        """
        Start a platform-specific code block.

        This function is called once per platform-specific data instead of once per block.
        Thus, in the following code block:

        ```c
        #ifdef SDL_PLATFORM_WINDOWS
            extern void SDL_foo();

            extern void SDL_bar();
        #endif
        ```

        `start_platform_code` will be called once with `platforms` being `["SDL_PLATFORM_WINDOWS"]`
        for both `SDL_foo` and `SDL_bar`.


        `platforms` is a list of all the platforms that support the following code block.
        """
        raise NotImplementedError()

    @abstractmethod
    def end_platform_code(self):
        """
        End a platform-specific code block.

        Similarly to `start_platform_code`, this function is called once per platform-specific data.
        Refer to `start_platform_code` for more information.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_function(self, rules: FuncRules):
        """
        Visit a function node.

        Contents of `rules` are:

        function.docs - documentation of the function

        function.name - name of the function

        function.params - node that has all the parameters (if any); check the children for each parameter

        function.return_ptr - present if the return type is a pointer

        function.return - node that has the return type of the function

        function.decl - the entire function declaration, without the docs

        function - the entire function node (docs + declaration)
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_enum(self, rules: EnumRules):
        """
        Visit an enum node.

        Contents of `rules` are:

        enum.name - name of the enum

        enum.entries - node that has all the entries of the enum; check the children for each entry

        enum - the entire enum declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_opaque(self, rules: OpaqueRules):
        """
        Visit an opaque node.

        Contents of `rules` are:

        opaque.name - name of the opaque type

        opaque - the entire opaque type declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_struct(self, rules: StructRules):
        """
        Visit a non-opaque struct node.

        Contents of `rules` are:

        struct.name - name of the struct

        struct.members - node that has all the members of the struct; check the children for each member

        struct - the entire struct declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_union(self, rules: UnionRules):
        """
        Visit a union node.

        Contents of `rules` are:

        union.name - name of the union

        union.members - node that has all the members of the union; check the children for each member

        union - the entire union declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_bitflag(self, rules: BitflagRules):
        """
        Visit a bitflag node.

        Contents of `rules` are:

        bitflag.name - name of the bitflag

        bitflag.type - type of the bitflag


        flag - array of all the flags

        flag.name - array of all the flag names

        flag.value - array of all the flag values
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_alias(self, rules: AliasRules):
        """
        Visit an alias node.

        Contents of `rules` are:

        alias.name - name of the alias

        alias.type - type of the alias

        alias - the entire alias declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_callback(self, rules: CallbackRules):
        """
        Visit a callback node.

        Contents of `rules` are:

        callback.name - name of the callback

        callback.params - node that has all the parameters (if any); check the children for each parameter

        callback.return_ptr - present if the return type is a pointer

        callback.return - node that has the return type of the callback

        callback - the entire callback declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_fn_macro(self, rules: FnMacroRules):
        """
        Visit a function-like macro node.

        Contents of `rules` are:

        fn_macro.name - name of the macro

        fn_macro.params - node that has all the parameters (if any); check the children for each parameter

        fn_macro.body - the body of the macro

        fn_macro - the entire macro declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_const(self, rules: ConstRules):
        """
        Visit a macro constant node.

        Contents of `rules` are:

        const.name - name of the constant

        const.value - value of the constant

        const - the entire constant declaration
        """
        raise NotImplementedError()


class _Visitor:
    _inner: VisitorBase

    def __init__(self, cls: type[VisitorBase], unit: str, *args, **kwargs) -> None:
        self._inner = cls(unit, *args, **kwargs)
        # The `unit` parameter is there just to tell you that's all you have

        # There is no query that can tell tree sitter to
        # ignore typedef/#defines that are used for bitflags
        # so we have to do it manually
        self._parsing_bitflag = False
        self._platforms = []
        self._platform_node_id = None

    def visit(self, rules: _MultiRules):
        # TODO: check if this is the child of the `cond` node, if the node is not `None`
        # when not the child, then the `cond` node becomes None

        def _platform_setup(rule: Rules):
            self._platform_node_id = _platform_id(rule, self._platform_node_id)
            if self._platform_node_id:
                self._inner.start_platform_code(self._platforms)

        parsed = _parse_rules(rules)
        match parsed:
            case FuncRules():
                _platform_setup(parsed)
                self._inner.visit_function(parsed)
            case BitflagRules():
                _platform_setup(parsed)
                self._inner.visit_bitflag(parsed)
                self._parsing_bitflag = False
            case EnumRules():
                _platform_setup(parsed)
                self._inner.visit_enum(parsed)
            case OpaqueRules():
                _platform_setup(parsed)
                self._inner.visit_opaque(parsed)
            case StructRules():
                _platform_setup(parsed)
                self._inner.visit_struct(parsed)
            case UnionRules():
                _platform_setup(parsed)
                self._inner.visit_union(parsed)
            case AliasRules():
                if parsed.root.next_sibling.type in _BITFLAG_FILTER:
                    self._parsing_bitflag = True
                    return

                _platform_setup(parsed)
                self._inner.visit_alias(parsed)
            case CallbackRules():
                _platform_setup(parsed)
                self._inner.visit_callback(parsed)
            case FnMacroRules():
                _platform_setup(parsed)
                self._inner.visit_fn_macro(parsed)
            case ConstRules():
                if not self._parsing_bitflag or self._platform_node_id:
                    # skip constants inside bitflags and platform-specific code
                    _platform_setup(parsed)
                    self._inner.visit_const(parsed)
            case CondRules():
                self._platforms = _PLATFORM_REGEX.findall(
                    parsed.cond_text.text.decode()
                )
                if self._platforms:
                    self._platform_node_id = parsed.root.id

                return

        if self._platform_node_id:
            self._inner.end_platform_code()
