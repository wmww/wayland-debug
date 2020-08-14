#ifndef MOCK_PROGRAM_H
#define MOCK_PROGRAM_H

const char* socket_name();
void mock_server_init();
struct wl_display* mock_server_get_display();
void mock_server_deinit();

void mock_client_init();
struct wl_display* mock_client_get_display();
void mock_client_deinit();

#endif // MOCK_PROGRAM_H
