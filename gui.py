
import sys
from dataclasses import replace
from pathlib import Path
from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QPushButton, QSpinBox, QDoubleSpinBox,
    QCheckBox, QColorDialog, QFileDialog, QMessageBox, QScrollArea,
    QGroupBox, QSplitter,
)
from shirtedit import Settings, process_image, process_file, VALID_EXT


class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Two Colour · Image editor')
        self.resize(1120, 780)
        self.source = None
        self.source_path = None
        self.controls = {}
        self.colours = {}
        self.pixmaps = {}
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(160)
        self.timer.timeout.connect(self.update_preview)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(18)
        header = QHBoxLayout()
        title = QLabel('Two Colour')
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()
        self.button(header, 'Open image', self.open_image)
        self.button(header, 'Process folder', self.batch)
        self.save_button = self.button(header, 'Save PNG', self.save_image)
        self.save_button.setObjectName('primary')
        self.save_button.setEnabled(False)
        outer.addLayout(header)

        splitter = QSplitter()
        outer.addWidget(splitter, 1)
        sidebar = QWidget()
        sidebar.setMinimumWidth(285)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 12, 0)
        defaults = Settings()
        adjustments = QGroupBox('Adjustments')
        form = QFormLayout(adjustments)
        form.setSpacing(14)
        for name, label, maximum, step in [
            ('threshold', 'Threshold', 255, 1),
            ('contrast', 'Contrast', 20, .1),
            ('sharpen', 'Sharpen', 20, .1),
            ('blur_radius', 'Blur radius', 100, .1),
        ]:
            control = QSpinBox() if name == 'threshold' else QDoubleSpinBox()
            control.setRange(0, maximum)
            control.setSingleStep(step)
            control.setValue(getattr(defaults, name))
            control.valueChanged.connect(self.schedule_preview)
            self.controls[name] = control
            form.addRow(label, control)
        for name, label in [('use_dither', 'Dither'), ('invert', 'Invert light and dark')]:
            control = QCheckBox(label)
            control.toggled.connect(self.schedule_preview)
            self.controls[name] = control
            form.addRow(control)
        side.addWidget(adjustments)

        colours = QGroupBox('Output colours')
        colour_form = QFormLayout(colours)
        for name, label in [('dark_color', 'Dark pixels'), ('light_color', 'Light pixels')]:
            button = QPushButton()
            button.clicked.connect(lambda checked=False, n=name: self.choose_colour(n))
            self.controls[name] = button
            self.set_colour(name, getattr(defaults, name))
            colour_form.addRow(label, button)
        side.addWidget(colours)

        export = QGroupBox('Print settings')
        export_form = QFormLayout(export)
        width = QDoubleSpinBox()
        width.setRange(0, 1000)
        width.setSpecialValueText('Original size')
        width.setSuffix(' in')
        self.controls['target_width_in'] = width
        export_form.addRow('Width', width)
        dpi = QSpinBox()
        dpi.setRange(1, 9600)
        dpi.setValue(defaults.dpi)
        self.controls['dpi'] = dpi
        export_form.addRow('DPI', dpi)
        side.addWidget(export)
        self.button(side, 'Reset settings', self.reset)
        side.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(sidebar)
        splitter.addWidget(scroll)

        previews = QWidget()
        preview_layout = QHBoxLayout(previews)
        preview_layout.setContentsMargins(12, 0, 0, 0)
        self.labels = {}
        for key, heading in [('original', 'ORIGINAL'), ('result', 'TWO COLOUR')]:
            panel = QVBoxLayout()
            label = QLabel(heading)
            label.setObjectName('caption')
            panel.addWidget(label)
            image_label = QLabel('Open an image to begin')
            image_label.setObjectName('preview')
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setMinimumSize(180, 220)
            image_label.setWordWrap(True)
            self.labels[key] = image_label
            panel.addWidget(image_label, 1)
            preview_layout.addLayout(panel, 1)
        splitter.addWidget(previews)
        splitter.setSizes([300, 800])
        splitter.setStretchFactor(1, 1)
        self.statusBar().showMessage('Open an image ')

    @staticmethod
    def button(layout, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    def schedule_preview(self, *_):
        self.timer.start()

    def settings(self):
        values = {}
        for name, control in self.controls.items():
            if name in self.colours:
                values[name] = self.colours[name]
            elif isinstance(control, QCheckBox):
                values[name] = control.isChecked()
            else:
                values[name] = control.value()
        values['target_width_in'] = values['target_width_in'] or None
        return Settings(**values)

    def set_colour(self, name, value):
        self.colours[name] = value
        colour = QColor(value)
        ink = '#111111' if colour.lightness() > 140 else '#ffffff'
        self.controls[name].setText(value.upper())
        self.controls[name].setStyleSheet(f'background: {value}; color: {ink};')

    def choose_colour(self, name):
        colour = QColorDialog.getColor(QColor(self.colours[name]), self, 'Choose output colour')
        if colour.isValid():
            self.set_colour(name, colour.name())
            self.schedule_preview()

    def load_image(self, path):
        with Image.open(path) as image:
            source = ImageOps.exif_transpose(image).convert('RGB')
        self.source = source
        self.source_path = Path(path)
        self.save_button.setEnabled(True)
        self.update_preview()

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open image', '', 'Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp)')
        if path:
            try:
                self.load_image(path)
            except Exception as error:
                QMessageBox.warning(self, 'Could not open image', str(error))

    def update_preview(self):
        if self.source is None:
            return
        small = self.source.copy()
        small.thumbnail((1000, 1000))
        result = process_image(small, replace(self.settings(), target_width_in=None))
        for key, image in [('original', small), ('result', result)]:
            rgb = image.convert('RGB')
            qimage = QImage(rgb.tobytes(), rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888).copy()
            self.pixmaps[key] = QPixmap.fromImage(qimage)
        self.fit_previews()
        self.statusBar().showMessage(f'{self.source_path.name} · {self.source.width} × {self.source.height} px')

    def fit_previews(self):
        for key, pixmap in self.pixmaps.items():
            self.labels[key].setPixmap(pixmap.scaled(self.labels[key].size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'pixmaps'):
            self.fit_previews()

    def save_image(self):
        if self.source is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save PNG', f'{self.source_path.stem}_BW_COLOR.png', 'PNG image (*.png)')
        if not path:
            return
        try:
            settings = self.settings()
            process_image(self.source, settings).save(path, format='PNG', dpi=(settings.dpi, settings.dpi))
            self.statusBar().showMessage(f'Saved {path}')
        except Exception as error:
            QMessageBox.warning(self, 'Could not save image', str(error))

    def reset(self):
        defaults = Settings()
        for name, control in self.controls.items():
            value = getattr(defaults, name)
            if name in self.colours:
                self.set_colour(name, value)
            elif isinstance(control, QCheckBox):
                control.setChecked(value)
            else:
                control.setValue(value or 0)
        self.schedule_preview()

    def batch(self):
        source = QFileDialog.getExistingDirectory(self, 'Choose input folder')
        if not source:
            return
        target = QFileDialog.getExistingDirectory(self, 'Choose output folder')
        if not target:
            return
        files = sorted(p for p in Path(source).iterdir() if p.is_file() and p.suffix.lower() in VALID_EXT)
        failures = []
        settings = self.settings()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for path in files:
                output = Path(target) / f'{path.stem}_BW_COLOR.png'
                count = 1
                while output.exists():
                    output = Path(target) / f'{path.stem}_BW_COLOR_{count}.png'
                    count += 1
                try:
                    process_file(path, output, settings)
                except Exception as error:
                    failures.append(f'{path.name}: {error}')
        finally:
            QApplication.restoreOverrideCursor()
        QMessageBox.information(self, 'Batch complete', f'Saved {len(files) - len(failures)} of {len(files)} images.\n' + '\n'.join(failures))


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(Path(__file__).with_name('style.qss').read_text(encoding='utf-8'))
    window = EditorWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    run()
