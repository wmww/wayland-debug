To run wayland-debug in GDB mode, you need a debug build of libwayland. wayland-debug needs libwayland debug symbols, and compiler optimizations on libwayland are known to break wayland-debug (so installing debug symbols for the normal libwayland is no longer sufficient).

The `wayland-debug` snap bundles a debug build of libwayland and uses it automatically. In most cases, this should work out of the box. However, dynamically linking programs to shared libraries from snaps is quite fragile and may break in some cases, especially on systems with a libc older than Ubuntu 20.04's (the snap's base). If you run into trouble, or if you're not using the snap at all, you'll need to build libwayland from source. This is generally not difficult.

To make the process even easier, we provide `resources/get-libwayland.sh`. It clones libwayland into `resources` and builds it. You will need to install whatever build dependencies are required on your system. `wayland-debug` will automatically look for libwayland at the location where it's built.

To use a libwayland built at an arbitrary location, specify it with the `--libwayland` flag. __NOTE: this flag must come before `-g`/`--gdb`__. The value should be the directory where `libwayland-client.so` and `libwayland-server.so` are located. For example:
```
$ wayland-debug --libwayland ~/code/wayland/build/src/ -g weston-terminal
```
