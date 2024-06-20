import importlib
import inspect
import os
import shutil
import sys
import time

from pcpp.pcmd import CmdPreprocessor


from setup import PATH_BY_UNIT, SDL_ROOT
import utils


if len(sys.argv) < 2:
    print("Usage: python sdl_parser.py <path-to-bind-gen-module> <gen-args>...")
    sys.exit(1)

mod = importlib.import_module(sys.argv[1])
gen = mod.__name__[mod.__name__.find(".") + 1 :]

_vis = [mem for mem in inspect.getmembers(mod) if mem[0] == "Visitor"]
if not _vis:
    print("Module does not contain a Visitor class")
    sys.exit(1)
else:
    visitor = getattr(mod, _vis[0][0])


def parse_file(*args, input: str, output: str):
    os.makedirs(os.path.dirname(output), exist_ok=True)

    _ = CmdPreprocessor(
        argv=[
            "<dummy-arg-doesnt-matter>",
            input,
            "-o",
            output,
            *args,
            "-D",
            "SDLCALL=",  # tree-sitter has a hard time parsing __cdecl
            "-D",
            "SDL_DECLSPEC=",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMCPY",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMMOVE",  # save us some time and headaches
            "-D",
            "SDL_SLOW_MEMSET",  # save us some time and headaches
            "-D",
            "SDL_COMPILE_TIME_ASSERT",  # save us some time and headaches
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
            "SDL_oldnames_h_",  # save us some time and headaches
            "-D",
            "SDL_stdinc_h_",  # save us some time and headaches
            "-D",
            "SDL_version_h_",  # save us some time and headaches
            "-D",
            "SDL_hidapi_h_",  # we don't care about this
            "-D",
            # we are not including SDL_stdinc.h, but this is needed
            # the cast to `int` is needed since this is used on enums
            # and enums are considered `int` in C
            """SDL_FOURCC(A, B, C, D)=\
    (int)((SDL_static_cast(Uint32, SDL_static_cast(Uint8, (A))) << 0) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (B))) << 8) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (C))) << 16) | \
     (SDL_static_cast(Uint32, SDL_static_cast(Uint8, (D))) << 24))""",
            "-D",
            "SDL_static_cast(T, V)=((T)(V))",  # save us some time and headaches
            "-N",
            "WINAPI_FAMILY_WINRT",  # workaround
            "--passthru-defines",  # keep defines in output
            # "--passthru-unknown-exprs",
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


def parse_extension(ext: str, query):
    sdl_ext = f"SDL_{ext}"
    tree = parse_file(
        input=f"{SDL_ROOT}/{PATH_BY_UNIT[sdl_ext]}",
        output=f"out/{gen}/pp/{sdl_ext}.i",
    )

    root = tree.root_node

    vis = visitor(ext)

    for i, rules in query.matches(root):
        vis.visit(rules)


def main():
    query = parse_query("query.scm")

    tree = parse_file(
        "-I",
        SDL_ROOT,
        input=f"{SDL_ROOT}/{PATH_BY_UNIT['SDL']}",
        output=f"out/{gen}/pp/SDL.i",
    )
    root = tree.root_node

    vis = visitor("SDL")

    for i, rules in query.matches(root):
        vis.visit(rules)

    for ext in PATH_BY_UNIT.keys():
        if ext == "SDL":
            continue
        parse_extension(ext[4:], query)

    # copy any file from the gen folder to the out folder
    if os.path.exists(f"gen/{gen}/"):
        for file in os.listdir(f"gen/{gen}/"):
            shutil.copy(f"gen/{gen}/{file}", f"out/{gen}/{file}")


if __name__ == "__main__":  # At this point, this is just for readability
    start = time.time()
    main()
    print(f"Elapsed: {time.time() - start:.2f}s")
