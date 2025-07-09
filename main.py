from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2
from nicegui.events import MouseEventArguments
from nicegui.elements.image import Image as UIImage

# Title
ui.label("🌱 Hydroponic System Image Cropper").classes("text-2xl font-bold mb-4")

# Globals
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


def on_image_click(e: MouseEventArguments):
    if len(clicks) < 4:
        clicks.append((e.image_x, e.image_y))
        with ui.row():
            ui.label(f"Point {len(clicks)}: ({int(e.image_x)}, {int(e.image_y)})")

    image_container.clear()
    show_first_image(overlay=True)

    if len(clicks) == 4:
        with ui.row():
            ui.label("✅ 4 points selected! You can now crop.")

def reset_points():
    clicks.clear()
    ui.notify("🧹 Cleared points", type="info")
# Upload
uploaded = ui.upload(multiple=True).props('accept=".jpg,.png,.jpeg"')

# UI elements
image_container = ui.column()

def handle_reset():
    reset_points()
    image_container.clear()
    show_first_image()

ui.button("🧹 Reset Points", on_click=handle_reset)


# Cropping logic
def process_images():
    uploaded_file_list = uploaded._props.get('files', [])
    if len(clicks) != 4 or not uploaded_file_list:
        ui.notify("Upload images and select 4 points", type="warning")
        return

    x_coords = [pt[0] for pt in clicks]
    y_coords = [pt[1] for pt in clicks]
    x, y = min(x_coords), min(y_coords)
    w, h = max(x_coords) - x, max(y_coords) - y
    roi = (x, y, w, h)

    temp_input = tempfile.mkdtemp()
    for file in uploaded_file_list:
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

ui.button("📦 Crop and Download ZIP", on_click=process_images)

# Display uploaded image
def show_first_image(overlay=False):
    if uploaded_files:
        file = uploaded_files[0]
        path = os.path.join(tempfile.gettempdir(), file.name)
        file.save(path)

        img = UIImage(path).on("click", on_image_click).style("cursor: crosshair;")
        image_container.clear()
        image_container.add(img)

        if overlay and clicks:
            with image_container:
                for i, (x, y) in enumerate(clicks):
                    ui.label(f"🔴 Point {i+1}: ({int(x)}, {int(y)})").style(f'position: absolute; left: {x}px; top: {y}px; color: red; font-size: 10px;')

                if len(clicks) == 4:
                    # Draw transparent rectangle from min/max points
                    x_coords = [pt[0] for pt in clicks]
                    y_coords = [pt[1] for pt in clicks]
                    x, y = min(x_coords), min(y_coords)
                    w, h = max(x_coords) - x, max(y_coords) - y
                    rectangle_style = (
                        f'position: absolute; '
                        f'left: {x}px; top: {y}px; '
                        f'width: {w}px; height: {h}px; '
                        f'border: 2px solid red; background-color: rgba(255, 0, 0, 0.2);'
                    )
                    ui.label("").style(rectangle_style)

uploaded.on("change", show_first_image)

# ---------------- RUN SERVER ----------------

ui.run(host="0.0.0.0", port=8080)

