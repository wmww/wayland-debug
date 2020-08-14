#include <stdio.h>
#include <stdlib.h>
#include <wayland-server-core.h>

#include "mock_program.h"

static int client_event_callback(int fd, uint32_t mask, void* data)
{
    (void)fd; (void)mask; (void)data;
    mock_client_dispatch();
    return 0;
}

int main(int argc, const char** argv)
{
    (void)argc; (void)argv;

    mock_server_init();
    mock_client_init();

    wl_event_loop_add_fd(
        mock_server_get_event_loop(),
        mock_client_get_display_fd(), WL_EVENT_READABLE,
        client_event_callback, NULL);

    mock_client_dispatch();
    mock_server_run();

    mock_client_deinit();
    mock_server_deinit();
}
