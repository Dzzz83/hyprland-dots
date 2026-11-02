# Random login-screen wallpaper

Configured on 2026-10-31 for Plasma Login Manager 6.8.2.

The login screen uses KDE's installed `org.kde.slideshow` plugin in random
order (`SlideshowMode=0`) with automatic changes disabled (`SlideInterval=0`).
It selects one image when the wallpaper process starts and keeps that image
while the login screen remains open. Random choices can occasionally repeat.

The 13 PNG wallpapers were copied from
`$HOME/Desktop/Wallpapers` to
`/usr/local/share/wallpapers/plasma-login`. This system location is readable
before a user logs in. The copies are a snapshot; new desktop wallpapers
are included after running the installer again:

```sh
sudo bash '$HOME/Documents/ChatGPT/Hyperland + CachyOS/login-wallpaper/install.sh'
```

Settings are in `/etc/plasmalogin.conf`. The previous image configuration is
retained there, and the original full file was backed up to
`/etc/plasmalogin.conf.backup-20261031-143653-random-wallpaper`.

To restore the original settings:

```sh
sudo cp -a /etc/plasmalogin.conf.backup-20261031-143653-random-wallpaper /etc/plasmalogin.conf
```

No display-manager restart or logout was performed during installation.
The real login screen still needs to be checked after logout. Checks passed
for installer Bash syntax, all 13 copied image hashes, image and directory
read permissions, and two offscreen plugin startups selecting different
images with no subsequent change during the two-second checks.

Implementation references: [Plasma Login configuration](https://github.com/KDE/plasma-login-manager/blob/master/README.md#configuration)
and [KDE image backend](https://github.com/KDE/plasma-workspace/blob/master/wallpapers/image/plugin/imagebackend.cpp).
