
# SDL_parser

This repo contains a Python script based on tree-sitter that parses SDL headers (SDL_image, SDL_mixer and SDL_ttf supported as well) and allows you to create language bindings of your own choice from the parsed ASTs.


## Setup

To run the project you need Python>=3.10. Dependencies can be acquired with

```py
pip install -r requirements.txt
```

Also, before you can run the script, you need to edit `PATH_BY_UNIT` in [setup.py](./setup.py) to choose the units you want to parse (or else the script will fail). The file contains default paths for each unit but you can edit them as you see fit. Furthermore, you can edit `SDL_ROOT` which is the common path where all your SDL headers reside, relative to the project's root. All that's left is to pick a generator and run `py sdl_parser.py gen.<generator-file-name> --<args>=<values>` (eg. `py sdl_parser.py gen.cpp --module="sdl.{ext}"` for C++ bindings) and have your bindings generated in `out/<generator-file-name>/`.

## Constructs

NOTE: This part is for people interested in writing their own bindings. Skip this section if you just want to use an already available generator.

The parser currently divides parsed content into different categories, each corresponding to a `visit_*` function in a visitor. The following constructs are recognized so far:

- Functions: Just regular functions, eg. `SDL_AsyncIO* SDL_AsyncIOFromFile(const char* file, const char* mode);`
- Callback: A `typedef` to a function pointer. eg. `typedef void (*SDL_CleanupPropertyCallback)(void *userdata, void *value);`
- Function macros: A macro with parameters, eg. `#define SDL_Swap16(a, b)`
- Bitflag: A `typedef` to an integer type following by one or more constant macros, eg.
```cpp
typedef Uint32 SDL_SurfaceFlags;

#define SDL_SURFACE_PREALLOCATED    0x00000001u
#define SDL_SURFACE_LOCK_NEEDED     0x00000002u
#define SDL_SURFACE_LOCKED          0x00000004u
#define SDL_SURFACE_SIMD_ALIGNED    0x00000008u
```
- Enum: Just a regular `enum`, eg.
```cpp
enum ScaleMode
{
    INVALID = SDL_SCALEMODE_INVALID,
    NEAREST = SDL_SCALEMODE_NEAREST,
    LINEAR = SDL_SCALEMODE_LINEAR,
    PIXELART = SDL_SCALEMODE_PIXELART,
};
```

- Opaque: An opaque type definition, eg. `typedef struct SDL_Window SDL_Window;`
- Struct: Just a regular non-opaque `struct`.
- Union: Just a regular union definition.
- Alias: A `typedef` that aliases to an existing type, eg. `typedef Uint32 SDL_CameraID;`
- Property: A constant macro that defines a property name, eg. `#define SDL_PROP_NAME_STRING "SDL.name"`. A property macro contains `_PROP_` in its name and its value is a static string (`const char *`).
- Constant: A constant defined as a (non-property) macro, eg. `#define SDL_ELF_NOTE_DLOPEN_PRIORITY_SUGGESTED   "suggested"`

Additionally, the parser detects `#if defined(SDL_PLATFORM_*)` blocks and reports the platforms for the block accordingly.

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
