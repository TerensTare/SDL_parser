from typing import Literal
from tree_sitter import Node
import utils
import re

# TODO:
# - add comment if the previous node is one
# - distinguish struct strings that are from input structs and output structs
# ^ (The first should be `InString` and the second should be `String`)
# ^ one solution is to have a BiString that can be constructed from string and converted to string

_EXT_PRELUDE: str = """
using System;
using System.Runtime;
using System.Runtime.InteropServices;

using static SDL3.SDL;

namespace SDL3
{{
    public static class {0}
    {{
        private const string lib = "{1}";

"""

_PRELUDE: str = """
using System;
using System.Runtime;
using System.Runtime.InteropServices;

namespace SDL3
{{
    // used internally as some names are left from the conversion
    using Uint8 = byte;
    using Uint16 = ushort;
    using Uint32 = uint;
    using Uint64 = ulong;
    using Sint8 = sbyte;
    using Sint16 = short;
    using Sint32 = int;
    using Sint64 = long;

    public static class {0}
    {{
        private const string lib = "{1}";

        public enum SDL_bool : int
        {{
            SDL_FALSE = 0,
            SDL_TRUE = 1,
        }}

        [StructLayout(LayoutKind.Sequential)]
        public struct SDL_Time
        {{
            public static implicit operator long(SDL_Time value) {{ return value._value; }}

            private readonly long _value;
        }}

        [StructLayout(LayoutKind.Sequential)]
        public struct SDL_FunctionPointer
        {{
            public static implicit operator bool(SDL_FunctionPointer value) {{ return value._value != IntPtr.Zero; }}

            private readonly IntPtr _value;
        }}

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_malloc(IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_calloc(IntPtr nmemb, IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_realloc(IntPtr memblock, IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern void SDL_free(IntPtr memblock);

"""

_TYPE_MAP = {
    "unsigned char": "byte",
    "unsigned short": "ushort",
    "unsigned int": "uint",
    "Uint8": "byte",
    "Uint16": "ushort",
    "Uint32": "uint",
    "Uint64": "ulong",
    "Sint8": "sbyte",
    "Sint16": "short",
    "Sint32": "int",
    "Sint64": "long",
    "size_t": "IntPtr",
    "intptr_t": "IntPtr",
    "XEvent": "void",  # XEvent is opaque
}

_NATIVE_TYPES = {
    "byte",
    "sbyte",
    "short",
    "ushort",
    "int",
    "uint",
    "long",
    "ulong",
    "float",
    "double",
}

# thanks a lot, C#
_PARAM_BLACKLIST = {"lock", "event", "string", "override"}


_UNSAFE_STRUCT_QUERY = utils.query("""
(field_declaration_list
    (_ declarator: (array_declarator) @fixed)
)""")


def _only(ty: str, node: Node):
    return filter(lambda x: x.type == ty, node.children)


def _parse_const(text: str) -> int:
    finish = text.find("/*")  # keep comments off our constants
    if finish == -1:
        finish = len(text)

    end = 0
    if text[end].isnumeric():
        # if this is an integer, find the last numeric character (skip the literal suffixes as they don't match with C#)
        while end < finish and text[end] in "0123456789ABCDEFabcdefxX":
            end += 1
    else:
        # otherwise, we have to find the last non-whitespace character
        end = finish
        while end > 0 and text[end - 1] <= " ":
            end -= 1

    return end


class CsVisitor:
    def __init__(self, *, is_ext: bool, out: str, dll: str, clazz: str) -> None:
        self._file = open(out, "w")

        prelude = _EXT_PRELUDE if is_ext else _PRELUDE
        self._file.write(prelude.format(clazz, dll))

        self._sdl_opaques = set()
        self._callbacks = set()
        self._fn_macros: dict[re.Pattern[str], tuple] = {
            re.compile(r"\bSDL_UINT64_C\b"): ([r"\bN\b"], "N"),
            re.compile(r"\bSDL_VERSIONNUM\b"): (
                [r"\bX\b", r"\bY\b", r"\bZ\b"],
                "X * 1000 + Y * 100 + Z",
            ),
        }
        self._const_map = dict()

        self._out = out

        # are we parsing a bitflag currently?
        self._parsing_bitflag = False

    def another_one(self, *, is_ext: bool, out: str, dll: str, clazz: str):
        cs = CsVisitor(is_ext=is_ext, out=out, dll=dll, clazz=clazz)
        cs._sdl_opaques = self._sdl_opaques
        cs._callbacks = self._callbacks
        cs._fn_macros = self._fn_macros
        cs._const_map = self._const_map

        return cs

    def __del__(self) -> None:
        self._file.write("    }\n}\n")
        self._file.close()

        with open(self._out, "r") as f:
            data = f.read()

        self._data = data
        while self._expand():
            # keep expanding until no more expansions are possible
            # TODO: as an optimization, expand only on the expanded text
            pass

        # thanks a lot, C#
        self._data = self._data.replace("<<", "<< (int)")

        with open(self._out, "w") as f:
            f.write(self._data)

    def visit(self, rules):
        if "function" in rules:
            self.visit_function(rules)
        elif "bitflag" in rules:
            self.visit_bitflag(rules)
        elif "enum" in rules:
            self.visit_enum(rules)
        elif "opaque" in rules:
            self.visit_opaque(rules)
        elif "struct" in rules:
            self.visit_struct(rules)
        elif "union" in rules:
            self.visit_union(rules)
        elif "alias" in rules:
            self.visit_alias(rules)
        elif "callback" in rules:
            self.visit_callback(rules)
        elif "fn_macro" in rules:
            self.visit_fn_macro(rules)
        elif "const" in rules:
            self.visit_const(rules)

    def visit_function(self, rules):
        name = rules["function.name"].text.decode()
        docs = rules["function.docs"]

        ret = rules["function.return"].text.decode()
        ret = _TYPE_MAP.get(ret, ret)

        ret_comment = ""

        if "function.return_ptr" in rules and ret not in self._sdl_opaques:
            if name.endswith("s"):  # probably always an array
                ret = f"{ret}[]"
            elif ret == "char":
                ret = (
                    "String"
                    if docs.text.find(b"\\returns[own]") == -1
                    else "HeapString"
                )
            else:
                ret_comment = f" // {ret} *"
                ret = "IntPtr"

        if rules["function.params"].text != b"(void)":
            self._file.write(f"""        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern {ret} {name}(
""")

            params = list(_only("parameter_declaration", rules["function.params"]))
            mx = len(params)
            for i, param in enumerate(params):
                ty, name, comment = self._format_param(
                    param=param, docs=docs.text.decode()
                )

                delim = "" if i == mx - 1 else ","

                self._file.write(f"            {ty} {name}{delim}{comment}\n")

            self._file.write(f"        );{ret_comment}\n\n")
        else:
            self._file.write(f"""        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern {ret} {name}();{ret_comment}

""")

    def visit_enum(self, rules):
        name = rules["enum.name"].text.decode()

        self._file.write(f"""        public enum {name}
        {{
""")

        for entry in _only("enumerator", rules["enum.entries"]):
            entry_name = entry.child_by_field_name("name").text.decode()
            entry_value = entry.child_by_field_name("value")

            if entry_value is None:
                self._file.write(f"            {entry_name},\n")
            else:
                entry_value = entry_value.text.decode()
                self._file.write(f"            {entry_name} = (int){entry_value},\n")

        self._file.write("        }\n\n")

        for entry in _only("enumerator", rules["enum.entries"]):
            entry_name = entry.child_by_field_name("name").text.decode()

            # HACK: needed just so C# doesn't complain about enum values not being in scope
            self._file.write(
                f"        internal const int {entry_name} = (int){name}.{entry_name};\n"
            )

            self._const_map[entry_name] = "int"

        self._file.write("\n")

    def visit_opaque(self, rules):
        name = rules["opaque.name"].text.decode()
        self._sdl_opaques.add(name)

        self._file.write(f"""        [StructLayout(LayoutKind.Sequential)]
        public struct {name}
        {{
            public static implicit operator bool({name} value) {{ return value._value != IntPtr.Zero; }}

            private readonly IntPtr _value;
        }}

""")

    def visit_struct(self, rules):
        name = rules["struct.name"].text.decode()

        # TODO: recheck this
        if rules["struct.members"].named_child_count == 0:
            return

        unsafe_query = _UNSAFE_STRUCT_QUERY.matches(rules["struct.members"])
        unsafe = ""
        if len(unsafe_query) > 0:
            if len(unsafe_query[0][1]) > 0:
                unsafe = "unsafe "

        self._file.write(f"""        [StructLayout(LayoutKind.Sequential)]
        public {unsafe}struct {name}
        {{
""")

        if name != "SDL_GamepadBinding":
            for member in _only("field_declaration", rules["struct.members"]):
                ty_node = member.child_by_field_name("type")

                for decl_node in member.children_by_field_name("declarator"):
                    ty, name, comment = self._format_member(
                        ty_=ty_node,
                        decl_=decl_node,
                    )

                    pre = ""

                    if name.find("padding") != -1:
                        pre = "private"
                    else:
                        pre = "public"

                    if (s := name.find("[")) != -1:
                        e = name.find("]", s)
                        old_len = name[s + 1 : e]

                        pre += " fixed"
                        if ty not in _NATIVE_TYPES:
                            pre = f"""[MarshalAs(UnmanagedType.ByValArray, ArraySubType = UnmanagedType.Struct, SizeConst = ((int){old_len}))]
            public"""
                            ty += "[]"
                            name = name[:s]

                    self._file.write(f"""            {pre} {ty} {name};{comment}
""")

        self._file.write("        }\n\n")

    def visit_union(self, rules):
        name = rules["union.name"].text.decode()

        if rules["union.members"].named_child_count == 0:
            return

        unsafe_query = _UNSAFE_STRUCT_QUERY.matches(rules["union.members"])
        unsafe = ""
        if len(unsafe_query) > 0:
            if len(unsafe_query[0][1]) > 0:
                unsafe = "unsafe "

        self._file.write(f"""        [StructLayout(LayoutKind.Explicit)]
        public {unsafe}struct {name}
        {{
""")

        for member in _only("field_declaration", rules["union.members"]):
            ty_node = member.child_by_field_name("type")
            assert ty_node is not None

            # chances are there might be multiple declarations in the same line
            for decl_node in member.children_by_field_name("declarator"):
                ty, name, comment = self._format_member(
                    ty_=ty_node,
                    decl_=decl_node,
                )

                pre = ""

                if name.find("padding") != -1:
                    pre = "private"
                else:
                    pre = "public"

                if name.find("[") != -1:
                    pre += " fixed"

                self._file.write(f"""            [FieldOffset(0)] {pre} {ty} {name};{comment}
    """)

        self._file.write("        }\n\n")

    def visit_bitflag(self, rules):
        name = rules["bitflag.name"].text.decode()
        ty = rules["bitflag.type"].text.decode()
        ty = _TYPE_MAP.get(ty, ty)

        self._file.write(f"""        [Flags]
        public enum {name} : {ty}
        {{
""")

        for entry in filter(lambda x: x.type == "preproc_def", rules["flag"]):
            entry_name = entry.child_by_field_name("name").text.decode()

            entry_value = entry.child_by_field_name("value").text.decode()
            end = _parse_const(entry_value)

            self._const_map[entry_name] = ty

            self._file.write(f"""            {entry_name} = {entry_value[:end].strip()},
""")

        self._file.write("        }\n\n")

        for entry in filter(lambda x: x.type == "preproc_def", rules["flag"]):
            entry_name = entry.child_by_field_name("name").text.decode()

            entry_value = entry.child_by_field_name("value").text.decode()
            end = _parse_const(entry_value)

            self._file.write(
                f"        internal const {ty} {entry_name} = ({ty}){name}.{entry_name};\n"
            )

        self._parsing_bitflag = False

    def visit_alias(self, rules):
        # There is no query that can tell tree sitter to
        # ignore typedef/#defines that are used for bitflags
        # so we have to do it manually
        _FILTER = {"preproc_def", "preproc_function_def"}
        if rules["alias"].next_sibling.type in _FILTER:
            self._parsing_bitflag = True
            return

        name = rules["alias.name"].text.decode()

        if "alias.ptr" in rules:
            ty = "IntPtr"
        else:
            ty = rules["alias.type"].text.decode()
            ty = _TYPE_MAP.get(ty, ty)

        self._file.write(f"""        [StructLayout(LayoutKind.Sequential)]
        public struct {name}
        {{
            public static implicit operator {name}({ty} value) {{ return new {name}(value); }}
            public static implicit operator {ty}({name} value) {{ return value._value; }}

            private {name}({ty} value) {{ _value = value; }}
            private readonly {ty} _value;
        }}

""")

    def visit_callback(self, rules):
        name = rules["callback.name"].text.decode()
        self._callbacks.add(name)

        ret = rules["callback.return"].text.decode()

        if "callback.return_ptr" in rules and ret not in self._sdl_opaques:
            comment = f" // {ret} *"
            ret = "IntPtr"

        if rules["callback.params"].text != b"(void)":
            self._file.write(f"""        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate {ret} {name}(
""")

            params = list(_only("parameter_declaration", rules["callback.params"]))
            mx = len(params)
            for i, param in enumerate(params):
                ty, name, comment = self._format_param(param=param, docs="")

                delim = "" if i == mx - 1 else ","

                self._file.write(f"            {ty} {name}{delim}{comment}\n")

            self._file.write("        );\n\n")
        else:
            self._file.write(f"""        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate {ret} {name}();

""")

    def visit_fn_macro(self, rules):
        name = rules["fn_macro.name"].text.decode()
        if name in self._fn_macros:
            return

        params = rules["fn_macro.params"]
        body = rules["fn_macro.body"].text.decode()

        ps_reg = [
            rf"\b{node.text.decode().strip()}\b" for node in _only("identifier", params)
        ]

        name_re = re.compile(rf"\b{name}\b")
        self._fn_macros[name_re] = (ps_reg, body)

    def visit_const(self, rules):
        if self._parsing_bitflag:
            return

        name = rules["const.name"].text.decode()
        value = rules["const.value"].text.decode()

        # these are macros that alias to other functions, we don't need them
        # so just skip them
        if any(c for c in name if c.islower()):
            return

        # these values are supposed to be private or C-specific (eg. __FILE__ and __LINE__)
        if value.find("__") != -1:
            return

        if value.startswith("((") and value[2].isalpha():
            # HACK: skip casted constants for now
            # e = value.find(")", 2)
            # ty = value[2:e]
            # last = value.rfind(")")
            # value = value[e + 1 : last]

            # self._file.write(
            #     f"        public static readonly {ty} {name} = ({ty})({value});\n\n"
            # )
            return

        prelude = "const"
        ty = "int"
        end = len(value)

        if value.startswith('"') or value.startswith("SDL_PROP"):
            prelude = "static readonly"
            ty = "string"
        else:
            # TODO: temporary hack
            end = _parse_const(value)

            ty = "long" if value.startswith("-") or value.startswith("(-") else "ulong"
            if value in self._const_map:
                # hopefully this helps
                ty = self._const_map[value]

            if value.find("(") != -1:
                # just in case
                prelude = "static readonly"

            if value == "NULL":
                prelude = "static readonly"
                ty = "IntPtr"
                value = "IntPtr.Zero"

        self._const_map[name] = ty

        self._file.write(f"        public {prelude} {ty} {name} = {value[:end]};\n\n")

    # TODO: this is static/general utility
    def _format_type_name(self, *, ty: Node, decl: Node) -> tuple[str, str, str]:
        if ty.type == "struct_specifier":
            ty = ty.child_by_field_name("name")

        node = ty.parent # get this before it's too late
        ty = ty.text.decode()

        if node.children[0].text == b"const":
            cst = "const"
        else:
            cst = ""

        ptr = ""
        comment = ""

        # TODO: handle arrays
        # TODO: handle function pointers
        while not decl.type.endswith("identifier"):
            match decl.type:
                case "pointer_declarator":
                    ptr += "*"
                    decl = decl.child_by_field_name("declarator")

                case "type_qualifier":
                    decl = decl.child_by_field_name("declarator")

                case "function_declarator":
                    # function_declarator > parenthesized_declarator > pointer_declarator > identifier
                    decl = decl.child_by_field_name("declarator")
                    decl = decl.named_children[0]
                    decl = decl.child_by_field_name("declarator")

                    ty = "IntPtr"

                    decl_lhs = node.text[: decl.start_byte - node.start_byte].decode()
                    decl_rhs = node.text[decl.end_byte - node.start_byte :].decode()

                    comment = f" // {decl_lhs} {decl_rhs}"

                case _:
                    break

        name = decl.text.decode()
        if name in _PARAM_BLACKLIST:
            name = f"@{name}"

        ty = _TYPE_MAP.get(ty, ty)

        return f"{cst} {ty} {ptr}".strip(), name, comment

    def _format_param(self, *, param: Node, docs: str):
        ty_node = param.child_by_field_name("type")
        decl_node = param.child_by_field_name("declarator")

        assert ty_node is not None and decl_node is not None

        ty, name, comment = self._format_type_name(
            ty=ty_node,
            decl=decl_node,
        )

        NO_DIR = 0
        REF = 1
        OUT = 2

        ref: Literal[0, 1, 2] = NO_DIR  # None, ref or out (0, 1, 2)

        opt = False
        own = False
        is_str = False
        is_void = False

        n = 0
        while (n := docs.find("\\param", n)) != -1:
            f = docs.find("\n", n)
            if f == -1:
                f = len(docs)

            brace_e = docs.find("]", n, f)
            brace_e = max(brace_e, n + len("\\param")) + 1

            tn = name if not name[0] == "@" else name[1:]

            if (
                not docs[brace_e:].strip().startswith(tn)
                or docs[brace_e:].strip()[len(tn)] != " "
            ):
                n = f
                continue

            brace_s = docs.find("[", n, brace_e)

            if brace_s == -1:
                break

            if docs.find("inout", brace_s + 1, brace_e) != -1:
                ref = REF
                pass
            elif docs.find("out", brace_s + 1, brace_e) != -1:
                ref = OUT
            elif docs.find("in", brace_s + 1, brace_e) != -1:
                if ty not in self._callbacks:
                    ref = REF

            opt = docs.find("opt", brace_s + 1, brace_e) != -1
            own = docs.find("own", brace_s + 1, brace_e) != -1

            break

        ot = ty

        if ty.startswith("const "):
            ty = ty[6:].strip()

        if ty.endswith("*"):
            if ref == NO_DIR:
                ref = REF
            ty = ty[:-1].strip()

            if ty.startswith("char"):
                is_str = True
                if ref == OUT:
                    ty = "HeapString" if own else "String"
                else:
                    ty = "InString"
                    ref = NO_DIR
            elif ty.startswith("void"):
                is_void = True
                if ref != OUT:
                    ref = NO_DIR
            elif ty in self._sdl_opaques or ty in self._callbacks:
                if ref != OUT:
                    ref = NO_DIR
                pass
            else:
                # this is probably an array
                # or just a pointer
                pass

        if ty.endswith("*"):
            # ^ this is the array pointer or a void **
            ty = ty[:-1].strip()

            if not is_void and ref != OUT:
                ty += "[]"

            if ref != OUT:
                ref = REF

        if is_void:
            ty = "IntPtr"
            comment = f" // {ot}"

        # opaques are nullable, just like strings
        if opt and not (is_str or is_void or ty in self._sdl_opaques):
            comment = f" // {ot}"
            ty = "IntPtr"
            if ref != OUT:
                ref = NO_DIR

        if ref == REF:
            return f"ref {ty}", name, comment
        elif ref == OUT:
            return f"out {ty}", name, comment
        else:
            return ty, name, comment

    def _format_member(self, *, ty_: Node, decl_: Node) -> tuple[str, str, str]:
        ty, name, comment = self._format_type_name(
            ty=ty_,
            decl=decl_,
        )

        if ty.endswith("*"):
            if ty.endswith("char *"):
                ty = "String"
            else:
                ty = "IntPtr"

        return ty, name, comment

    def _expand(self) -> bool:
        expanded = False

        for name, (ps_reg, body) in self._fn_macros.items():
            # expand the function macros
            n = 0
            while (r := name.search(self._data, n)) is not None:
                expanded = True
                n, p = r.start(), r.end()

                s = self._data.find("(", p)

                # There might be two or more '(' in the macro (especially on nested macros)
                # We only need the last ')'
                f = s + 1
                level = 1
                while f < len(self._data):
                    if self._data[f] == "(":
                        level += 1
                    elif self._data[f] == ")":
                        level -= 1

                    if level == 0:
                        break

                    f += 1

                if f == len(self._data):
                    break

                args = self._data[s + 1 : f].split(",")
                args = [arg.strip() for arg in args]

                body_rep = body
                for p, arg in zip(ps_reg, args):
                    body_rep = re.sub(p, arg, body_rep)

                self._data = self._data[:n] + body_rep + self._data[f + 1 :]

        return expanded
