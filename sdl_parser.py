import asyncio
import importlib
import inspect
import os
import shutil
import sys
import time

import aiofiles
from pcpp.pcmd import CmdPreprocessor


import utils


if len(sys.argv) != 2:
    print("Usage: python sdl_parser.py <path-to-bindgen-module>")
    sys.exit(1)

mod = importlib.import_module(sys.argv[1])
_vis = [mem for mem in inspect.getmembers(mod) if mem[0] == "Visitor"]
if not _vis:
    print("Module does not contain a Visitor class")
    sys.exit(1)
else:
    visitor = getattr(mod, _vis[0][0])


async def parse_file(*args, input: str, output: str):
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

    async with aiofiles.open(output, "r") as f:
        infile = await f.read()

    parser = utils.parser()
    tree = parser.parse(infile.encode())
    return tree


async def parse_query(file: str):
    async with aiofiles.open(file, "r") as f:
        query_txt = await f.read()

    query = utils.query(query_txt)
    return query


async def parse_extension(ext: str, query):
    tree = await parse_file(
        input=, # path to extension header
        # input=f"include/SDL3_{ext}/SDL_{ext}.h",
        output=, # path where to save preprocessed file
        # output=f"out/cs/pp/SDL_{ext}.i",
    )

    root = tree.root_node

    # vis = visitor(
    #     # inpath=, # path to extension header
    #     inpath=f"include/SDL3_{ext}/SDL_{ext}.h",
    #     # outpath=, # path to save generated code
    #     outpath=f"out/cpp/SDL_{ext}.g.cppm",
    #     # header=, # header include
    #     header=f"SDL3/SDL_{ext}.h",
    #     # module=, # generated module name
    #     module=f"sdl.{ext}",
    #     # namespace=, # namespace for generated code
    #     namespace=f"sdl_{ext}",
    # )

    vis = visitor(
        out=, # path to save generated C# code
        # out=f"out/cs/SDL_{ext}.g.cs",
        dll=f"SDL_{ext}.dll", # WARNING: don't touch
        clazz=, # class name
        # clazz=f"SDL_{ext}",
        imp="using static SDL3.SDL;", # WARNING: don't touch
    )

    for i, rules in query.matches(root):
        vis.visit(rules)


async def main():
    tree, query = await asyncio.gather(
        parse_file(
            "-I",
            "include",
            input=, # path to SDL.h
            # input="include/SDL3/SDL.h",
            output=, # path to save preprocessed file
            # output="out/cs/pp/SDL.i",
        ),
        parse_query("query.scm"),
    )

    root = tree.root_node

    # vis = visitor(
    #     # inpath=, # path to SDL.h
    #     inpath="include/SDL3/SDL.h",
    #     # outpath=, # path to save generated code
    #     outpath="out/cpp/SDL.g.cppm",
    #     # header=, # header include
    #     header="SDL3/SDL.h",
    #     # module=, # generated module name
    #     module="sdl",
    #     # namespace=, # namespace for generated code
    #     namespace="sdl",
    # )

    vis = visitor(
        out=, # path to save generated code
        # out="out/cs/SDL.g.cs",
        dll="SDL3.dll", # WARNING: don't touch
        # clazz="SDL",
        clazz=, # class name
        imp="", # WARNING: don't touch
    )

    for i, rules in query.matches(root):
        vis.visit(rules)

    exts = # what extensions to parse
    # exts = ["image", "mixer", "ttf"]
    for ext in exts:
        await parse_extension(ext, query)

    # copy any file from the gen folder to the out folder
    gen = mod.__name__[mod.__name__.find(".") + 1 :]
    if os.path.exists(f"gen/{gen}/"):
        for file in os.listdir(f"gen/{gen}/"):
            shutil.copy(f"gen/{gen}/{file}", f"out/{gen}/{file}")


start = time.time()

asyncio.run(main())

print(f"Elapsed: {time.time() - start:.2f}s")
