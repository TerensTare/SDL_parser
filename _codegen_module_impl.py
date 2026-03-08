import importlib
import inspect
import os
import shutil
import sys
import warnings

from pcpp.pcmd import CmdPreprocessor

import utils
from setup import PATH_BY_UNIT, SDL_ROOT
from visitor import VisitorBase, _Visitor


def os_defines() -> list[str]:
    match sys.platform:
        case "aix":
            return ["-D", "_AIX"]

        case "android":
            return ["-D", "__ANDROID__", "-D", "ANDROID"]

        case "cygwin":
            return ["-D", "_WIN32", "-D", "__CYGWIN__"]

        case "darwin":
            return ["-D", "__APPLE__", "-D", "__MACH__"]

        case "emscripten":
            return ["-D", "__EMSCRIPTEN__"]

        case "ios":
            return ["-D", "__APPLE__", "-D", "__IOS__"]

        case "linux":
            return ["-D", "__linux__"]

        case "wasi":
            return ["-D", "__wasi__"]

        case "win32":
            return [
                "-D",
                "_WIN32",
                "-D",
                "_MSC_VER=1900",  # VS2015 should be enough
                "-U",
                "__MACH__",  # save us ~500 lines of output
                "-U",
                "__GNUC__",
                "-U",
                "__clang__",
                "-U",
                "__MWERKS__",
                "-U",
                "__BORLANDC__",
            ]

        case _:
            warnings.warn(
                f"""Your platform ({sys.platform}) is not handled by SDL_parser.
                Please double-check the output and report if it's correct or not."""
            )
            return []


def parse_file(*args, input: str, output: str):
    os.makedirs(os.path.dirname(output), exist_ok=True)

    _ = CmdPreprocessor(
        argv=[
            "<dummy-arg-doesnt-matter>",
            input,
            "-o",
            output,
            *args,
            *os_defines(),
            # extern "C" confuses tree-sitter because of "unrelated" closing }
            # + preprocessed output drops by ~100 lines so why not
            "-U",
            "__cplusplus",
            "-D",
            "SDL_MAIN_USE_CALLBACKS",  # test
            "-D",
            "SDLCALL=",  # tree-sitter has a hard time parsing __cdecl
            "-D",
            "SDL_RESTRICT=/* restrict */",  # just for docs
            "-D",
            "SDL_PRINTF_VARARG_FUNC(x)=",  # save us some time and headaches
            "-D",
            "SDL_PRINTF_VARARG_FUNCV(x)=",  # save us some time and headaches
            "-D",
            "SDL_PRINTF_FORMAT_STRING=",  # save us some time and headaches
            "-D",
            "SDL_THREAD_ANNOTATION_ATTRIBUTE__(x)=",  # save us some time and headaches
            "-D",
            "SDL_DECLSPEC=",  # save us some time and headaches
            "-D",
            "SDLMAIN_DECLSPEC=",  # save us some time and headaches
            "-U",
            "SDL_MAIN_EXPORTED",  # for now
            "-U",
            "SDL_PLATFORM_PRIVATE_MAIN",  # a good default
            "-D",
            "SDL_DEPRECATED=",  # save us some time and headaches
            "-D",
            "SDL_UNUSED=",  # save us some time and headaches
            "-D",
            "SDL_ASSERT_LEVEL=1",  # save us some time and headaches
            "-D",
            "SDL_NODISCARD=",  # save us some time and headaches
            "-D",
            "SDL_NORETURN=",  # save us some time and headaches
            "-D",
            "SDL_ANALYZER_NORETURN=",  # save us some time and headaches
            "-D",
            "SDL_HAS_BUILTIN(x)=0",  # save us some time and headaches
            "-D",
            "SDL_ALIGNED(x)=",  # save us some time and headaches; ~400 lines removed
            "-D",
            "SDL_MALLOC=",  # save us some time and headaches
            "-D",
            "SDL_ALLOC_SIZE=",  # save us some time and headaches
            "-D",
            "SDL_ALLOC_SIZE2=",  # save us some time and headaches
            "-D",
            "SDL_BYTEORDER=SDL_LIL_ENDIAN",  # save us some time and headaches
            "-D",
            "SDL_FLOATWORDORDER=SDL_LIL_ENDIAN",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMCPY",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMMOVE",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMSET",  # save us some time and headaches
            "-D",
            "SDL_COMPILE_TIME_ASSERT",  # save us some time and headaches
            "-D",
            "SDL_AssertBreakpoint",  # save us some time and headaches
            "-D",
            "SDL_FALLTHROUGH=",  # save us some time and headaches
            "-D",
            "NULL=0",  # save us some time and headaches
            "-D",
            "SDL_INLINE=",  # save us some time and headaches
            "-D",
            "SDL_FORCE_INLINE=",  # save us some time and headaches
            "-D",
            "DOXYGEN_SHOULD_IGNORE_THIS",  # we are not interested anything doxygen doesn't want
            "-U",
            "SDL_WIKI_DOCUMENTATION_SECTION",  # this is never defined (we're not building the wiki)
            "-D",
            "SDL_BeginThreadFunction",
            "-D",
            "SDL_EndThreadFunction",
            "-D",
            "SDL_platform_defines_h_",  # save us some time and headaches
            "-D",
            "SDL_oldnames_h_",  # save us some time and headaches
            "-D",
            "SDL_stdinc_h_",  # save us some time and headaches
            "-D",
            "SDL_version_h_",  # save us some time and headaches
            "-D",
            "SDL_assert_h_",  # HACK, remove if we care about assertions eventually; this removes ~1300 lines from output
            "-D",
            "SDL_hidapi_h_",  # we don't care about this
            # we are not including SDL_stdinc.h, but this is needed
            # the cast to `int` is needed since this is used on enums
            # and enums are considered `int` in C
            "-D",
            """SDL_FOURCC(A, B, C, D)=\
    (int)((SDL_static_cast(Uint32, SDL_static_cast(Uint8, (A))) << 0) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (B))) << 8) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (C))) << 16) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (D))) << 24))""",
            "-D",
            "SDL_static_cast(T, V)=((T)(V))",  # save us some time and headaches
            # skip this as we need them to detect platform-specific code
            "--passthru-defines",  # keep defines in output
            "--passthru-unknown-exprs",  # NOTE: this keeps the ifdef/endif blocks
            "--passthru-unfound-includes",  # skip missing includes
            "--passthru-comments",  # keep comments in output
            "--output-encoding",
            "utf-8",  # output encoding
            "--line-directive",
            "",  # don't output line directives
        ]
    )

    with open(output, "r") as f:
        infile = f.read()

    parser = utils.parser()
    tree = parser.parse(infile.encode())
    return tree


def parse_query(file: str):
    with open(file, "r") as f:
        query_txt = f.read()

    query = utils.query(query_txt)
    return query


def parse_extension(gen: str, ext: str, query, visitor: type[VisitorBase]):
    sdl_ext = f"SDL_{ext}"
    tree = parse_file(
        input=f"{SDL_ROOT}/{PATH_BY_UNIT[sdl_ext]}",
        output=f"out/{gen}/pp/{sdl_ext}.i",
    )

    root = tree.root_node

    vis = _Visitor(visitor, ext)

    for i, rules in query.matches(root):
        vis.visit(rules)


def codegen(mod_name: str):
    mod = importlib.import_module(mod_name)
    assert mod is not None
    gen = mod.__name__[mod.__name__.find(".") + 1 :]

    _vis = [mem for mem in inspect.getmembers(mod) if mem[0] == "Visitor"]
    if not _vis:
        print("Module does not contain a class named `Visitor`")
        sys.exit(1)

    visitor = getattr(mod, _vis[0][0])
    query = parse_query("query.scm")

    tree = parse_file(
        "-I",
        SDL_ROOT,
        input=f"{SDL_ROOT}/{PATH_BY_UNIT['SDL']}",
        output=f"out/{gen}/pp/SDL.i",
    )
    root = tree.root_node

    vis = _Visitor(visitor, "SDL")

    for _, rules in query.matches(root):
        vis.visit(rules)

    for ext in PATH_BY_UNIT.keys():
        if ext == "SDL":
            continue
        parse_extension(gen, ext[4:], query, visitor)

    # copy any file from the gen folder to the out folder
    if os.path.exists(f"gen/{gen}/"):
        for file in os.listdir(f"gen/{gen}/"):
            if os.path.exists(f"out/{gen}/{file}"):
                os.remove(f"out/{gen}/{file}")

            shutil.copy(f"gen/{gen}/{file}", f"out/{gen}/{file}")
