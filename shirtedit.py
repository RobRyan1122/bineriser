
from dataclasses import dataclass
from pathlib import Path
import argparse
import math
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

VALID_EXT = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}
BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Settings:
    threshold: int = 80
    contrast: float = 1.4
    sharpen: float = 0.4
    blur_radius: float = 0.0
    use_dither: bool = False
    invert: bool = False
    dark_color: str = '#aa3cc8'
    light_color: str = '#000000'
    target_width_in: float | None = None
    dpi: int = 300

    def validate(self):
        if not 0 <= self.threshold <= 255:
            raise ValueError('Threshold must be between 0 and 255.')
        for name in ('contrast', 'sharpen', 'blur_radius'):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'{name.replace("_", " ").title()} must be a finite, non-negative number.')
        if self.dpi <= 0:
            raise ValueError('DPI must be a positive whole number.')
        if self.target_width_in is not None:
            if not math.isfinite(self.target_width_in) or self.target_width_in <= 0:
                raise ValueError('Print width must be positive, or blank for original size.')


def process_image(image: Image.Image, settings: Settings) -> Image.Image:
    settings.validate()
    image = ImageOps.exif_transpose(image).convert('RGB')
    if settings.target_width_in is not None:
        width = max(1, round(settings.target_width_in * settings.dpi))
        height = max(1, round(image.height * width / image.width))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(image)
    if settings.blur_radius:
        gray = gray.filter(ImageFilter.GaussianBlur(settings.blur_radius))
    gray = ImageEnhance.Contrast(gray).enhance(settings.contrast)
    if settings.sharpen:
        gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=int(150 * settings.sharpen), threshold=3))
    if settings.invert:
        gray = ImageOps.invert(gray)
    if settings.use_dither:
        # Shift the dither midpoint so the threshold still controls the result.
        gray = gray.point([max(0, min(255, p + 128 - settings.threshold)) for p in range(256)])
        mask = gray.convert('1', dither=Image.Dither.FLOYDSTEINBERG).convert('L')
    else:
        mask = gray.point([255 if p >= settings.threshold else 0 for p in range(256)])
    return ImageOps.colorize(mask, settings.dark_color, settings.light_color)


def process_file(source: Path, destination: Path, settings: Settings):
    with Image.open(source) as image:
        result = process_image(image, settings)
    result.save(destination, format='PNG', dpi=(settings.dpi, settings.dpi))


def launch_gui():
    from gui import run
    run()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', action='store_true', help='Process a folder without opening the GUI')
    parser.add_argument('--input', type=Path, default=BASE_DIR / 'input_images')
    parser.add_argument('--output', type=Path, default=BASE_DIR / 'output_images')
    parser.add_argument('--threshold', type=int, default=80)
    parser.add_argument('--contrast', type=float, default=1.4)
    args = parser.parse_args()
    if not args.batch:
        launch_gui()
        return
    settings = Settings(threshold=args.threshold, contrast=args.contrast)
    settings.validate()
    args.output.mkdir(parents=True, exist_ok=True)
    for path in sorted(args.input.iterdir()):
        if path.is_file() and path.suffix.lower() in VALID_EXT:
            process_file(path, args.output / f'{path.stem}_BW_COLOR.png', settings)
            print(f'Saved {path.name}')


if __name__ == '__main__':
    main()
