using System;
using System.Runtime;
using System.Runtime.InteropServices;

namespace SDL3
{
    public static class Runtime
    {
        private const string lib = "SDL3.lib";

        public enum SDL_bool : int
        {
            SDL_FALSE = 0,
            SDL_TRUE = 1,
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SDL_Time
        {
            public static implicit operator long(SDL_Time value) { return value._value; }

            private readonly long _value;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SDL_FunctionPointer
        {
            public static implicit operator bool(SDL_FunctionPointer value) { return value._value != IntPtr.Zero; }

            private readonly IntPtr _value;
        }

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_malloc(IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_calloc(IntPtr nmemb, IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern IntPtr SDL_realloc(IntPtr memblock, IntPtr size);

        [DllImport(lib, CallingConvention = CallingConvention.Cdecl)]
        internal static extern void SDL_free(IntPtr memblock);
    }
}