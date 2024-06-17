from tree_sitter import Language, Parser, Query
import tree_sitter_c as tsc


C_LANGUAGE = Language(tsc.language())

_PARSER = Parser(C_LANGUAGE)


def parser():
    return _PARSER


def query(text: str):
    return Query(C_LANGUAGE, text)
