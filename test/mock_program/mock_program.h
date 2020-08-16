#ifndef MOCK_PROGRAM_H
#define MOCK_PROGRAM_H

enum Mode
{
    MODE_INVALID = 0,
    MODE_SERVER,
    MODE_CLIENT_AND_SERVER,
    MODE_SIMPLE_CLIENT,
    MODE_POINTER_MOVE,
};

extern enum Mode mode;

const char* socket_name();
void mock_server_init();
struct wl_display* mock_server_get_display();
void mock_server_deinit();

void mock_client_init();
struct wl_display* mock_client_get_display();
void mock_client_deinit();

void mock_program_terminate();

#endif // MOCK_PROGRAM_H
