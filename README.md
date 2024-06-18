
# SDL_parser

This repo contains a Python script based on tree-sitter that parses SDL headers (SDL_image, SDL_mixer and SDL_ttf supported as well) and allows you to create language bindings of your own choice from the parsed ASTs.


To run the project you need Python>=3.10. Dependencies can be acquired with

```py
pip install -r requirements.txt
```

Also, before you can run the script, you need to provide some paths for the location of the headers and DLLs (if needed), as well as the folder where to generate the files into. They are left incomplete on purpose so you can simply run `py main.py` and fix the errors, however the next line provides a sample default as to make things easier.


For now only C# is supported for generating bindings, but supported for more languages will be added in the future. In the meantime, if you want to write your own generator, please check [cs.py](./cs.py) to understand how the generator gets the data from the parsed files.

The basic idea is that the generator visits each node that matches the tree sitter queries specified in [query.scm](./query.scm) and calls a function depending on the type of the node. This process is handled by the `visit` method, which delegates the node to the corresponding method. Then each method does its own magic to do the codegen.


For any questions or issues, feel free to open an issue or PR. Thank you!