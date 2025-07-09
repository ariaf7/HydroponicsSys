from nicegui import ui
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2

clicks = []
uploaded_files = []

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

def on_image_click(e):
    if len(clicks) < 4:
        clicks.append((e.args.x, e.args.y))
        points_display.clear()
        for i, pt in enumerate(clicks):
            points_display.label(f"Point {i+1}: {pt}")
        if len(clicks) == 4:
            points_display.label("✅ 4 points selected! You can now crop.")

def reset_points():
    clicks.clear()
    points_display.clear()
    with points_display:
        ui.label("🖱 Click 4 points on the image to select ROI")


def process_images():
    if len(clicks) != 4 or not uploaded_files:
        ui.notify("Upload images and click 4 points", type="warning")
        return

    x_coords = [pt[0] for pt in clicks]
    y_coords = [pt[1] for pt in clicks]
    x, y = min(x_coords), min(y_coords)
    w, h = max(x_coords) - x, max(y_coords) - y
    roi = (x, y, w, h)

    temp_input = tempfile.mkdtemp()
    for file in uploaded_files:
        save_path = os.path.join(temp_input, file.name)
        file.save(save_path)

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

def show_first_image():
    if uploaded_files:
        file = uploaded_files[0]
        temp_path = os.path.join(tempfile.gettempdir(), file.name)
        file.save(temp_path)
        image_container.clear()
        image_container.image(temp_path).on("click", on_image_click).style("cursor: crosshair")

with ui.column():
    ui.label("🌿 Hydroponic System Cropping Tool").classes("text-2xl font-bold")

    # Upload section
    def handle_upload(e):
        uploaded_files.clear()
        uploaded_files.extend(e.files)
        reset_points()
        show_first_image()

    ui.upload(multiple=True, on_upload=handle_upload).props('accept=".jpg,.png,.jpeg"')

    image_container = ui.column()
    points_display = ui.column()

    with ui.row():
        ui.button("🔄 Reset Points", on_click=reset_points)
        ui.button("✂️ Crop and Download ZIP", on_click=process_images)


# ---------------- RUN SERVER ----------------

ui.run(host="0.0.0.0", port=8080)

