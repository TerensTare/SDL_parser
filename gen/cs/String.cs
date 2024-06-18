
using System;
using System.Text;
using System.Runtime.InteropServices;

// TODO:
// consider having 2048 bytes for in strings, and 2048 bytes for out strings
// since out strings might need to live longer than in strings

internal static class StringPool
{
    internal unsafe static IntPtr str(string str)
    {
        if (str == null) return IntPtr.Zero;
        
        int len = str.Length * 4 + 1;
        if (cursor + len >= 4096)
            cursor = 0; // reset the cursor, this memory should be available by now
        
        IntPtr strMem = IntPtr.Zero;
        
        fixed (char *p = str)
        {
            fixed (byte *addr = &memory[cursor])
            {
                int _len = Encoding.UTF8.GetBytes(p, str.Length + 1, addr, 4096 - cursor);
                strMem = (IntPtr)addr;
                cursor += _len;
            }
        }
        
        return strMem;
    }

    // copy pasted from SDL2#, but now it can be internal
    internal static unsafe string UTF8_ToManaged(IntPtr str, bool freePtr = false)
    {
        if (str == IntPtr.Zero)
        {
            return null;
        }

        byte *ptr = (byte *)str;
        while (*ptr != 0)
        {
            ptr++;
        }

        /* TODO: This #ifdef is only here because the equivalent
            * .NET 2.0 constructor appears to be less efficient?
            * Here's the pretty version, maybe steal this instead:
            *
        string result = new string(
            (sbyte*) str, // Also, why sbyte???
            0,
            (int) (ptr - (byte*) str),
            System.Text.Encoding.UTF8
        );
            * See the CoreCLR source for more info.
            * -flibit
            */
    #if NETSTANDARD2_0
        /* Modern C# lets you just send the byte*, nice! */
        string result = System.Text.Encoding.UTF8.GetString(
            (byte*) str,
            (int) (ptr - (byte*) str)
        );
    #else
        /* Old C# requires an extra memcpy, bleh! */
        int len = (int) (ptr - (byte*) str);
        if (len == 0)
        {
            return string.Empty;
        }
        char* chars = stackalloc char[len];
        int strLen = System.Text.Encoding.UTF8.GetChars((byte*) str, len, chars, len);
        string result = new string(chars, 0, strLen);
    #endif

        if (freePtr)
        {
            SDL_free(str);
        }

        return result;
    }

    [DllImport("SDL3.dll", CallingConvention = CallingConvention.Cdecl)]
    private static extern void SDL_free(IntPtr memblock);


    static StringPool()
    {
        // this should be good, considering all strings are short-lived
        memory = new byte[4096];
    }

    private static byte[] memory;
    private static int cursor = 0;
}

// String type used to pass C# strings to SDL functions that need them as input.
// Usage example:
// ```cs
// // no need to use the type explicitly, just pass a string and that's it
// var window = SDL3.SDL.SDL_CreateWindow("Hello World!", 640, 480, SDL3.SDL.SDL_WindowFlags.SDL_WINDOW_OPENGL);
// ```
public struct InString
{
    public static implicit operator InString(string str)
    {
        return new InString(StringPool.str(str));
    }

    public static InString Empty {
        get {
            return new InString(IntPtr.Zero);
        }
    }

    private InString(IntPtr ptr)
    {
        this.str = ptr;
    }
    
    private readonly IntPtr str;
}


// Wrapper for strings returned by SDL functions. Only used for strings that are not owned by the caller (ie. it does not free the pointer).
// WARNING: Do not use this for parameters that are passed to SDL functions, only for return values.
// WARNING: Do not use this type for strings that you should free, use `HeapString` instead.
// Usage example:
// ```cs
// // notice we use the built-in `string` type here and `.Str()` to convert the `String` to a `string`
// string str = SDL3.SDL_GetError().Str();
// Console.WriteLine(str);
// ```
[StructLayout(LayoutKind.Sequential)]
public struct String
{
    internal String(IntPtr str) { _str = str; }

    public string Str() { return StringPool.UTF8_ToManaged(_str); }

    private readonly IntPtr _str;
}

// Wrapper for strings returned by SDL functions. Only used for strings that are owned by the caller (ie. it frees the pointer).
// WARNING: Do not use this for parameters that are passed to SDL functions, only for return values.
// WARNING: Do not use this type directly, use the implicit conversion to `string` instead.
// WARNING: Do not use this type for strings owned by SDL, use `String` instead.
// WARNING: You can only call `.Str()` once as the internal string is freed, so make sure to store the result in a variable for reuse.
// Usage example:
// ```cs
// // notice we use the built-in `string` type here and `.Str()` to convert the `HeapString` to a `string`
// // no need to free the pointer, it's done automatically
// string str = SDL3.SDL_GetCameraDeviceName(<camera-id>).Str();
// Console.WriteLine(str);
// ```
[StructLayout(LayoutKind.Sequential)]
public struct HeapString
{
    internal HeapString(IntPtr str) { _str = str; }

    public string Str() { return StringPool.UTF8_ToManaged(_str, true); }

    private readonly IntPtr _str;
}