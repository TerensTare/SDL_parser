
# Q&A

Q: How do I use the C++ generator?
A: Just like how you would use the other generators, by running: `py sdl_parser.py gen.cpp`. You can specify the following parameters:
    `--module`: a format string for the module name. Defaults to `sdl.{ext}`.
    `--namespace`: a format string for the namespace containing the generated code. Defaults to `sdl::{ext}`


Q: What compiler do I need to use the code?
A: You need a compiler that supports C++20 modules.


Q: How do I use the generated code?
A: You simply import the modules you want on your code and use the functions/types as you would with any C++ code.

Q: How do I build the code?
A:  You need to consult the documentation of your compiler on how to build modules, but below there are commands showing how to build the provided example (example.cpp) with the main SDL module (`SDL.g.cppm`) on the three main compilers: GCC, Clang and MSVC. Remember to use `example-sdl2.cpp` instead of `example.cpp` if you have generated SDL2 headers.
```sh
# For GCC, warning: untested code
# Apparently with GCC you have to build everything at once
g++ -std=c++20 -fmodules-ts -o example example.cpp SDL.g.cppm -I<your-include-paths> -l<sdl-lib>


# For Clang, warning: untested code
clang -c -std=c++20 SDL.g.cppm -Xclang -emit-module-interface -o SDL.g.pcm -I<your-include-paths>
# No include paths are needed when building the executable
clang --std=c++20 -fprebuilt-module-path=. -fmodule-file=sdl=SDL.g.pcm example.cpp SDL.g.cppm -o example -l<sdl-lib>

# For MSVC
cl /std:c++20 /c SDL.g.cppm /TP /interface /I <your-include-paths>
# Notice no include paths are needed when building the executable
cl /std:c++20 example.cpp /link SDL.g.obj <sdl-library>
```



The SDL modules need to be built only once and can be used freely after that.

Q: What difference does the generated code have over the regular SDL code?
A: Here's a list of changes that the generator applies:
- Everything is located inside a namespace, depending on the unit they are part of.
- The names have the prefix stripped (eg. `SDL_Init` is `sdl::Init`).
- Macros are now `constexpr` functions, as macros and static variables cannot be exported from modules.
- Enums and bitflags are strongly typed (as in `enum class`). Bitflags also use the alias type as underlying type.