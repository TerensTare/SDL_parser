from abc import ABCMeta, abstractmethod
from getopt import getopt
import inspect
import sys
import re

from tree_sitter import Node

_Rules = dict[str, Node | list[Node]]


_BITFLAG_FILTER = {"preproc_def", "preproc_function_def"}

_PLATFORM_REGEX = re.compile(r"\bSDL_PLATFORM_\w+\b")


class Visitor(metaclass=ABCMeta):
    def __init__(self, unit: str) -> None:
        # The `unit` parameter is there just to tell you that's all you have

        # There is no query that can tell tree sitter to
        # ignore typedef/#defines that are used for bitflags
        # so we have to do it manually
        self._parsing_bitflag = False
        self._platforms = []
        self._platform_node_id = None

    def __del__(self) -> None:
        # empty for now
        pass

    def visit(self, rules: _Rules):
        # TODO: check if this is the child of the `cond` node, if the node is not `None`
        # when not the child, then the `cond` node becomes None

        def _platform_setup(rule: str):
            cursor = rules[rule]

            if self._platform_node_id:
                while (
                    cursor.parent
                    and cursor.parent.parent
                    and cursor.parent.parent.type != "translation_unit"
                ):
                    cursor = cursor.parent

                if cursor.id != self._platform_node_id:
                    self._platform_node_id = None

            if self._platform_node_id:
                self.start_platform_code(self._platforms)

        if "function" in rules:
            _platform_setup("function")
            self.visit_function(rules)
        elif "bitflag" in rules:
            _platform_setup("bitflag")
            self.visit_bitflag(rules)
            self._parsing_bitflag = False
        elif "enum" in rules:
            _platform_setup("enum")
            self.visit_enum(rules)
        elif "opaque" in rules:
            _platform_setup("opaque")
            self.visit_opaque(rules)
        elif "struct" in rules:
            _platform_setup("struct")
            self.visit_struct(rules)
        elif "union" in rules:
            _platform_setup("union")
            self.visit_union(rules)
        elif "alias" in rules:
            if rules["alias"].next_sibling.type in _BITFLAG_FILTER:
                self._parsing_bitflag = True
                return

            _platform_setup("alias")
            self.visit_alias(rules)
        elif "callback" in rules:
            _platform_setup("callback")
            self.visit_callback(rules)
        elif "fn_macro" in rules:
            _platform_setup("fn_macro")
            self.visit_fn_macro(rules)
        elif "const" in rules:
            if not self._parsing_bitflag or self._platform_node_id:
                # skip constants inside bitflags and platform-specific code
                _platform_setup("const")
                self.visit_const(rules)
        elif "cond" in rules:
            self._platforms = _PLATFORM_REGEX.findall(rules["cond.text"].text.decode())
            if not self._platforms:
                return

            self._platform_node_id = rules["cond"].id
            return

        if self._platform_node_id:
            self.end_platform_code()

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
    def visit_function(self, rules: _Rules):
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
    def visit_enum(self, rules: _Rules):
        """
        Visit an enum node.

        Contents of `rules` are:

        enum.name - name of the enum

        enum.entries - node that has all the entries of the enum; check the children for each entry

        enum - the entire enum declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_opaque(self, rules: _Rules):
        """
        Visit an opaque node.

        Contents of `rules` are:

        opaque.name - name of the opaque type

        opaque - the entire opaque type declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_struct(self, rules: _Rules):
        """
        Visit a non-opaque struct node.

        Contents of `rules` are:

        struct.name - name of the struct

        struct.members - node that has all the members of the struct; check the children for each member

        struct - the entire struct declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_union(self, rules: _Rules):
        """
        Visit a union node.

        Contents of `rules` are:

        union.name - name of the union

        union.members - node that has all the members of the union; check the children for each member

        union - the entire union declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_bitflag(self, rules: _Rules):
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
    def visit_alias(self, rules: _Rules):
        """
        Visit an alias node.

        Contents of `rules` are:

        alias.name - name of the alias

        alias.type - type of the alias

        alias - the entire alias declaration
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_callback(self, rules: _Rules):
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
    def visit_fn_macro(self, rules: _Rules):
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
    def visit_const(self, rules: _Rules):
        """
        Visit a macro constant node.

        Contents of `rules` are:

        const.name - name of the constant

        const.value - value of the constant

        const - the entire constant declaration
        """
        raise NotImplementedError()


def visitor(cls):
    has_init = cls.__dict__.__contains__("__init__")
    has_del = cls.__dict__.__contains__("__del__")

    mod = cls.__module__
    cls = type("Visitor", (Visitor,), dict(cls.__dict__))  # add base

    if has_init:
        # these are done by default if no __init__ is specified
        old_init = cls.__init__

        def __init__(self, *args):
            super(cls, self).__init__(*args)

            all_args = inspect.getfullargspec(old_init)

            flag_names = set(all_args.kwonlyargs)
            defaults = all_args.kwonlydefaults or {}

            flags, _ = getopt(
                sys.argv[2:],
                shortopts="",
                longopts=[f"{flag}=" for flag in flag_names],
            )

            flags = {k[2:]: v for k, v in flags}

            for flag in flag_names:
                if flag not in flags and flag not in defaults:
                    print(f"Error: missing flag `{flag}`")
                    sys.exit(1)

            old_init(self, *args, **flags)

        cls.__init__ = __init__

    if has_del:
        old_del = cls.__del__

        def __del__(self):
            old_del(self)
            super(cls, self).__del__()

        cls.__del__ = __del__

    sys.modules[mod].__dict__["Visitor"] = cls  # add to module

    return cls
