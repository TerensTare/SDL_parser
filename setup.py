import sys

# NOTE: this is relative to `sdl_parser.py` if a relative path.
SDL_ROOT = "./include"


# NOTE: these are relative paths from SDL_ROOT,
# which defaults to "include" in the root of the project.
# All these paths should be reasonable defaults.
# Uncomment and change as needed.
PATH_BY_UNIT = {
    # "SDL": "SDL3/SDL.h",
    # "SDL_main": "SDL3/SDL_main.h",
    # "SDL_vulkan": "SDL3/SDL_vulkan.h",
    # "SDL_image": "SDL3_image/SDL_image.h",
    # "SDL_mixer": "SDL3_mixer/SDL_mixer.h",
    # "SDL_ttf": "SDL3_ttf/SDL_ttf.h",
}

# NOTE: do not touch :)
if not PATH_BY_UNIT:
    print("Error: no units chosen to parse.")
    sys.exit(1)
