
# SDL_parser

This repo contains a Python script based on tree-sitter that parses SDL headers (SDL_image, SDL_mixer and SDL_ttf supported as well) and allows you to create language bindings of your own choice from the parsed ASTs.


## Setup

To run the project you need Python>=3.10. Dependencies can be acquired with

```py
pip install -r requirements.txt
```

Also, before you can run the script, you need to edit `PATH_BY_UNIT` in [setup.py](./setup.py) to choose the units you want to parse (or else the script will fail). The file contains default paths for each unit but you can edit them as you see fit. Furthermore, you can edit `SDL_ROOT` which is the common path where all your SDL headers reside, relative to the project's root. All that's left is to pick a generator and run `py sdl_parser.py gen.<generator-file-name> --<args>=<values>` (eg. `py sdl_parser.py gen.cpp --module="sdl.{ext}"` for C++ bindings) and have your bindings generated in `out/<generator-file-name>/`.


## Supported languages

This is a list of currently supported languages:

- C++ ([example](./gen/cpp/example.cpp)) (for SDL2 use [this](./gen/cpp/example-sdl2.cpp) instead)
- C# ([example](./gen/cs/Example.cs)) (NOTE: headers must be annotated as in this [PR](https://github.com/libsdl-org/SDL/pull/9907))
- JSON

If you want to write bindings for another language, please refer to [bindings-my-way](docs/bindings-my-way.md).


## Q&A

Q: Can I use this to generate SDL2 bindings?
A: Yes, but the bindings are not of the same quality as SDL3 bindings due to some coding conventions that are not present in SDL2 code. The difference is that you need to cast SDL2 enums to their underlying type when passing to functions. Also some bitflags are not recognized as enums, but rather constants. Please compare the examples on `gen/cpp` to notice the difference.


For any other questions or issues, feel free to open an issue or PR. Thank you!