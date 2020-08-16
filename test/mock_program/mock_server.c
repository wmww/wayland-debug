#include <wayland-server.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "mock_program.h"

static struct wl_display* display;

static const double test_fixed_sequence[] = {0.0, 1.0, 0.5, -1.0, 280.0, -12.5, 16.3, 425.87, -100000.0, 0.001};

#define FATAL_NOT_IMPL printf("fatal: %s() not implemented", __func__); exit(1)

static void client_disconnect(struct wl_listener *listener, void *data)
{
    mock_program_terminate();
}

static struct wl_listener client_disconnect_listener = {
    .notify = client_disconnect,
};

static void client_connect(struct wl_listener *listener, void *data)
{
    struct wl_client* client = (struct wl_client*)data;
    wl_client_add_destroy_listener(client, &client_disconnect_listener);
}

static struct wl_listener client_connect_listener = {
    .notify = client_connect,
};

static void compositor_create_surface(struct wl_client* client, struct wl_resource* resource, uint32_t id)
{
    FATAL_NOT_IMPL;
}

static void compositor_create_region(struct wl_client * client, struct wl_resource * resource, uint32_t id)
{
    FATAL_NOT_IMPL;
}

static const struct wl_compositor_interface compositor_interface = {
    .create_surface = compositor_create_surface,
    .create_region = compositor_create_region,
};

static void compositor_bind(struct wl_client* client, void* data, uint32_t version, uint32_t id)
{
    struct wl_resource* resource = wl_resource_create(client, &wl_compositor_interface, version, id);
    wl_resource_set_implementation(resource, &compositor_interface, NULL, NULL);
};

void seat_get_pointer(struct wl_client *client, struct wl_resource *resource, uint32_t id)
{
    struct wl_resource* pointer = wl_resource_create(
        client,
        &wl_pointer_interface,
        wl_resource_get_version(resource),
        id);
    for (unsigned long i = 0; i < sizeof(test_fixed_sequence) / sizeof(test_fixed_sequence[0]); i++)
    {
        wl_pointer_send_motion(pointer, 0, 0.0, wl_fixed_from_double(test_fixed_sequence[i]));
    }
}

void seat_get_keyboard(struct wl_client *client, struct wl_resource *resource, uint32_t id)
{
    FATAL_NOT_IMPL;
}

void seat_get_touch(struct wl_client *client, struct wl_resource *resource, uint32_t id)
{
    FATAL_NOT_IMPL;
}

void seat_release(struct wl_client *client, struct wl_resource *resource)
{
    FATAL_NOT_IMPL;
}

static const struct wl_seat_interface seat_interface = {
    .get_pointer = seat_get_pointer,
    .get_keyboard = seat_get_keyboard,
    .get_touch = seat_get_touch,
    .release = seat_release,
};

static void seat_bind(struct wl_client* client, void* data, uint32_t version, uint32_t id)
{
    struct wl_resource* resource = wl_resource_create(client, &wl_seat_interface, version, id);
    wl_resource_set_implementation(resource, &seat_interface, NULL, NULL);
};

void mock_server_init()
{
    display = wl_display_create();
    if (wl_display_add_socket(display, socket_name()) != 0)
    {
        printf("Server failed to connect to Wayland display %s\n", socket_name());
        exit(1);
    }

    wl_display_add_client_created_listener(display, &client_connect_listener);

    wl_global_create(display, &wl_compositor_interface, 4, NULL, compositor_bind);
    printf("Created compositor\n");
    wl_global_create(display, &wl_seat_interface, 7, NULL, seat_bind);
    printf("Created seat\n");
}

struct wl_display* mock_server_get_display()
{
    return display;
}

void mock_server_deinit()
{
    wl_display_destroy(display);
}
