#include <stdio.h>
#include <stdlib.h>
#include <wayland-server-core.h>
#include <wayland-client-core.h>

#include "mock_program.h"

static int client_event_callback(int fd, uint32_t mask, void* data)
{
    (void)fd; (void)mask; (void)data;
    wl_display_read_events(mock_client_get_display());

    while (wl_display_prepare_read(mock_client_get_display()) != 0)
    {
        wl_display_dispatch_pending(mock_client_get_display());
    }
    wl_display_flush(mock_client_get_display());

    return 0;
}

int main(int argc, const char** argv)
{
    (void)argc; (void)argv;

    mock_server_init();
    mock_client_init();

    wl_event_loop_add_fd(
        wl_display_get_event_loop(mock_server_get_display()),
        wl_display_get_fd(mock_client_get_display()),
        WL_EVENT_READABLE,
        client_event_callback, NULL);

    while (wl_display_prepare_read(mock_client_get_display()) != 0)
    {
        wl_display_dispatch_pending(mock_client_get_display());
    }
    wl_display_flush(mock_client_get_display());

    wl_display_run(mock_server_get_display());

    mock_client_deinit();
    mock_server_deinit();
}

void mock_program_terminate()
{
    wl_display_terminate(mock_server_get_display());
}
