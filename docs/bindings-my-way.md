
If you want to generate bindings to a language that is not currently supported, you can write your own generator.

First you create a python file inside the `gen` folder and add the following code to the file:
```py

from tree_sitter import Node
from visitor import visitor

@visitor
class MyVisitor: # pick a name
    def visit_function(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_enum(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_opaque(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_struct(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_union(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_bitflag(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_alias(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_callback(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_fn_macro(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

    def visit_const(self, rules: dict[str, Node | list[Node]]):
        raise NotImplementedError

```

Now all that's left is a matter replacing all those `raise`s with your code and calling `py sdl_parser.py gen.<your-gen-file>` when you are done. The visitor class contains documentation showing the structure of the data that is passed to each of the `visit_*` methods. For further help, you can check the already present generators such as the [C++](../gen/cpp.py) one.

If you need to provide certain files along with your generated code, you can place them inside the `gen/<your-gen-file>/` folder and they will be automatically copied to `out/<your-gen-file>/` once everything is done (eg. the `cs` generator has a `String.cs` file inside the `gen/cs/` folder that gets copied to `out/cs/` automatically). Such files can be files that adapt certain APIs or examples that show how to use the bindings.

If you think your generator would be helpful to the community, please submit a [PR](https://github.com/TerensTare/SDL_parser/pulls) to the project.