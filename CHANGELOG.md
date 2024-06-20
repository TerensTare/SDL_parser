
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## 2024-06-20

### Added

- Units that are not included by `SDL.h` by default (`SDL_main.h` and `SDL_vulkan.h`).
- Json generator in case you want to generate bindings from that (thank you @playmer for the idea).

### Changed

- You no longer need to modify `sdl_parser.py` to run the script. Everything you need is now organized inside [setup.py](./setup.py). The only thing you need to do is now choose which units to parse by uncommenting lines on `PATH_BY_UNIT` and setting their path as needed. You can also edit `SDL_ROOT` if that is necessary
- Visitors constructors should have a single positional argument, the other should be keyword arguments. So the signature becomes:
```py
# file gen/my.py

@visitor
class MyVisitor:
    def __init__(self, unit: str, *, arg1, arg2=42, ...): # notice the * that separates positional and keyword arguments
        # do whatever you like here
        # unit is any of the following: `SDL`, `image`, `mixer`, `ttf` 
        pass
```
Following this change, keyword arguments should be passed from the command line (in this case you would run `py sdl_parser.py `--arg1=<SomeValue>`). Note that you can skip arguments with a default value (in this case `arg2`) or specify a custom value for them.

- Switched to using sync I/O as it was not yielding a significant performance boost. As a result the project doesn't depend on `aiofiles` anymore.

### Fixed

- Some indentation issues related to the C++ generator.
- Preprocessed files are now output to the correct folder depending on the generator used by default.


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
