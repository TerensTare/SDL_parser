
using System;

using static SDL3.SDL;

public class Example
{
    public static void Main(string[] args)
    {
        SDL_Init(SDL_InitFlags.SDL_INIT_VIDEO);

        var window = SDL_CreateWindow("Hello World!", 640, 480, SDL_WindowFlags.SDL_WINDOW_OPENGL);

        if (!window)
        {
            Console.WriteLine($"Failed to create window! {SDL_GetError().Str()}");
            return;
        }

        SDL_ShowSimpleMessageBox(
            SDL_MessageBoxFlags.SDL_MESSAGEBOX_INFORMATION,
            "Hello World!",
            "Welcome to SDL3 with C#!",
            window
        );

        var renderer = SDL_CreateRenderer(window, InString.Empty);

        if (!renderer)
        {
            Console.WriteLine($"Failed to create renderer! {SDL_GetError().Str()}");
            return;
        }

        bool running = true;
        uint color = 0;

        while (running)
        {
            while (SDL_PollEvent(out SDL_Event e) != 0)
            {
                if (e.type == (uint)SDL_EventType.SDL_EVENT_QUIT)
                {
                    running = false;
                }
            }

            color = (color + 1) & 0xFFFFFF;
            byte r = (byte)((color >> 16) & 0xFF);
            byte g = (byte)((color >> 8) & 0xFF);
            byte b = (byte)(color & 0xFF);


            SDL_SetRenderDrawColor(renderer, 0xFF, 0xFF, 0xFF, 0xFF);
            SDL_RenderClear(renderer);

            SDL_SetRenderDrawColor(renderer, r, g, b, 0xFF);

            var area = new SDL_FRect() { x = 160, y = 160, w = 320, h = 160 };
            SDL_RenderFillRect(renderer, ref area);

            SDL_RenderPresent(renderer);

            SDL_Delay(10);
        }

        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);

        SDL_Quit();

        return;
    }
}