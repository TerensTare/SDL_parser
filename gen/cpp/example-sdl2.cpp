
import sdl.SDL;

int main(int, char **)
{
    if (sdl::Init(sdl::INIT_EVERYTHING()) != 0)
    {
        sdl::ShowSimpleMessageBox(
            (Uint32)sdl::MessageBoxFlags::ERROR,
            "Error",
            "Failed to initialize SDL",
            nullptr
        );
        return 1;
    }

    auto window = sdl::CreateWindow(
        "Hello world!",
        sdl::WINDOWPOS_CENTERED(), sdl::WINDOWPOS_CENTERED(),
        640, 480,
        (Uint32)sdl::WindowFlags::SHOWN
    );

    if (window == nullptr)
    {
        sdl::ShowSimpleMessageBox(
            (Uint32)sdl::MessageBoxFlags::ERROR,
            "Error",
            "Failed to create window",
            nullptr
        );
        return 1;
    }

    auto renderer = sdl::CreateRenderer(window, -1, (Uint32)sdl::RendererFlags::ACCELERATED);

    if (renderer == nullptr)
    {
        sdl::ShowSimpleMessageBox(
            (Uint32)sdl::MessageBoxFlags::ERROR,
            "Error",
            "Failed to create renderer",
            nullptr
        );
        return 1;
    }

    sdl::Event event;
    bool running = true;

    while (running)
    {
        while (sdl::PollEvent(&event))
        {
            if (event.type == sdl::EventType::QUIT)
            {
                running = false;
            }
        }

        sdl::SetRenderDrawColor(renderer, 0, 0, 0, 255);
        sdl::RenderClear(renderer);

        sdl::SetRenderDrawColor(renderer, 255, 255, 255, 255);
        sdl::RenderDrawLine(renderer, 320, 240, 400, 300);

        sdl::RenderPresent(renderer);

        sdl::Delay(16);
    }

    // this is still manual for now :(

    sdl::DestroyRenderer(renderer);
    sdl::DestroyWindow(window);
    sdl::Quit();

    return 0;
}