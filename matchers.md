# Matchers

Matchers are used throughout wayland-debug to filter messages and set breakpoints. Matchers can leave components of messages unspecified, and use wildcards.

| Matcher               | Description |
| ---                   | --- |
| `wl_surface`          | All events and requests on `wl_surface`s |
| `xdg_*`               | Messages on any XDG type (using a wildcard) |
| `5`                   | Messages on all objects with ID `5` |
| `4b`                  | Messages on object `4b` |
| `.commit`             | `commit` messages on any object |
| `wl_surface.commit`   | `commit` messages on `wl_surface`s |
| `B: .commit`          | `commit` messages on connection `B` (the 2nd connection) |
| `wl_pointer(pressed)` | Any Messages on `wl_pointer`s with `pressed` as an argument |
| `wl_pointer(buffer=)` | Messages with an argument named `buffer` |
| `.(null)`             | Messages that have an object argument that's null |

Objects are created by messages on other objects. When objects are destroyed the `wl_display` gets a `.delete_id` message with the object ID of the destroyed object. `object.new` and `object.destroyed` aren't real Wayland messages, but they allow you to match these two cases more easily.

| Matcher                   | Description |
| ---                       | --- |
| `.new`                    | Any object being created |
| `wl_surface.new`          | `wl_surface`s being created |
| `.destroyed`              | Any object being destroyed |
| `10.destroyed`            | Object with ID 10 being destroyed |

A matcher can be a comma-separated list of patterns, in which case a message that matches any of the cases will match. A list or pattern can be followed by `!` and one or more patterns, in which case any message that matches those is excluded. Argument lists behave a little differently, because all items in an argument list must match at least one argument.

| Matcher                           | Description |
| ---                               | --- |
| `wl_pointer, .commit`             | Matches any message on a `wl_surface`, and a `.commit` message on any type |
| `wl_pointer, wl_touch ! .motion ` | All `wl_pointer` and `wl_touch` messages except `.motion` |
| `xdg_* ! xdg_popup, .get_popup`   | Matches all messages on XDG types except those relating to popups |
| `(x=0, y=0)`                      | Matches only messages that have both an `x=0` argument and a `y=0` argument |

Components of a pattern can be surrounded by braces and use the `positive ! negative` syntax as described above.

| Matcher                           | Description |
| ---                               | --- |
| `55a.[motion, axis]`              | Matches `.motion` and `.axis` events on object `55a` |
| `[wl_pointer ! 55, 62].motion`    | Matches `.motion` events on `wl_pointer`s that do not have object ID `55` or `62` |
| `([x=0, y=0])`                    | Matches messages that have either an `x=0` or `y=0` argument |

The special matchers `*` and `!` match anything and nothing respectively.
