
If you want to generate bindings to a language that is not currently supported, you can write your own generator.

## Setting up your generator

First you need to setup your generator by making a new file in `gen/` with the following content:

```py
from visitor import VisitorBase

# important: class should be named Visitor and derive from VisitorBase
class Visitor(VisitorBase):
    pass
    
_ = Visitor("") # this will error if you don't implement all needed methods. Your type checker will tell you what you need to derive. You can remove this line when implementing all methods.
```

## Doing the rest of the job

![](image.png)

Now all that's left is a matter of implementing all the needed abstract methods and calling `py sdl_parser.py gen.<your-gen-file> --my-args=my-values` when you are done. The `visitor.VisitorBase` class contains documentation showing the structure of the data that is passed to each of the `visit_*` methods. For further help, you can check the already present generators such as the [C++](../gen/cpp.py) one. As for the constructor parameters, they are passed from the command lines. Keyword parameters (those after `*` in the constructor) need to be specified if they don't have a default value (or else the script will tell you to specify them and terminate) and can be omitted if they have a default value.

## Adding pre-made files

If you need to provide certain files along with your generated code, you can place them inside the `gen/<your-gen-file>/` folder and they will be automatically copied to `out/<your-gen-file>/` once everything is done (eg. the `cs` generator has a `String.cs` file inside the `gen/cs/` folder that contains string-related utilities). Such files can be files that adapt certain APIs or examples that show how to use the bindings.

If you think your generator would be helpful to the community, please submit a [PR](https://github.com/TerensTare/SDL_parser/pulls) to the project.
