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
                          'assets/wallpapers', 'scripts', 'xfce4/xfconf/xfce-perchannel-xml']
            for name in components:
                (checkout / name).mkdir(parents=True, exist_ok=True)
            for name in ['swaync/config.json.in', 'gtk-3.0/bookmarks.template',
                         'xfce4/xfconf/xfce-perchannel-xml/thunar.xml', 'scripts/screen-record']:
                shutil.copy2(REPO / name, checkout / name)
            shutil.copytree(REPO / 'fish', checkout / 'fish')
            original = home / '.config/ghostty'
            original.mkdir(parents=True)
            (original / 'config').write_text('original config')
            fish = home / '.config/fish'
            fish.mkdir()
            (fish / 'secrets.fish').write_text('local-only secret placeholder')
            (fish / 'fish_variables').write_text('local runtime state')
            (home / '.config/viegphunt').symlink_to(checkout / 'scripts')
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


if __name__ == '__main__':
    unittest.main(buffer=True)
