#include <wayland-client.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

#include "mock_program.h"

static struct wl_display* display;
static struct wl_registry* registry;
static struct wl_compositor* compositor;

static void registry_global(
    void* data,
    struct wl_registry* registry,
    uint32_t id,
    const char* name,
    uint32_t version)
{
    (void)data;
    if (strcmp(wl_compositor_interface.name, name) == 0)
    {
        compositor = wl_registry_bind(registry, id, &wl_compositor_interface, version);
        mock_program_terminate();
    }
}

static void registry_global_remove(void* data, struct wl_registry* registry, uint32_t id)
{
    (void)data; (void)registry;
    printf("fatal: registry.global_remove() not implemented (id: %d)", id);
    exit(1);
}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_global_remove,
};

void mock_client_init()
{
    for (int i = 0; i < 100; i++)
    {
        display = wl_display_connect(socket_name());
        if (display)
        {
            break;
        }

        static const struct timespec sleep_time = {
            .tv_sec = 0,
            .tv_nsec = 50000000,
        };
        nanosleep(&sleep_time, NULL);
    };

    if (!display)
    {
        printf("mock_client_init(): can't connect to host Wayland display %s\n", socket_name());
        exit(1);
    }

    registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
}

struct wl_display* mock_client_get_display()
{
    return display;
}

void mock_client_deinit()
{
    wl_display_disconnect(display);
}
