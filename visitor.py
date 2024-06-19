from abc import ABCMeta, abstractmethod
import sys

from tree_sitter import Node

_Rules = dict[str, Node | list[Node]]


_BITFLAG_FILTER = {"preproc_def", "preproc_function_def"}


class Visitor(metaclass=ABCMeta):
    def __init__(self) -> None:
        # There is no query that can tell tree sitter to
        # ignore typedef/#defines that are used for bitflags
        # so we have to do it manually
        self._parsing_bitflag = False

    def __del__(self) -> None:
        # empty for now
        pass

    def visit(self, rules: _Rules):
        if "function" in rules:
            self.visit_function(rules)
        elif "bitflag" in rules:
            self.visit_bitflag(rules)
            self._parsing_bitflag = False
        elif "enum" in rules:
            self.visit_enum(rules)
        elif "opaque" in rules:
            self.visit_opaque(rules)
        elif "struct" in rules:
            self.visit_struct(rules)
        elif "union" in rules:
            self.visit_union(rules)
        elif "alias" in rules:
            if rules["alias"].next_sibling.type in _BITFLAG_FILTER:
                self._parsing_bitflag = True
                return

            self.visit_alias(rules)
        elif "callback" in rules:
            self.visit_callback(rules)
        elif "fn_macro" in rules:
            self.visit_fn_macro(rules)
        elif "const" in rules:
            if not self._parsing_bitflag:
                self.visit_const(rules)

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

        def __init__(self, *args, **kwargs):
            super(cls, self).__init__()
            old_init(self, *args, **kwargs)

        cls.__init__ = __init__

    if has_del:
        old_del = cls.__del__

        def __del__(self):
            old_del(self)
            super(cls, self).__del__()

        cls.__del__ = __del__

    sys.modules[mod].__dict__["Visitor"] = cls  # add to module

    return cls
