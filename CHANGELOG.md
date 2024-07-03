
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [Unreleased]

### Added

- Experimental support for platform-dependent code. You should now define `start_platform_code` and `end_platform_code` on your generators to be run on each item inside a platform-specific code. The built-in generators already have support for these changes. Please refer to the documentation inside `visitor.py` for more.
- README on the C++ generator discussing most common topics related to it.

### Changed

- Rewrote the C# generator to use functions from `utils`.


## 2024-06-28

### Added

- Q&A section on the [README](./README.md).
- [Example](./gen/cpp/example-sdl2.cpp) showing how to use the SDL2 C++ api.

### Changed

- The C++ generator will skip any functions with unnamed parameters. The only known case is `SDL_ReportAssertion` from SDL2.
Please note that as the documentation also suggests, you should use the `SDL_assert_*` macros if you want SDL assertions, so it shouldn't be an issue.
Also note that this behavior is not global to every generator, only to the C++ one.

### Fixed

- Bug where the script will crash if you add a new file to `gen/<your-gen>`. This happened as the script tried to delete its analogue from `out/<your-gen>`, which doesn't exist.
- The script correctly detects the current platform used by the script.
- The C++ generator now uses the correct namespace for the default module (it defaults to `sdl`, you cannot change it as of now).


## 2024-06-24

### Added

- Support for providing parameter documentation and return documentation in the JSON generator. Find it on the 'docs' field.

### Fixed

- Files on `gen/<your-gen>` are now always copied even if they exist in the destination.

### Changed

- Structure of function parameters in data generated as JSON. The new structure is as following:
```json
{
    "type" : <type>,
    "name": <name>,
    "docs": <docs>
}
````



## 2024-06-22

### Added

- New command to ease generator creation. Run `py sdl_parser.py --new <name>` and check `gen/<name>.py`.
- Utilities to help writing your own generators. Check out `only` and `split_type_name` from [utils.py](./utils.py).
- Updated guides to reflect current changes.


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
