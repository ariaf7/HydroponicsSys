from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2

from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2

clicks = []

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

uploaded_files = []

points_display = ui.column()
with points_display:
    ui.label("🖱 Click 4 points on the image to select ROI")

image_container = ui.column()

def on_image_click(e):
    if len(clicks) < 4:
        clicks.append((e.args.x, e.args.y))
        points_display.clear()
        with points_display:
            ui.label("🖱 Click 4 points on the image to select ROI")
            for i, (x, y) in enumerate(clicks, 1):
                ui.label(f"Point {i}: ({int(x)}, {int(y)})")
        if len(clicks) == 4:
            with points_display:
                ui.label("✅ 4 points selected! You can now crop.")
    else:
        ui.notify("Already selected 4 points. Press Reset to start over.", type="warning")

def reset_points():
    clicks.clear()
    points_display.clear()
    with points_display:
        ui.label("🖱 Click 4 points on the image to select ROI")

def show_first_image(files):
    if not files:
        return
    first_file = files[0]
    temp_path = os.path.join(tempfile.gettempdir(), first_file.name)
    first_file.save(temp_path)
    image_container.clear()
    with image_container:
        ui.image(temp_path).on("click", on_image_click).style("cursor: crosshair;")

def process_images():
    if len(clicks) != 4 or not uploaded_files:
        ui.notify("Please upload images and select exactly 4 points", type="warning")
        return

    x_coords = [pt[0] for pt in clicks]
    y_coords = [pt[1] for pt in clicks]
    x, y = min(x_coords), min(y_coords)
    w, h = max(x_coords) - x, max(y_coords) - y
    roi = (x, y, w, h)

    temp_input = tempfile.mkdtemp()
    for file in uploaded_files:
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

ui.button("Reset Points", on_click=reset_points)
ui.button("Crop and Download ZIP", on_click=process_images)

upload = ui.upload(multiple=True).props('accept=".jpg,.jpeg,.png"')

@upload.on("update")
def on_upload(e):
    uploaded_files.clear()
    uploaded_files.extend(e.args)
    reset_points()
    show_first_image(uploaded_files)

# ---------------- RUN SERVER ----------------

ui.run(host="0.0.0.0", port=8080)

