# Wayland debug

A tool for debugging Wayland protocol messages. It can parse the output of a wayland app/compositor run with `WAYLAND_DEBUG=1`, or it can integrate directly with with GDB.

## Usage
```
main.py [-h] [--matcher-help] [-v] [-l LOAD] [-a] [-f MATCHER] [-b MATCHER] [-d]

optional arguments:
  -h, --help                    show this help message and exit
  --matcher-help                show how to write matchers used by filter and quit
  -v, --verbose                 verbose output, mostly used for debugging this program
  -l LOAD, --load LOAD          Load Wayland events from a file instead of stdin
  -a, --all                     show output that can't be parsed as Wayland events
  -f MATCHER, --filter MATCHER  only show these objects/messages (see --matcher-help for syntax)
  -b MATCHER, --break MATCHER   break on these objects/messages (see --matcher-help for syntax)
  -d, --gdb                     run inside gdb, all subsequent arguments are sent to gdb
```

## Matchers
Matchers are used through out the program to show and hide messages. A matcher consists of a comma seporated list of objects. An object is a type name, and/or an object ID (in which case a generation can also be specified). An @ goes inbetween the name and ID, and is optional if both are not specified. A * can be used as a wildcard in type names.

Examples of objects:

| Matcher | Description |
| --- | --- |
| wl_surface   | Matches any wl_surface |
| 5            | Matches the object with ID 5 |
| 4.12         | Matches the 12th object with ID 4 |
| wl_surface@6 | Matches the object with ID 7, which is asserted to be a wl_surface |
| xdg_*@3.2    | Matches the 2nd object with ID 3, which is some sort of XDG type |

Matchers can optionally be accompanied by a brace enclosed, comma seporated list of messages. Messages can have wildcards too. Messages before the object require the object to be on argument, and messages after require the message to be called on the object.

Examples of messages:

| Matcher | Description |
| --- | --- |
| wl_surface[commit]   | Matches commit messages on wl_surfaces |
| 6.2[motion,button]   | Matches motion or button messages on the 2nd object with ID 6 |
| [delete_id]*_surface | Matches delete_id messages on any sort of surface (this works even though the messages themselves are called on the wl_display) |

If the matcher list (or a message list) starts with '^', it matches everything but what's given.

## Examples

### Piping messages from stdin
This will only show pointer, surface commit and surface destroy messages
```
WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | ./main.py -af 'wl_pointer, wl_surface[commit, destroy]'
```

### Loading from a file
This will show everything but callbacks and frame messages. file.log was presumably written from the output of libwayland with `WAYLAND_DEBUG=1`.
```
./main.py -l dir/file.log -f '^ wl_callback, *[frame]'
```

### Use GDB
This will spin up an instance of GDB, and run the program inside it. It will show all messages, but break when an XDG thing is configured or when object ID 12 is used
```
./main.py -b 'xdg_*[configure], 12' --gdb program
```
