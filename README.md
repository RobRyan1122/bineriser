# bineriser

A simple desktop editor for turning images into two-colour graphics, built with
Python, Pillow, and PySide6. Includes automatic previews, colour pickers,
threshold and contrast controls, dithering, print resizing, and folder processing.

## Setup

On Windows, with Python 3.10 or newer installed:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Double-click **Start Image Editor.bat** to open the PySide6 desktop interface.
The launcher uses the local Python environment prepared above.

1. Choose **Open image**.
2. Change threshold, contrast, sharpening, blur, colours, dithering or inversion.
3. The preview updates automatically as you change settings.
4. Choose **Save PNG** to save the full-resolution result.

Higher thresholds map more pixels to the dark colour. Click the colour swatches
to open colour pickers.
Contrast 1 leaves contrast unchanged; 0 produces a flat tone.
Print width is optional; leave it blank to preserve pixel dimensions.
With a print width supplied, pixel width equals inches × DPI.
The preview is reduced for speed and can differ in fine detail from the saved image.
Transparent inputs are converted to RGB, matching the original script.

**Process folder** applies the current settings to all supported images in a
chosen folder. Existing output filenames are given a numerical suffix to avoid
overwriting them. Individual Save PNG uses the normal overwrite confirmation.

The Python `Settings` dataclass also lets other code pass settings directly to
`process_image(image, settings)` without editing global constants.

Optional terminal batch mode:

```powershell
python shirtedit.py --batch --input input_images --output output_images --threshold 80 --contrast 1.4
```

Terminal batch mode overwrites matching output names, like the original script.

## Editing the interface

- `shirtedit.py`: settings, image processing, and terminal entry point.
- `gui.py`: the `EditorWindow` class creates the controls and layout. Change
  button text, section labels, and control ranges in `__init__`. A button's
  `clicked` signal connects it to its action. `QHBoxLayout` arranges widgets
  horizontally, `QVBoxLayout` vertically, and `QFormLayout` pairs labels with fields.
- `style.qss`: Qt's CSS-like stylesheet. Change `background`, `color`,
  `border-radius`, `padding`, and `font-size` here. Selectors such as
  `QPushButton#primary` refer to widgets assigned that name with `setObjectName`.

Save changes and restart the editor to see them. Keep these three files together.

## Standalone Windows executable

After building, `dist/Two Colour.exe` is the standalone app. You can copy that one file to
another Windows x64 PC; Python and the source files are not needed to run it.
The stylesheet is included inside the executable.

After editing the source or stylesheet, rebuild with **Build EXE.bat**.
Build dependencies can be installed with
`.venv\Scripts\python.exe -m pip install -r requirements-build.txt`.
The executable is a snapshot of the files at build time.
