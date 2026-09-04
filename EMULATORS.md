# PC-98 emulator setup

[WebNP2](https://uraraworks.github.io/WebNP2/?lang=en) runs in a browser.
[RetroArch](https://www.retroarch.com/) with the Neko Project II Kai core is a
local alternative. Both accept user-supplied PC-98 disk images. This repository
does not host a player, firmware, or disk images.

## WebNP2 and the font fix

WebNP2 includes a replacement bitmap font, `font.bmp`, derived from Shinonome.
Without a registered font ROM, its lettering can look very different from a
desktop emulator. These are emulated PC-98 glyphs, so changing browser fonts
will not change them.

To use the same font as an existing desktop setup:

1. Open **More → ROM Files**.
2. Choose **Select Files** and select the desktop emulator's `FONT.ROM`.
3. Confirm that the dialog lists `font.rom`, then choose **Reload Page**.
4. Start the emulator afresh so it loads the new font.

WebNP2 normalizes the filename and prefers a registered `font.rom` over its
bundled bitmap. Registration stores the file locally in that browser; it does
not upload it. The setting persists across visits until the site's storage is
cleared.

We checked this on September 4, 2026 with WebNP2 build `954dfe3+`. The browser
initially reported no registered ROM files. Registering the same 288,768-byte
`FONT.ROM` used by our desktop setup restored the expected lettering, confirmed
visually by the user. This verifies the font correction, not general browser
compatibility or a complete playthrough.

Disk images and changes also stay in browser storage. Download modified disks
as backups before clearing site data or moving to another browser or device.
See the [WebNP2 user guide](https://uraraworks.github.io/WebNP2/help.html?lang=en)
for disk handling, input controls, and save states.

## RetroArch

1. Install RetroArch for your operating system. On Apple Silicon, use an arm64
   build and matching arm64 cores; mixing an Intel core with an arm64 frontend
   prevents the core from loading.
2. Use **Online Updater → Core Downloader** to install **NEC - PC-98 (Neko
   Project II Kai)**. If your distribution does not provide the downloader,
   use its core installation method instead.
3. Check **Settings → Directory → System/BIOS**. Create an `np2kai` subdirectory
   inside that directory and put your NP2kai firmware there. The
   [core documentation](https://docs.libretro.com/library/neko_project_ii_kai/#bios)
   lists the firmware filenames and optional sound assets.
4. For consistent lettering, use the same `FONT.ROM` as in WebNP2. Our inspected
   macOS setup uses `~/Documents/RetroArch/system/np2kai/FONT.ROM`; the location
   depends on the configured System/BIOS directory, not the operating system
   alone.
5. Load the Neko Project II Kai core. **Information → Core Information** helps
   check firmware availability. Use **Load Content** to select your own
   supported PC-98 image; the core supports HDI and several floppy formats.

The core's **F11** shortcut toggles mouse capture, and **F12** opens its own
machine menu. On keyboards that reserve function keys for media controls, you
may need **Fn**. See the
[core's controls documentation](https://docs.libretro.com/library/neko_project_ii_kai/#usage)
for details.

Back up writable disk images after closing the emulator. Keep emulator save
states separately, and do not assume they transfer between WebNP2 and
RetroArch or between different core versions.

### If the fonts still differ

Check which file is actually available, not just the configured filename.
Our desktop `np2kai.cfg` pointed to a missing `font.bmp`; NP2kai then found
`FONT.ROM` through its fallback search. WebNP2 had a real bundled `font.bmp`,
so it used different glyph data. A successfully loaded bitmap can take
precedence over the corresponding ROM glyphs in the desktop loader: inspect
the `fontfile` setting and point it explicitly at your intended font when
necessary, with the emulator closed.

After changing font assets, start afresh rather than restoring an old emulator
state. Matching the glyph data addresses letter shapes; display scaling and
filtering can still affect their apparent sharpness.
