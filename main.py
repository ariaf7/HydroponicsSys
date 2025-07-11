from nicegui import ui, events
from PIL import Image
import os
import tempfile
import shutil
import zipfile
import io
import cv2

clicks = []
uploaded_files = []
ii = None 
def crop_ready():
    x_coords = [pt[0] for pt in clicks]
    y_coords = [pt[1] for pt in clicks]
    x = int(min(x_coords))
    y = int(min(y_coords))
    w = int(max(x_coords) - x)
    h = int(max(y_coords) - y)
    roi = (x, y, w, h)

    # Save uploaded files to temp input folder
    temp_input = tempfile.mkdtemp()
    for file in uploaded_files:
        path = os.path.join(temp_input, file.name)
        with open(path, 'wb') as f:
            f.write(file.content.read())

    # Create temp output folder and run cropping
    temp_output = tempfile.mkdtemp()
    run_cropping(temp_input, temp_output, roi)

    # Zip the cropped images to a file
    zip_path = os.path.join(tempfile.gettempdir(), "cropped_images.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for fname in os.listdir(temp_output):
            fpath = os.path.join(temp_output, fname)
            zipf.write(fpath, arcname=fname)

    # Download the zip file
    ui.download(zip_path, filename="cropped_images.zip")

    # Clean up
    shutil.rmtree(temp_input)
    shutil.rmtree(temp_output)

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

def on_image_click(e: events.MouseEventArguments):
    global ii
    if len(clicks) < 4:
        color = 'SkyBlue' if e.type == 'mousedown' else 'SteelBlue'
        ii.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'
        ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')
        clicks.append([e.image_x, e.image_y])
        ui.notify(f"Point {len(clicks)}: ({int(e.image_x)}, {int(e.image_y)})")
        if len(clicks) == 4:
            ui.notify("✅ 4 points selected! You can now crop.")
            crop_ready()
    else:
        ui.notify("Already selected 4 points. Press Reset to start over.", type="warning")

def reset_points():
    clicks.clear()
    ui.notify("🩹 Points reset. Please click 4 new points on the image.")

def show_first_image():
    global ii
    if not uploaded_files:
        ui.notify("return.",type="warning")
        return
    
    first_file = uploaded_files[0]
    temp_path = os.path.join(tempfile.gettempdir(), first_file.name)
    with open(temp_path, 'wb') as f:
        f.write(first_file.content.read())
    ii = ui.interactive_image(temp_path, on_mouse=on_image_click, events=['click'], cross=True)
    ui.notify("made.",type="warning")

def process_images():
    if not uploaded_files:
        ui.notify("Please", type="warning")
    show_first_image()    
    if len(clicks) != 4 or not uploaded_files:
        ui.notify("Please upload images and select exactly 4 points", type="warning")
        return


ui.button("Reset Points", on_click=reset_points)
ui.button("Crop and Download ZIP", on_click=process_images)

def handle_upload(e: events.UploadEventArguments):
    uploaded_files.append(e)
    ui.notify(f'Uploaded {e.name}')

def update_file_list():
    file_list_container.clear()
    with file_list_container:
        ui.label("Uploaded Files:")
        for file_name in uploaded_files:
            ui.label(file_name)

uploader = ui.upload(on_upload=handle_upload, multiple=True)
uploader.on('finish', update_file_list)

file_list_container = ui.column()

ui.run()
