import sys
from pathlib import Path

# NOTE: this is relative to `sdl_parser.py` if a relative path.
SDL_ROOT = "./include"


# NOTE: these are relative paths from SDL_ROOT,
# which defaults to "include" in the root of the project.
# All these paths should be reasonable defaults.
# Uncomment and change as needed.
PATH_BY_UNIT = {
    # "SDL": "SDL2/SDL.h",
    "SDL": "SDL3/SDL.h",
    # "SDL_main": "SDL3/SDL_main.h",
    # "SDL_vulkan": "SDL3/SDL_vulkan.h",
    # "SDL_image": "SDL3_image/SDL_image.h",
    # "SDL_mixer": "SDL3_mixer/SDL_mixer.h",
    # "SDL_ttf": "SDL3_ttf/SDL_ttf.h",
}

# Validation, don't touch

if not Path(SDL_ROOT).exists():
    print("Error: SDL_ROOT is not a valid path. Please edit setup.py.")

if not PATH_BY_UNIT:
    print("Error: no units chosen to parse. Please edit PATH_BY_UNIT in setup.py.")
    sys.exit(1)

_SDL_MODULES = {"SDL", "SDL_main", "SDL_vulkan", "SDL_image", "SDL_mixer", "SDL_ttf"}
for k, v in PATH_BY_UNIT.items():
    if k not in _SDL_MODULES:
        print(
            f"Unsupported module {k} in setup.py/PATH_BY_UNIT. Expected one of {_SDL_MODULES}."
        )
        sys.exit(1)
    if not (Path(SDL_ROOT) / v).exists():
        print(f"Invalid path {v} for module {k} in setup.py/PATH_BY_UNIT.")
        sys.exit(1)
