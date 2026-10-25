"""Run with .venv\\Scripts\\python.exe test_gui.py (uses offscreen Qt)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from gui import EditorWindow
from shirtedit import Settings, process_image

app = QApplication([])
app.setStyle('Fusion')
app.setStyleSheet(Path('style.qss').read_text())
window = EditorWindow()
window.show()
app.processEvents()
assert not window.save_button.isEnabled()
with TemporaryDirectory() as temp:
    folder = Path(temp)
    source = folder / 'sample.png'
    image = Image.new('RGB', (360, 240))
    for y in range(240):
        for x in range(360):
            v = int(x / 359 * 255)
            image.putpixel((x, y), (v, int(y / 239 * 255), v))
    image.save(source)
    window.load_image(source)
    app.processEvents()
    assert window.save_button.isEnabled()
    assert not window.pixmaps['result'].isNull()
    original_result = window.pixmaps['result'].toImage()
    window.controls['threshold'].setValue(200)
    window.update_preview()
    assert original_result != window.pixmaps['result'].toImage()
    window.reset()
    assert window.settings() == Settings()
    output = folder / 'result.png'
    with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(output), '')):
        window.save_image()
    with Image.open(output) as saved:
        assert saved.size == image.size
        assert saved.tobytes() == process_image(image, Settings()).tobytes()
    batch_input = folder / 'input'
    batch_input.mkdir()
    image.save(batch_input / 'sample.png')
    batch_output = folder / 'output'
    batch_output.mkdir()
    (batch_output / 'sample_BW_COLOR.png').write_bytes(b'preserve')
    with patch.object(QFileDialog, 'getExistingDirectory', side_effect=[str(batch_input), str(batch_output)]), patch.object(QMessageBox, 'information'):
        window.batch()
    assert (batch_output / 'sample_BW_COLOR.png').read_bytes() == b'preserve'
    assert (batch_output / 'sample_BW_COLOR_1.png').exists()
    window.grab().save('gui-preview.png')
window.close()
print('PASS: GUI startup, loading, reactive controls, reset, full-resolution export, batch collision handling')
