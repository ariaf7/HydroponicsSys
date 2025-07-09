from nicegui import ui
from PIL import Image
import os
import shutil
import zipfile
import tempfile
import io

uploaded_images = []
temp_input_dir = tempfile.mkdtemp()
temp_output_dir = tempfile.mkdtemp()

x_input = y_input = w_input = h_input = None
image_preview = None
zip_buffer = None


def save_uploaded_files(files):
    uploaded_images.clear()
    shutil.rmtree(temp_input_dir)
    os.makedirs(temp_input_dir, exist_ok=True)

    for file in files:
        file_path = os.path.join(temp_input_dir, file.name)
        file.save(file_path)
        uploaded_images.append(file_path)

    if uploaded_images:
        show_image_preview(uploaded_images[0])


def show_image_preview(image_path):
    global image_preview
    if image_preview:
        image_preview.delete()

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img.save("preview.jpg")  # temporary image for UI
        image_preview = ui.image("preview.jpg").classes("w-1/2")


def crop_images():
    global zip_buffer
    x = int(x_input.value)
    y = int(y_input.value)
    w = int(w_input.value)
    h = int(h_input.value)

    shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    for path in uploaded_images:
        try:
            with Image.open(path) as img:
                cropped = img.crop((x, y, x + w, y + h))
                out_path = os.path.join(temp_output_dir, os.path.basename(path))
                cropped.save(out_path)
        except Exception as e:
            print(f"Failed to crop {path}: {e}")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for file in os.listdir(temp_output_dir):
            full_path = os.path.join(temp_output_dir, file)
            zipf.write(full_path, arcname=file)
    zip_buffer.seek(0)

    ui.button("📦 Download Cropped ZIP", on_click=download_zip)


def download_zip():
    if zip_buffer:
        ui.download(zip_buffer, filename="cropped_images.zip")


# --- UI Layout ---
ui.markdown("## 🌿 Crop Images")

ui.upload(
    label="Upload image files",
    multiple=True,
    on_upload=lambda e: save_uploaded_files(e.files),
).props('accept=".jpg,.jpeg,.png"')

with ui.row():
    x_input = ui.number("Crop X", value=0, min=0)
    y_input = ui.number("Crop Y", value=0, min=0)
    w_input = ui.number("Crop Width", value=100, min=1)
    h_input = ui.number("Crop Height", value=100, min=1)

ui.button("✂️ Run Cropping", on_click=crop_images, color="primary")

ui.run()
