import sys
import time

from _codegen_module_impl import codegen

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(
            """Usage:
    python sdl_parser.py <path-to-bind-gen-module> <gen-args>...

    To write your own generator, make a new `gen/<my_gen>.py` file and derive a `Visitor` class from `visitor.VisitorBase`.
    Then you can use it as `python sdl_parser.py gen.my_gen`.
"""
        )
        sys.exit(1)

    start = time.time()
    codegen(sys.argv[1])
    print(f"Elapsed: {time.time() - start:.2f}s")
