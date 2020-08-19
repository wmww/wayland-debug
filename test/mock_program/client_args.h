#ifndef CLIENT_ARGS_H
#define CLIENT_ARGS_H

// To add a mode, you also need to add it to client_args.c
enum Mode
{
    MODE_INVALID = 0,
    MODE_SIMPLE_CLIENT,
    MODE_POINTER_MOVE,
};

extern enum Mode mode;

void parse_args(int argc, const char** argv);

#endif // CLIENT_ARGS_H
