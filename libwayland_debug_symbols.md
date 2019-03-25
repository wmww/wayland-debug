To run wayland-debug in GDB mode, you need libwayland debug symbols installed. Debug symbols allow GDB to understand a program or library, which is needed for wayland-debug to be able to pull out the data it needs. If you don't already know that you have them, you probaly don't, but you'll know for sure if you get an error about it when you start up wayland-debug in GDB mode.

How to get them depends on your distro

### Ubuntu
On Ubuntu, see [this wiki page](https://wiki.ubuntu.com/Debug%20Symbol%20Packages), then install with
```
sudo apt install libwayland-server0-dbgsym libwayland-client0-dbgsym
```

### Arch
The best way I know is to [turn makepkg debug symbol stripping off](https://wiki.archlinux.org/index.php/Debug_-_Getting_Traces#Compilation_settings), then install `wayland-git` from the AUR
```
yay -S wayland-git
```

### Other
Feel free to extend this page if you get them installed on another distro
