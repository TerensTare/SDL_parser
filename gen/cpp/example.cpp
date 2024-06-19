
import sdl;

int main(int, char **)
{
    if (sdl::Init(sdl::InitFlags::VIDEO) != 0)
    {
        sdl::ShowSimpleMessageBox(
            sdl::MessageBoxFlags::ERROR,
            "Error",
            "Failed to initialize SDL",
            nullptr
        );
        return 1;
    }

    auto window = sdl::CreateWindow(
        "Hello world!",
        640, 480,
        sdl::WindowFlags::OPENGL
    );

    if (window == nullptr)
    {
        sdl::ShowSimpleMessageBox(
            sdl::MessageBoxFlags::ERROR,
            "Error",
            "Failed to create window",
            nullptr
        );
        return 1;
    }

    auto renderer = sdl::CreateRenderer(window, nullptr);

    if (renderer == nullptr)
    {
        sdl::ShowSimpleMessageBox(
            sdl::MessageBoxFlags::ERROR,
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
        sdl::RenderLine(renderer, 320, 240, 400, 300);

        sdl::RenderPresent(renderer);

        sdl::Delay(16);
    }

    // this is still manual for now :(

    sdl::DestroyRenderer(renderer);
    sdl::DestroyWindow(window);
    sdl::Quit();

    return 0;
}