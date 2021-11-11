// This is an implementation of a Wayland compositor for testing
// It does not show anything on the screen, and it is not conforment
// The only client it's supposed to work with is the one in mock_client.c

#include <wayland-server.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "common.h"

static struct wl_display* display = NULL;
static struct wl_resource* compositor = NULL;
static struct wl_resource* seat = NULL;
static struct wl_resource* data_device_manager = NULL;
static struct wl_resource* output = NULL;
static struct wl_resource* surface = NULL;

static const double test_fixed_sequence[] = {0.0, 1.0, 0.5, -1.0, 280.0, -12.5, 16.3, 425.87, -100000.0, 0.001};

#define FATAL_NOT_IMPL printf("fatal: %s() not implemented", __func__); exit(1)

static void client_disconnect(struct wl_listener *listener, void *data)
{
    wl_display_terminate(display);
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

static int surface_dispatcher(const void* data, void* resource, uint32_t opcode, const struct wl_message* message, union wl_argument* args)
{
    return 0;
}

static void compositor_create_surface(struct wl_client* client, struct wl_resource* resource, uint32_t id)
{
    if (!output)
    {
        printf("Client should not have created surface without binding to output");
        exit(1);
    }
    surface = wl_resource_create(
        client,
        &wl_surface_interface,
        wl_resource_get_version(resource),
        id);
    wl_resource_set_dispatcher(surface, surface_dispatcher, NULL, NULL, NULL);
    wl_surface_send_enter(surface, output);
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
    compositor = wl_resource_create(client, &wl_compositor_interface, version, id);
    wl_resource_set_implementation(compositor, &compositor_interface, NULL, NULL);
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
    struct wl_resource* keyboard = wl_resource_create(
        client,
        &wl_keyboard_interface,
        wl_resource_get_version(resource),
        id);
    if (surface)
    {
        struct wl_array keys;
        wl_array_init(&keys);
        uint32_t* data = wl_array_add(&keys, 2 * sizeof(uint32_t));
        data[0] = 69;
        data[1] = 420;
        wl_keyboard_send_enter(keyboard, wl_display_next_serial(display), surface, &keys);
        wl_array_release(&keys);

    }
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
    seat = wl_resource_create(client, &wl_seat_interface, version, id);
    wl_resource_set_implementation(seat, &seat_interface, NULL, NULL);
    wl_seat_send_capabilities(seat, WL_SEAT_CAPABILITY_POINTER | WL_SEAT_CAPABILITY_KEYBOARD);
};

void data_device_manager_create_data_source(struct wl_client *client, struct wl_resource *resource, uint32_t id)
{
    FATAL_NOT_IMPL;
}

void data_device_manager_get_data_device(
    struct wl_client *client,
    struct wl_resource *resource,
    uint32_t id,
    struct wl_resource *seat)
{
    struct wl_resource* data_device = wl_resource_create(
        client,
        &wl_data_device_interface,
        wl_resource_get_version(resource),
        id);
    struct wl_resource* data_offer = wl_resource_create(
        client,
        &wl_data_offer_interface,
        wl_resource_get_version(resource),
        0);
    wl_data_device_send_data_offer(data_device, data_offer);
    wl_data_offer_send_offer(data_offer, "mock-meme-type");
}

static const struct wl_data_device_manager_interface data_device_manager_interface = {
    .create_data_source = data_device_manager_create_data_source,
    .get_data_device = data_device_manager_get_data_device,
};

static void data_device_manager_bind(struct wl_client* client, void* data, uint32_t version, uint32_t id)
{
    data_device_manager = wl_resource_create(client, &wl_data_device_manager_interface, version, id);
    wl_resource_set_implementation(data_device_manager, &data_device_manager_interface, NULL, NULL);
};

static void output_bind(struct wl_client* client, void* data, uint32_t version, uint32_t id)
{
    output = wl_resource_create(client, &wl_output_interface, version, id);
};

int main(int argc, const char** argv)
{
    display = wl_display_create();
    if (wl_display_add_socket(display, get_display_name()) != 0)
    {
        printf("Server failed to connect to Wayland display %s\n", get_display_name());
        exit(1);
    }

    wl_display_add_client_created_listener(display, &client_connect_listener);

    wl_global_create(display, &wl_compositor_interface, 4, NULL, compositor_bind);
    wl_global_create(display, &wl_seat_interface, 6, NULL, seat_bind);
    wl_global_create(display, &wl_data_device_manager_interface, 2, NULL, data_device_manager_bind);
    wl_global_create(display, &wl_output_interface, 1, NULL, output_bind);

    wl_display_run(display);

    wl_display_destroy(display);

    return 0;
}
