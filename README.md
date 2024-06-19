
# SDL_parser

This repo contains a Python script based on tree-sitter that parses SDL headers (SDL_image, SDL_mixer and SDL_ttf supported as well) and allows you to create language bindings of your own choice from the parsed ASTs.


## Setup

To run the project you need Python>=3.10. Dependencies can be acquired with

```py
pip install -r requirements.txt
```

Also, before you can run the script, you need to provide some paths for the location of the headers and DLLs (if needed), as well as the folder where to generate the files into. They are left incomplete on purpose so you can simply run `py sdl_parser.py <generator-module-name>` (eg. `py sdl_parser.py gen.cpp` for C++ bindings) and fix the errors, however the next line provides a sample default as to make things easier.


## Supported languages

This is a list of currently supported languages:

- C++ ([example](https://gist.github.com/TerensTare/2ab3e47f832ce9ffb9c6e461651f9fdc)) (NOTE: headers must be annotated as in this [PR](https://github.com/libsdl-org/SDL/pull/9907) for C#)
- C# ([example](https://gist.github.com/TerensTare/0c0e9bde9fbfdbdf4d217496c5a7cad2))

If you want to write bindings for another language, please refer to [bindings-my-way](docs/bindings-my-way.md).



For any questions or issues, feel free to open an issue or PR. Thank you!