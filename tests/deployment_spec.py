"""Deployment preserves local state and is safe to rerun in a new HOME."""
import os
import json
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class DeploymentTests(unittest.TestCase):
    def test_dry_run_does_not_replace_existing_config(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            original = home / '.config/ghostty'
            original.mkdir(parents=True)
            (original / 'config').write_text('font-size = 12\n')
            result = subprocess.run(['python3', str(REPO / 'install/deploy.py'), '--dry-run', '--skip-thunar'],
                                    env=dict(os.environ, HOME=folder), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(original.is_symlink())
            self.assertEqual((original / 'config').read_text(), 'font-size = 12\n')
            self.assertFalse((home / '.local/state/hypr-dots-backups').exists())


    def test_install_backs_up_configs_preserves_secrets_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            checkout = Path(folder) / 'checkout'
            home = Path(folder) / 'home'
            (checkout / 'install').mkdir(parents=True)
            shutil.copy2(REPO / 'install/deploy.py', checkout / 'install/deploy.py')
            components = ['waybar', 'rofi', 'swaync', 'wlogout', 'cava', 'ghostty', 'colors',
                          'gtk-3.0', 'gtk-4.0', 'Thunar', 'fontconfig', 'wifi-manager',
                          'ohmyposh', 'fcitx5', 'config', 'assets/icons', 'assets/themes',
                          'assets/wallpapers', 'scripts', 'desktop', 'xfce4/xfconf/xfce-perchannel-xml']
            for name in components:
                (checkout / name).mkdir(parents=True, exist_ok=True)
            for name in ['swaync/config.json.in', 'gtk-3.0/bookmarks.template',
                         'xfce4/xfconf/xfce-perchannel-xml/thunar.xml', 'scripts/screen-record']:
                shutil.copy2(REPO / name, checkout / name)
            shutil.copytree(REPO / 'fish', checkout / 'fish')
            shutil.copytree(REPO / 'assets/icons/default', checkout / 'assets/icons/default')
            shutil.copy2(REPO / 'desktop/org.freedesktop.FileManager1.service', checkout / 'desktop')
            original = home / '.config/ghostty'
            original.mkdir(parents=True)
            (original / 'config').write_text('original config')
            fish = home / '.config/fish'
            fish.mkdir()
            (fish / 'secrets.fish').write_text('local-only secret placeholder')
            (fish / 'fish_variables').write_text('local runtime state')
            (home / '.config/viegphunt').symlink_to(checkout / 'scripts')
            (home / '.config/mimeapps.list').write_text(
                '[Default Applications]\ninode/directory=kitty-open.desktop;\ntext/html=firefox.desktop;\n')
            (home / '.config/kcminputrc').write_text('[Mouse]\ncursorSize=30\nOtherSetting=keep\n')
            xsettings = home / '.config/xsettingsd/xsettingsd.conf'
            xsettings.parent.mkdir()
            xsettings.write_text('Gtk/CursorThemeSize 30\nNet/IconThemeName "breeze"\n')
            command = ['python3', str(checkout / 'install/deploy.py'), '--shell', '--input', '--skip-thunar']
            for _ in range(2):
                result = subprocess.run(command, env=dict(os.environ, HOME=str(home)), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(original.resolve(), checkout / 'ghostty')
            saved = list((home / '.local/state/hypr-dots-backups').glob('*/.config/ghostty/config'))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].read_text(), 'original config')
            self.assertEqual((fish / 'secrets.fish').read_text(), 'local-only secret placeholder')
            self.assertEqual((fish / 'fish_variables').read_text(), 'local runtime state')
            self.assertFalse((home / '.config/viegphunt').exists())
            self.assertFalse((home / '.config/viegphunt').is_symlink())
            self.assertNotIn('@HOME@', (checkout / 'gtk-3.0/bookmarks').read_text())
            json.loads((checkout / 'swaync/config.json').read_text())
            self.assertIn('dashboard = false', (checkout / 'config/local.lua').read_text())
            associations = (home / '.config/mimeapps.list').read_text()
            self.assertIn('inode/directory=thunar.desktop;', associations)
            self.assertIn('text/html=firefox.desktop;', associations)
            self.assertEqual(len(list((home / '.local/state/hypr-dots-backups').glob('*/.config/mimeapps.list'))), 1)
            self.assertIn('cursorSize=24', (home / '.config/kcminputrc').read_text())
            self.assertIn('OtherSetting=keep', (home / '.config/kcminputrc').read_text())
            self.assertIn('Gtk/CursorThemeSize 24', xsettings.read_text())
            self.assertIn('Net/IconThemeName "breeze"', xsettings.read_text())
            self.assertEqual((home / '.icons/default').resolve(), checkout / 'assets/icons/default')
            self.assertTrue((home / '.local/share/dbus-1/services/org.freedesktop.FileManager1.service').is_file())


if __name__ == '__main__':
    unittest.main(buffer=True)
