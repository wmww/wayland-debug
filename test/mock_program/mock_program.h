#ifndef MOCK_PROGRAM_H
#define MOCK_PROGRAM_H

const char* socket_name();
void mock_server_init();
struct wl_event_loop* mock_server_get_event_loop();
void mock_server_run();
void mock_server_deinit();

void mock_client_init();
int mock_client_get_display_fd();
void mock_client_dispatch();
void mock_client_deinit();

#endif // MOCK_PROGRAM_H
