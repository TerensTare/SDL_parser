from tree_sitter import Node


from setup import PATH_BY_UNIT
from visitor import visitor
from utils import only

_PRELUDE: str = """
module;

#include <type_traits>
#include <{0}>

export module {1};

#define REGULAR_ENUM(ty) \\
    constexpr bool operator ==(std::underlying_type_t<ty> a, ty b) noexcept \\
    {{ \\
        return a == static_cast<std::underlying_type_t<ty>>(b); \\
    }} \\
    constexpr bool operator ==(ty a, std::underlying_type_t<ty> b) noexcept \\
    {{ \\
        return static_cast<std::underlying_type_t<ty>>(a) == b; \\
    }}

#define BITFLAG_ENUM(ty) \\
    constexpr ty operator|(ty a, ty b) noexcept \\
    {{ \\
        return static_cast<ty>(static_cast<std::underlying_type_t<ty>>(a) | static_cast<std::underlying_type_t<ty>>(b)); \\
    }} \\
    constexpr ty operator&(ty a, ty b) noexcept \\
    {{ \\
        return static_cast<ty>(static_cast<std::underlying_type_t<ty>>(a) & static_cast<std::underlying_type_t<ty>>(b)); \\
    }} \\
    constexpr ty operator^(ty a, ty b) noexcept \\
    {{ \\
        return static_cast<ty>(static_cast<std::underlying_type_t<ty>>(a) ^ static_cast<std::underlying_type_t<ty>>(b)); \\
    }} \\
    constexpr ty operator~(ty a) noexcept \\
    {{ \\
        return static_cast<ty>(~static_cast<std::underlying_type_t<ty>>(a)); \\
    }} \\
    constexpr ty& operator|=(ty& a, ty b) noexcept \\
    {{ \\
        return a = a | b; \\
    }} \\
    constexpr ty& operator&=(ty& a, ty b) noexcept \\
    {{ \\
        return a = a & b; \\
    }} \\
    constexpr ty& operator^=(ty& a, ty b) noexcept \\
    {{ \\
        return a = a ^ b; \\
    }}

export namespace {2}
{{
"""


def _cut_similarity(model: str, target: str) -> str:
    mi, ti = 0, 0
    f = len(model)
    last = 0

    while mi < f:
        if target[ti] == "_":
            ti += 1
            last = ti
            continue
        elif model[mi].upper() == target[ti]:
            ti += 1
        else:
            break

        mi += 1

    if target[ti] == "_":
        ti += 1
    else:
        ti = last

    if target[ti].isnumeric():
        ti -= 1
    # elif mi == f:
    #     ti = last

    return target[ti:]


@visitor
class CppVisitor:
    def __init__(
        self,
        unit: str,
        *,
        module: str = "sdl.{ext}",
        namespace: str = "sdl::{ext}",
    ) -> None:
        """
        Generate a C++ module from the parsed SDL header file.

        Args:
            unit (str): The SDL unit to generate the module for.
            module (str, optional): The module name to use. Defaults to "sdl.{ext}".
            namespace (str, optional): The namespace to use. Defaults to "sdl::{ext}".
        """

        self._enum = set()

        mod = module.format(ext=unit)
        ns = "sdl" if unit == "SDL" else namespace.format(ext=unit)

        if unit != "SDL":
            unit = f"SDL_{unit}"

        header = PATH_BY_UNIT[unit].split("/")[-1][:-2]  # remove ".h"
        self._file = open(f"out/cpp/{header}.g.cppm", "w")
        self._file.write(_PRELUDE.format(PATH_BY_UNIT[unit], mod, ns))

    def __del__(self) -> None:
        self._file.write("}\n")
        self._file.close()

    def start_platform_code(self, platforms: list[str]):
        self._file.write(
            f"#if {' || '.join(map(lambda p: f'defined({p})', platforms))}\n"
        )

    def end_platform_code(self):
        self._file.write("#endif\n\n")

    def visit_function(self, rules: dict[str, Node | list[Node]]):
        name = rules["function.name"]
        ret = rules["function.return"].text.decode()
        params = rules["function.params"]

        if "function.return_ptr" in rules:
            ret += "*"
        if any(only("type_qualifier", rules["function.decl"])):
            ret = "const " + ret

        body_ret = "" if ret == "void" else "return "

        def extract_type(node: Node) -> str:
            if node.text == b"void":
                return "void"

            ty = node.child_by_field_name("type").text.decode()
            decl = node.child_by_field_name("declarator")

            if ty[4:] in self._enum:
                ty = ty[4:]

            if node.named_children[0].type == "type_qualifier":
                ty = node.named_children[0].text.decode() + " " + ty

            while decl is not None and decl.type == "pointer_declarator":
                decl = decl.child_by_field_name("declarator")
                ty += "*"

            return ty

        def extract_name(node: Node) -> str:
            decl = node.child_by_field_name("declarator")

            if decl is None:
                return ""

            while not decl.type.endswith("identifier"):
                match decl.type:
                    case "pointer_declarator":
                        decl = decl.child_by_field_name("declarator")

                    case "type_qualifier":
                        decl = decl.child_by_field_name("declarator")

                    case "function_declarator":
                        # function_declarator > parenthesized_declarator > pointer_declarator > identifier
                        decl = decl.child_by_field_name("declarator")
                        decl = decl.named_children[0]
                        decl = decl.child_by_field_name("declarator")

                    case "array_declarator":
                        decl = decl.child_by_field_name("declarator")

                    case _:
                        break

            return decl.text.decode()

        def cast_if_enum(ty: str, name: str) -> str:
            if ty.startswith("const "):
                ty = ty[6:]
                # TODO: take care of `const Enum *` case

            if ty[-1] == "*":
                ty_tmp = ty[:-1]

                if ty_tmp in self._enum:
                    return f"(SDL_{ty_tmp}*)({name})"

            if ty in self._enum:
                return f"(SDL_{ty})({name})"
            return name

        ps = list(only("parameter_declaration", params))

        ps_types = [extract_type(p) for p in ps]
        ps_name = [extract_name(p) for p in ps]

        for i, n in enumerate(ps_name):
            if n == "" and ps_types[i] != "void":
                print(f"Note: Skipping {name.text.decode()} due to unnamed parameter")
                return

        self._file.write(f"\n    {ret} {name.text[4:].decode()}(")

        self._file.write(", ".join(f"{ty} {nm}" for ty, nm in zip(ps_types, ps_name)))

        self._file.write(f""")
    {{
        {body_ret}{name.text.decode()}({", ".join(cast_if_enum(t, n) for t, n in zip(ps_types, ps_name))});
    }}
""")

    def visit_enum(self, rules: dict[str, Node | list[Node]]):
        name = rules["enum.name"]
        entries = rules["enum.entries"]

        self._file.write(f"""
    enum class {name.text[4:].decode()}
    {{
""")

        for entry in only("enumerator", entries):
            entry_name = entry.child_by_field_name("name")
            clean_name = _cut_similarity(
                name.text[4:].decode(),
                entry_name.text[4:].decode(),
            )

            self._file.write(f"        {clean_name} = {entry_name.text.decode()},\n")

        self._file.write(f"    }};\n    REGULAR_ENUM({name.text[4:].decode()});\n")

        self._enum.add(name.text[4:].decode())

        pass

    def visit_opaque(self, rules: dict[str, Node | list[Node]]):
        name = rules["opaque.name"]

        al = name.text[4:].decode() if name.text[4:] == b"_" else name.text.decode()

        self._file.write(f"\n    using {al} = {name.text.decode()};\n")
        pass

    def visit_struct(self, rules: dict[str, Node | list[Node]]):
        name = rules["struct.name"]

        self._file.write(
            f"\n    using {name.text[4:].decode()} = {name.text.decode()};\n"
        )
        pass

    def visit_union(self, rules: dict[str, Node | list[Node]]):
        name = rules["union.name"]

        self._file.write(
            f"\n    using {name.text[4:].decode()} = {name.text.decode()};\n"
        )
        pass

    def visit_bitflag(self, rules: dict[str, Node | list[Node]]):
        name = rules["bitflag.name"]
        ty = rules["bitflag.type"]
        flags = rules["flag"]

        self._enum.add(name.text[4:].decode())
        name = name.text[4:].decode()

        self._file.write(f"""
    enum class {name} : {ty.text.decode()}
    {{
""")

        for entry in filter(lambda x: x.type == "preproc_def", flags):
            entry_name = entry.child_by_field_name("name")
            clean_name = _cut_similarity(
                name,
                entry_name.text[4:].decode(),
            )

            self._file.write(f"        {clean_name} = {entry_name.text.decode()},\n")

        self._file.write(f"    }};\n    BITFLAG_ENUM({name});\n")

        pass

    def visit_alias(self, rules: dict[str, Node | list[Node]]):
        name = rules["alias.name"]
        ty = rules["alias.type"]

        self._file.write(
            f"\n    using {name.text[4:].decode()} = {ty.text.decode()};\n"
        )

    def visit_callback(self, rules: dict[str, Node | list[Node]]):
        pass

    def visit_fn_macro(self, rules: dict[str, Node | list[Node]]):
        pass

    def visit_const(self, rules: dict[str, Node | list[Node]]):
        name = rules["const.name"].text
        value = rules["const.value"].text

        # these are macros that alias to other functions, we don't need them
        # so just skip them
        if any(c for c in name if c >= 97 and c <= 122):
            return

        # these values are supposed to be private or C-specific (eg. __FILE__ and __LINE__)
        if value.find(b"__") != -1:
            return

        self._file.write(
            f"\n    constexpr auto {name[4:].decode()}() {{ return {value.decode()}; }}\n"
        )

        pass
