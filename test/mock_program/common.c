#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void sleep_for_ms(int ms)
{
    struct timespec sleep_time = {
        .tv_sec = 0,
        .tv_nsec = (long)ms * 1000000,
    };
    nanosleep(&sleep_time, NULL);
}

const char* get_display_name()
{
    const char* result = getenv("WAYLAND_DISPLAY");
    if (!result)
    {
        printf("Error: WAYLAND_DISPLAY not set\n");
        exit(1);
    }
    return result;
}
