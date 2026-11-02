# Consolidation verification (2026-11-02)

Verified on the existing CachyOS/Hyprland 0.57.0 desktop:

- 20 Python tests pass, including isolated deployment, idempotency, backup,
  secret preservation and dry-run checks.
- Lua configuration syntax and workspace-preview behavior checks pass.
- Hyprspace builds from the repository snapshot; its two native geometry and
  navigation test executables pass.
- HyprCapture builds from the repository snapshot and vendored JSON headers.
  Its config, security, annotation-editor and helper-startup CTest checks pass.
- Both audio-panel Rust unit tests pass against the relocated source snapshot.
- An exported staged checkout deploys into a temporary HOME with the generic
  profile, valid generated SwayNC config, resolved icon links, and no prebuilt
  binaries. The export is removed after inspection.
- The real desktop has both plugins loaded and no Hyprland configuration errors.
  Capture opens from the relocated helper. Waybar and SwayNC reload successfully.
- The old script alias is removed; active/legacy callers use the actual scripts
  folder. Existing Fish secret and runtime files remain outside this checkout.
- Included asset/source symlinks resolve, no indexed native ELF binaries are
  present, and no individual included file exceeds 90 MB.
- Publishing inputs were checked for private-key/API-token signatures. Accounts,
  browser profiles, VPN/Wi-Fi credentials, secrets and histories are not copied.
- Whitespace checks pass for the maintained configuration, deployment scripts,
  helper scripts and documentation. Some copied upstream sources/themes and
  historical patches retain pre-existing whitespace warnings; their content was
  preserved rather than reformatted for this migration.

This is not a full installation on a second physical machine. Other monitor
layouts, distributions, GPU drivers, audio hardware, laptop charging interfaces
and login managers may require their own profile/dependencies. Full Wi-Fi
connection/password entry and Bluetooth pairing were not exercised by this
migration. The installer does not enable optional system services or change
credentials. The generic profile intentionally disables the fixed dashboard.

Future plugin/Qt updates require a matching rebuild. The build helper refuses
to rebuild a plugin while it is loaded in the current Hyprland session.
