#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "client_args.h"

enum Mode mode = MODE_INVALID;

struct {
    enum Mode mode;
    const char* arg;
} mode_args[] = {
    {
        .mode = MODE_SIMPLE_CLIENT,
        .arg = "simple-client",
    },
    {
        .mode = MODE_POINTER_MOVE,
        .arg = "pointer-move",
    },
    {
        .mode = MODE_DISPATCHER,
        .arg = "dispatcher",
    },
    {
        .mode = MODE_SERVER_CREATED_OBJ,
        .arg = "server-created-obj",
    },
    {
        .mode = MODE_KEYBOARD_ENTER,
        .arg = "keyboard-enter",
    },
};

void parse_args(int argc, const char** argv)
{
    if (argc < 2)
    {
        printf("No mode given\n");
    }
    else if (argc > 2)
    {
        printf("Too many arguments\n");
    }
    else if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)
    {
        // Mode is not set so help will be shown without additional error message
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
        }
    }

    if (mode == MODE_INVALID)
    {
        printf("Valid modes:\n");
        for (unsigned long i = 0; i < sizeof(mode_args) / sizeof(mode_args[0]); i++)
        {
            printf("  %s\n", mode_args[i].arg);
        }
        exit(1);
    }
}
