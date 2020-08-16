#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <poll.h>
#include <wayland-server-core.h>
#include <wayland-client-core.h>

#include "mock_program.h"

enum Mode mode = MODE_INVALID;
static int terminate_requested = 0; // Only used in client-only modes

struct {
    enum Mode mode;
    const char* arg;
} mode_args[] = {
    {
        .mode = MODE_SERVER,
        .arg = "server",
    },
    {
        .mode = MODE_CLIENT_AND_SERVER,
        .arg = "client-and-server",
    },
    {
        .mode = MODE_SIMPLE_CLIENT,
        .arg = "simple-client",
    },
};

static void client_prepare_read()
{
    while (wl_display_prepare_read(mock_client_get_display()) != 0)
    {
        wl_display_dispatch_pending(mock_client_get_display());
    }
    wl_display_flush(mock_client_get_display());
}

static int client_event_callback(int fd, uint32_t mask, void* data)
{
    (void)fd; (void)mask; (void)data;
    wl_display_read_events(mock_client_get_display());
    client_prepare_read();
    return 0;
}

void client_only_main()
{
    mock_client_init();

    client_prepare_read();
    while (!terminate_requested)
    {
        struct pollfd fds = {
            .fd = wl_display_get_fd(mock_client_get_display()),
            .events = POLLIN,
            .revents = 0,
        };
        poll(&fds, 1, -1);
        client_event_callback(0, 0, NULL);
    }

    mock_client_deinit();
}

void server_only_main()
{
    mock_server_init();
    wl_display_run(mock_server_get_display());
    mock_server_deinit();
}

void client_and_server_main()
{
    mock_server_init();
    mock_client_init();

    wl_event_loop_add_fd(
        wl_display_get_event_loop(mock_server_get_display()),
        wl_display_get_fd(mock_client_get_display()),
        WL_EVENT_READABLE,
        client_event_callback, NULL);

    client_prepare_read();
    wl_display_run(mock_server_get_display());

    mock_client_deinit();
    mock_server_deinit();
}

int main(int argc, const char** argv)
{
    int show_help = 0;

    if (argc < 2)
    {
        printf("No mode given\n");
        show_help = 1;
    }
    else if (argc > 2)
    {
        printf("Too many arguments\n");
        show_help = 1;
    }
    else if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)
    {
        show_help = 1;
    }
    else
    {
        for (unsigned long i = 0; i < sizeof(mode_args) / sizeof(mode_args[0]); i++)
        {
            if (strcmp(argv[1], mode_args[i].arg) == 0)
            {
                mode = mode_args[i].mode;
                break;
            }
        }

        if (mode == MODE_INVALID)
        {
            printf("%s is not a valid mode\n", argv[1]);
            show_help = 1;
        }
    }

    if (show_help)
    {
        printf("Valid modes:\n");
        for (unsigned long i = 0; i < sizeof(mode_args) / sizeof(mode_args[0]); i++)
        {
            printf("  %s\n", mode_args[i].arg);
        }
        exit(1);
    }

    switch (mode)
    {
    case MODE_SERVER:
        server_only_main();
        break;

    case MODE_CLIENT_AND_SERVER:
        client_and_server_main();
        break;

    default:
        client_only_main();
    }
}

void mock_program_terminate()
{
    switch (mode)
    {
    case MODE_SERVER:
    case MODE_CLIENT_AND_SERVER:
        wl_display_terminate(mock_server_get_display());
        break;

    default:
        terminate_requested = 1;
    }
}
