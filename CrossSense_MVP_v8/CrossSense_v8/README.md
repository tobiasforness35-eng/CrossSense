# CrossSense v8

DualSense Cross Deadzone mapper with virtual Xbox output for Rocket League.

## Current recommended Rocket League profile

- Inner deadzone: `6.0`
- Outer saturation: `83.0`
- Forward boost: `0.0`
- Mode: Pure Steam Cross 6–83 feel

Only use `Safe boost 1.0` or `Boost 1.5` if frontflip cancel feels weak. If Pure 6–83 feels good, leave boost at `0.0`.

## How to run

1. Close DS4Windows completely.
2. Connect DualSense with USB.
3. Right-click `run_crosssense.bat` and choose **Run as administrator**.
4. Press **Start profile**.
5. Open Rocket League after CrossSense is active.

Windows should show one virtual controller called `Controller (XBOX 360 For Windows)` from CrossSense.

## No black CMD window

After the normal launcher has installed dependencies once, you can try:

- `run_crosssense_silent.vbs`

This opens CrossSense without the visible CMD window.

## Build a real EXE

Run:

- `build_exe.bat`

It creates:

- `dist/CrossSense.exe`

The EXE is built on your Windows PC because this chat environment cannot compile a Windows EXE directly.

## Desktop shortcut

Run:

- `make_desktop_shortcut.bat`

It creates a Desktop shortcut that opens the silent launcher.

## Hide original DualSense

CrossSense outputs a virtual Xbox controller. Rocket League may still see the original DualSense too.
If you get double input, use the **Hide DualSense guide** button in the app and configure HidHide manually.

Do not hide the virtual Xbox controller. Hide only the physical DualSense from games.
