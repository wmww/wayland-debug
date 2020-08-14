#include <wayland-server.h>
#include <stdio.h>
#include <stdlib.h>

static struct wl_display* display;

const char* socket_name()
{
    return "wayland-debug-mock";
}

static void compositor_create_surface(struct wl_client* client, struct wl_resource* resource, uint32_t id)
{
    (void)client; (void)resource; (void)id;
    printf("fatal: wl_compositor.create_surface() not implemented");
    exit(1);
}

static void compositor_create_region(struct wl_client * client, struct wl_resource * resource, uint32_t id)
{
    (void)client; (void)resource; (void)id;
    printf("fatal: wl_compositor.create_region() not implemented");
    exit(1);
}

static const struct wl_compositor_interface compositor_interface = {
    .create_surface = compositor_create_surface,
    .create_region = compositor_create_region,
};

static void wl_compositor_bind(struct wl_client* client, void* data, uint32_t version, uint32_t id)
{
    (void)data;
    struct wl_resource* resource = wl_resource_create(client, &wl_compositor_interface, version, id);
    wl_resource_set_implementation(resource, &compositor_interface, NULL, NULL);
};

void mock_server_init()
{
    display = wl_display_create();
    wl_display_add_socket(display, socket_name());

    printf("Server created on display %s\n", socket_name());

    wl_global_create(display, &wl_compositor_interface, 4, NULL, wl_compositor_bind);
}

struct wl_display* mock_server_get_display()
{
    return display;
}

void mock_server_deinit()
{
    wl_display_destroy(display);
}
