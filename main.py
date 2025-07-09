from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2

def run_cropping(input_folder, output_folder, roi):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        filepath = os.path.join(input_folder, filename)
        image = cv2.imread(filepath)
        if image is None:
            continue
        x, y, w, h = roi
        cropped = image[int(y):int(y + h), int(x):int(x + w)]
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, cropped)

clicks = []

def on_image_click(e):
    if len(clicks) < 4:
        clicks.append((e.args.x, e.args.y))
        with ui.row():
            ui.label(f"Point {len(clicks)}: ({e.args.x}, {e.args.y})")
    if len(clicks) == 4:
        with ui.row():
            ui.label("✅ 4 points selected! You can now crop.")

def reset_points():
    clicks.clear()

with ui.column():
    uploaded = ui.upload(multiple=True).props('accept=".jpg,.png,.jpeg"')

    image_container = ui.column()
    start_button = ui.button("Start Cropping", on_click=reset_points)

    def process_images():
        if len(clicks) != 4 or not uploaded.value:
            ui.notify("Upload images and select 4 points", type="warning")
            return

        x_coords = [pt[0] for pt in clicks]
        y_coords = [pt[1] for pt in clicks]
        x, y = min(x_coords), min(y_coords)
        w, h = max(x_coords) - x, max(y_coords) - y
        roi = (x, y, w, h)

        temp_input = tempfile.mkdtemp()
        for file in uploaded.files:
            file.save(os.path.join(temp_input, file.name))

        temp_output = tempfile.mkdtemp()
        run_cropping(temp_input, temp_output, roi)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for fname in os.listdir(temp_output):
                fpath = os.path.join(temp_output, fname)
                zipf.write(fpath, arcname=fname)
        zip_buffer.seek(0)

        ui.download(data=zip_buffer, filename="cropped_images.zip")
        shutil.rmtree(temp_input)
        shutil.rmtree(temp_output)

    crop_button = ui.button("Crop and Download ZIP", on_click=process_images)

    def show_first_image():
        if uploaded.value:
            file = uploaded.files[0]
            path = os.path.join(tempfile.gettempdir(), file.name)
            file.save(path)
            img_ui = ui.image(path).on("click", on_image_click).style("cursor: crosshair;")
            image_container.clear()
            image_container.add(img_ui)

    uploaded.on("change", show_first_image)
