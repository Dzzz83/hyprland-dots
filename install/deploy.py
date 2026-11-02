#!/usr/bin/env python3
"""Back up existing desktop files and install links to this checkout."""
import argparse
import configparser
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('generic', 'lenovo'), default='generic')
    parser.add_argument('--backlight', help='Name under /sys/class/backlight; detected otherwise')
    parser.add_argument('--shell', action='store_true', help='Also install Fish and prompt configuration')
    parser.add_argument('--input', action='store_true', help='Also install Fcitx5 configuration')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-thunar', action='store_true', help='Skip live xfconf import (for offline staging)')
    args = parser.parse_args()
    home = Path.home()
    config = home / '.config'
    state = home / '.local/state/hypr-dots-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    runtime = REPO / 'build/runtime'
    backlights = sorted(Path('/sys/class/backlight').glob('*'))
    backlight = args.backlight or (backlights[0].name if backlights else '')
    if args.backlight and not (Path('/sys/class/backlight') / args.backlight).exists():
        parser.error('The selected backlight device does not exist')

    def backup(path):
        if not path.exists() and not path.is_symlink():
            return
        target = state / path.relative_to(home)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), target)

    def link(source, target):
        source, target = Path(source), Path(target)
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        if target == source:
            return
        print(f'LINK {target} -> {source}')
        if not args.dry_run:
            backup(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source, target_is_directory=source.is_dir())

    def write_setting_file(path, contents):
        if path.exists() and path.read_text() == contents:
            return
        print(f'UPDATE {path}')
        if not args.dry_run:
            backup(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)

    def merge_ini(path, settings):
        # Keep unrelated associations/preferences and preserve case-sensitive keys.
        document = configparser.ConfigParser(interpolation=None, delimiters=('=',))
        document.optionxform = str
        if path.exists():
            document.read(path)
        for section, values in settings.items():
            if not document.has_section(section):
                document.add_section(section)
            document[section].update(values)
        output = io.StringIO()
        document.write(output, space_around_delimiters=False)
        write_setting_file(path, output.getvalue())

    if not args.dry_run:
        runtime.mkdir(parents=True, exist_ok=True)
        machine = {'profile': args.profile, 'dashboard': args.profile == 'lenovo',
                   'primary_monitor': 'eDP-1' if args.profile == 'lenovo' else None}
        fields = [f'profile = {json.dumps(machine["profile"])}',
                  f'dashboard = {str(machine["dashboard"]).lower()}']
        if machine['primary_monitor']:
            fields.append(f'primary_monitor = {json.dumps(machine["primary_monitor"])}')
        (REPO / 'config/local.lua').write_text('return { ' + ', '.join(fields) + ' }\n')
        swaync = json.loads((REPO / 'swaync/config.json.in').read_text().replace('@BACKLIGHT@', backlight))
        if not backlight:
            # A desktop without a backlight must not display a nonfunctional slider.
            swaync['widgets'] = [name for name in swaync.get('widgets', []) if name != 'backlight']
            swaync.get('widget-config', {}).pop('backlight', None)
        (runtime / 'swaync-config.json').write_text(json.dumps(swaync, indent=4) + '\n')
        bookmarks = (REPO / 'gtk-3.0/bookmarks.template').read_text().replace('@HOME@', str(home))
        (runtime / 'gtk-bookmarks').write_text(bookmarks)
        for target, relative in [(REPO / 'swaync/config.json', '../build/runtime/swaync-config.json'),
                                 (REPO / 'gtk-3.0/bookmarks', '../build/runtime/gtk-bookmarks')]:
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                raise RuntimeError(f'Refusing to replace unexpected repository file: {target}')
            target.symlink_to(relative)

    link(REPO, config / 'hypr')
    components = ['waybar', 'rofi', 'swaync', 'wlogout', 'cava', 'ghostty', 'colors',
                  'gtk-3.0', 'gtk-4.0', 'Thunar', 'fontconfig', 'wifi-manager']
    if args.shell:
        components += ['ohmyposh']
    if args.input:
        components += ['fcitx5']
    for name in components:
        link(REPO / name, config / name)
    if args.shell:
        # Keep secrets and universal/runtime variables in the original Fish directory.
        for name in ('config.fish', 'fish_plugins', 'functions', 'conf.d', 'completions'):
            link(REPO / 'fish' / name, config / 'fish' / name)
    for category in ('icons', 'themes'):
        for source in sorted((REPO / 'assets' / category).iterdir()):
            link(source, home / '.local/share' / category / source.name)
    for name in ('wifi-manager', 'audio-panel'):
        binary = REPO / 'build/cargo/release' / name
        if binary.exists():
            link(binary, home / '.local/bin' / name)
    if (REPO / 'pavucontrol.ini').exists():
        link(REPO / 'pavucontrol.ini', config / 'pavucontrol.ini')
    link(REPO / 'scripts/screen-record', home / '.local/bin/screen-record')
    link(REPO / 'assets/wallpapers', home / 'Desktop/Wallpapers')
    link(REPO / 'assets/icons/default', home / '.icons/default')
    link(REPO / 'desktop/org.freedesktop.FileManager1.service',
         home / '.local/share/dbus-1/services/org.freedesktop.FileManager1.service')
    merge_ini(config / 'mimeapps.list', {'Default Applications': {
        'inode/directory': 'thunar.desktop;',
        'application/x-directory': 'thunar.desktop;',
    }})
    merge_ini(config / 'kcminputrc', {'Mouse': {
        'cursorTheme': 'breeze_cursors', 'cursorSize': '24',
    }})
    # Update an existing Xsettings daemon config without changing its other settings.
    xsettings = config / 'xsettingsd/xsettingsd.conf'
    if xsettings.exists():
        contents = xsettings.read_text()
        for key, value in [('Gtk/CursorThemeName', '"breeze_cursors"'),
                           ('Gtk/CursorThemeSize', '24')]:
            contents, count = re.subn(r'^' + re.escape(key) + r'[ \t]+[^\n]*$',
                                      f'{key} {value}', contents, flags=re.MULTILINE)
            if not count:
                contents = contents.rstrip() + f'\n{key} {value}\n'
        write_setting_file(xsettings, contents)

    # xfconfd owns and rewrites its XML. Import preferences instead of linking its database.
    thunar_xml = REPO / 'xfce4/xfconf/xfce-perchannel-xml/thunar.xml'
    print(f'IMPORT {thunar_xml} into xfconf when available')
    if not args.dry_run and not args.skip_thunar and shutil.which('xfconf-query'):
        destination = config / 'xfce4/xfconf/xfce-perchannel-xml/thunar.xml'
        if destination.exists():
            saved = state / destination.relative_to(home)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
        for prop in ET.parse(thunar_xml).getroot().findall('property'):
            kind = prop.attrib['type']
            if kind not in ('string', 'int', 'bool'):
                continue
            command = ['xfconf-query', '-c', 'thunar', '-p', '/' + prop.attrib['name']]
            exists = subprocess.run(command, capture_output=True).returncode == 0
            if not exists:
                command += ['-n', '-t', kind]
            subprocess.run(command + ['-s', prop.attrib['value']], check=True)
    alias = config / 'viegphunt'
    print(f'RETIRE {alias} (only if it links to this checkout’s scripts)')
    if not args.dry_run and alias.is_symlink() and alias.resolve() == (REPO / 'scripts').resolve():
        alias.unlink()
    if not args.dry_run:
        print(f'Existing files backed up under {state}')
        print('Reload Hyprland, Waybar and SwayNC after building native components.')


if __name__ == '__main__':
    main()
