#include <wayland-client.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "client_args.h"
#include "common.h"

static struct wl_display* display;
static struct wl_registry* registry;
static struct wl_compositor* compositor;
static struct wl_output* output;
static struct wl_surface* surface;
static struct wl_seat* seat;
static struct wl_pointer* pointer;
static struct wl_data_device_manager* data_device_manager;
static struct wl_data_device* data_device;

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

void data_offer_offer(void *data, struct wl_data_offer *wl_data_offer, const char *mime_type) {}
void data_offer_source_actions(void *data, struct wl_data_offer *wl_data_offer, uint32_t source_actions) {}
void data_offer_action(void *data, struct wl_data_offer *wl_data_offer, uint32_t dnd_action) {}

static const struct wl_data_offer_listener data_offer_listener = {
    .offer = data_offer_offer,
    .source_actions = data_offer_source_actions,
    .action = data_offer_action,
};

void data_device_data_offer(void *data, struct wl_data_device *wl_data_device, struct wl_data_offer *id)
{
    wl_data_offer_add_listener(id, &data_offer_listener, NULL);
}

void data_device_enter(void *data, struct wl_data_device *wl_data_device, uint32_t serial, struct wl_surface *surface, wl_fixed_t x, wl_fixed_t y, struct wl_data_offer *id) {}
void data_device_leave(void *data, struct wl_data_device *wl_data_device) {}
void data_device_motion(void *data, struct wl_data_device *wl_data_device, uint32_t time, wl_fixed_t x, wl_fixed_t y) {}
void data_device_drop(void *data, struct wl_data_device *wl_data_device) {}
void data_device_selection(void *data, struct wl_data_device *wl_data_device, struct wl_data_offer *id) {}

static const struct wl_data_device_listener data_device_listener = {
    .data_offer = data_device_data_offer,
    .enter = data_device_enter,
    .leave = data_device_leave,
    .motion = data_device_motion,
    .drop = data_device_drop,
    .selection = data_device_selection,
};

static int surface_dispatcher(const void* data, void* resource, uint32_t opcode, const struct wl_message* message, union wl_argument* args)
{
    return 0;
}

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
    if (strcmp(wl_output_interface.name, name) == 0)
    {
        output = wl_registry_bind(registry, id, &wl_output_interface, version);
    }
    else if (strcmp(wl_seat_interface.name, name) == 0)
    {
        seat = wl_registry_bind(registry, id, &wl_seat_interface, version);
        if (mode == MODE_POINTER_MOVE)
        {
            pointer = wl_seat_get_pointer(seat);
            wl_pointer_add_listener(pointer, &pointer_listener, NULL);
            wl_display_roundtrip(display);
        }
    }
    else if (strcmp(wl_data_device_manager_interface.name, name) == 0)
    {
        data_device_manager = wl_registry_bind(registry, id, &wl_data_device_manager_interface, version);
    }

    if (mode == MODE_SERVER_CREATED_OBJ && data_device_manager && seat && !data_device)
    {
        data_device = wl_data_device_manager_get_data_device(data_device_manager, seat);
        wl_data_device_add_listener(data_device, &data_device_listener, NULL);
        wl_display_roundtrip(display);
    }

    if (mode == MODE_DISPATCHER && compositor && output && !surface)
    {
        surface = wl_compositor_create_surface(compositor);
        wl_proxy_add_dispatcher((struct wl_proxy*)surface, surface_dispatcher, NULL, NULL);
        wl_surface_attach(surface, NULL, 0, 0);
        wl_display_roundtrip(display);
    }
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

int main(int argc, const char** argv)
{
    parse_args(argc, argv);

    // Wait 5 seconds for server to appear
    const int wait_time_ms = 5000;
    const int check_interval_ms = 50;
    // We don't account for time not spent sleeping but who cares
    for (int t = 0; t < wait_time_ms; t += check_interval_ms)
    {
        if ((display = wl_display_connect(get_display_name())))
        {
            break;
        }

        sleep_for_ms(check_interval_ms);
    };

    if (!display)
    {
        printf("mock_client_init(): can't connect to host Wayland display %s\n", get_display_name());
        exit(1);
    }

    registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);

    wl_display_disconnect(display);
}
