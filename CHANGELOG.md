
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## 2024-06-19

### Added

- Examples showing how to use the generated code. Check your generator's folder inside `gen`.
- C++20 modules generator ([code](./gen/cpp.py)). Still WIP and not final.
- Decorator `@visitor` to ease writing custom generators.
- Documentation on how to write your own code generator ([docs](./docs/bindings-my-way.md)).


### Changed

- Adapted `@visitor` decorator on existing visitors.
- Modified the C# generator to get closer to the other generators' style.


## 2024-06-18

### Added

- This changelog file. Yay!
- Tree-sitter query that parses opaque types of form `typedef struct X *Y;` (needed for `SDL_GLContext`).
- [visitor.py](./visitor.py) to make writing your own binding generator easier. Implement the abstract methods and let the script handle the rest.


### Changed

- Renamed `main.py` to [sdl_parser.py](./sdl_parser.py).
- Generators are now located inside `gen`, and by convention have a separate folder for files they need (eg. impl files/other).
- You can now specify your own generator by running `python sdl_parser.py <gen-module>` (eg. `py sdl_parser.py gen.cs` for the C# generator). Please make sure to check [sdl_parser.py](./sdl_parser.py) and configure the generating steps as desired.
