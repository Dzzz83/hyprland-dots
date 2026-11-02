#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
    printf '%s\n' 'Run this installer with administrator privileges.' >&2
    exit 1
fi

wallpaper_source=$HOME/Desktop/Wallpapers
wallpaper_destination=/usr/local/share/wallpapers/plasma-login
login_config=/etc/plasmalogin.conf

shopt -s nullglob
wallpapers=("$wallpaper_source"/*.png)
if (( ${#wallpapers[@]} == 0 )); then
    printf '%s\n' 'No PNG wallpapers found; login settings were not changed.' >&2
    exit 1
fi

backup_path="${login_config}.backup-$(date +%Y%m%d-%H%M%S)-random-wallpaper"
cp -a -- "$login_config" "$backup_path"
install -d -m 755 -o root -g root "$wallpaper_destination"
install -m 644 -o root -g root -- "${wallpapers[@]}" "$wallpaper_destination/"

# A random slideshow with no timer picks once when the login screen starts.
kwriteconfig6 --file "$login_config" --group Greeter --key WallpaperPluginId org.kde.slideshow
kwriteconfig6 --file "$login_config" --group Greeter --group Wallpaper --group org.kde.slideshow --group General --key SlidePaths "$wallpaper_destination"
kwriteconfig6 --file "$login_config" --group Greeter --group Wallpaper --group org.kde.slideshow --group General --key SlideInterval 0
kwriteconfig6 --file "$login_config" --group Greeter --group Wallpaper --group org.kde.slideshow --group General --key SlideshowMode 0
kwriteconfig6 --file "$login_config" --group Greeter --group Wallpaper --group org.kde.slideshow --group General --key Blur true
kwriteconfig6 --file "$login_config" --group Greeter --group Wallpaper --group org.kde.slideshow --group General --key FillMode 0

runuser -u plasmalogin -- test -r "$wallpaper_destination/${wallpapers[0]##*/}"
printf 'Installed %s login wallpapers. Previous configuration: %s\n' "${#wallpapers[@]}" "$backup_path"
printf '%s\n' 'The next login screen will use the new settings; the current session was not restarted.'
