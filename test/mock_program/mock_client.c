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
static struct wl_seat* seat;
static struct wl_pointer* pointer;

#define FATAL_NOT_IMPL printf("fatal: %s() not implemented", __func__); exit(1)

void pointer_enter(void *data, struct wl_pointer *wl_pointer, uint32_t serial, struct wl_surface *surface, wl_fixed_t surface_x, wl_fixed_t surface_y) {}
void pointer_leave(void *data, struct wl_pointer *wl_pointer, uint32_t serial, struct wl_surface *surface) {}
void pointer_motion(void *data, struct wl_pointer *wl_pointer, uint32_t time, wl_fixed_t surface_x, wl_fixed_t surface_y) {}
void pointer_button(void *data, struct wl_pointer *wl_pointer, uint32_t serial, uint32_t time, uint32_t button, uint32_t state) {}
void pointer_axis(void *data, struct wl_pointer *wl_pointer, uint32_t time, uint32_t axis, wl_fixed_t value) {}
void pointer_frame(void *data, struct wl_pointer *wl_pointer) {}
void pointer_axis_source(void *data, struct wl_pointer *wl_pointer, uint32_t axis_source) {}
void pointer_axis_stop(void *data, struct wl_pointer *wl_pointer, uint32_t time, uint32_t axis) {}
void pointer_axis_discrete(void *data, struct wl_pointer *wl_pointer, uint32_t axis, int32_t discrete) {}

static const struct wl_pointer_listener pointer_listener = {
    .enter = pointer_enter,
    .leave = pointer_leave,
    .motion = pointer_motion,
    .button = pointer_button,
    .axis = pointer_axis,
    .frame = pointer_frame,
    .axis_source = pointer_axis_source,
    .axis_stop = pointer_axis_stop,
    .axis_discrete = pointer_axis_discrete,
};

static void registry_global(
    void* data,
    struct wl_registry* registry,
    uint32_t id,
    const char* name,
    uint32_t version)
{
    if (strcmp(wl_compositor_interface.name, name) == 0)
    {
        compositor = wl_registry_bind(registry, id, &wl_compositor_interface, version);
    }
    else if (strcmp(wl_seat_interface.name, name) == 0)
    {
        seat = wl_registry_bind(registry, id, &wl_seat_interface, version);
        if (mode == MODE_POINTER_MOVE)
        {
            pointer = wl_seat_get_pointer(seat);
            wl_pointer_add_listener(pointer, &pointer_listener, NULL);
            wl_display_roundtrip(display);
            mock_program_terminate();
        }
    }

    if (mode != MODE_CLIENT_AND_SERVER)
    {
        wl_display_roundtrip(display); // Causes problems when the server is running on the same event loop
    }
    mock_program_terminate();
}

static void registry_global_remove(void* data, struct wl_registry* registry, uint32_t id)
{
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

void mock_client_main()
{
    mock_program_terminate();
}

struct wl_display* mock_client_get_display()
{
    return display;
}

void mock_client_deinit()
{
    wl_display_disconnect(display);
}
