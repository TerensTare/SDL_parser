import re
import sys
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
    PropertyRules,
    Rules,
    StructRules,
    UnionRules,
    _MultiRules,
    _parse_rules,
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
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_enum(self, rules: EnumRules):
        """
        Visit an enum node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_opaque(self, rules: OpaqueRules):
        """
        Visit an opaque node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_struct(self, rules: StructRules):
        """
        Visit a non-opaque struct node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_union(self, rules: UnionRules):
        """
        Visit a union node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_bitflag(self, rules: BitflagRules):
        """
        Visit a bitflag node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_alias(self, rules: AliasRules):
        """
        Visit an alias node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_callback(self, rules: CallbackRules):
        """
        Visit a callback node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_fn_macro(self, rules: FnMacroRules):
        """
        Visit a function-like macro node.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_property(self, rules: PropertyRules):
        """
        Visit a property macro node. Property macros start with `SDL_PROP` and their value is a string.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_const(self, rules: ConstRules):
        """
        Visit a macro constant node.
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
        self._platform_block = None

    def visit(self, rules: _MultiRules):
        # TODO: check if this is the child of the `cond` node, if the node is not `None`
        # when not the child, then the `cond` node becomes None

        def _platform_setup(rule: Rules):
            if self._platform_block:
                if (
                    rule.root.start_point.row >= self._platform_block.start_point.row
                    and rule.root.end_point.row <= self._platform_block.end_point.row
                ):
                    self._inner.start_platform_code(self._platforms)
                else:  # reset
                    self._platform_block = None

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
                if not self._parsing_bitflag:
                    # skip constants inside bitflags and platform-specific code
                    _platform_setup(parsed)
                    self._inner.visit_const(parsed)
            case CondRules():
                self._platforms = _PLATFORM_REGEX.findall(
                    parsed.cond_text.text.decode()
                )
                if self._platforms:
                    self._platform_block = parsed.root

                return
            case PropertyRules():
                # TODO: are there properties in platform-specific blocks? Right now none
                self._inner.visit_property(parsed)

            case _:
                print(f"Internal error: Unhandled rule type {type(parsed)}")
                sys.exit(1)

        if self._platform_block:
            self._inner.end_platform_code()
