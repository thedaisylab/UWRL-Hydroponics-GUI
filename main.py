from nicegui import ui, events, app,run
import uuid
import os
import tempfile
import shutil
import zipfile
import cv2
from backend import *
from PIL import Image
import threading
# ui.markdown("## 🌱 **Hydroponic System Analysis**")
clicks = []
ii = None 
mask_zip_path = ''
file_list_column = ui.column()
mask_uploader = None
start_growth_button = None
##### UPLOAD LOGIC#####
UPLOAD_DIR = Path('/tmp/hydro_uploads')
GROWTH_DIR = Path('/tmp/hydro_growth')
MASK_DIR = Path('/tmp/hydro_masks')

UPLOAD_DIR.mkdir(exist_ok=True)
GROWTH_DIR.mkdir(exist_ok=True)
MASK_DIR.mkdir(exist_ok=True)

session_id = str(uuid.uuid4())

session_dir = UPLOAD_DIR / session_id
growth_session_dir = GROWTH_DIR / session_id
mask_session_dir = MASK_DIR / session_id

for d in [session_dir, growth_session_dir, mask_session_dir]:
    d.mkdir(parents=True, exist_ok=True)

uploaded_file_paths = []
uploaded_mask_paths = []


def save_uploaded_file(event):
    file = event.name
    path = session_dir / file
    content = event.content.read()  # Read once
    with open(path, 'wb') as f:
        f.write(content)
    uploaded_file_paths.append(str(path))  # Convert to string if needed
    # with ui.column():
    #     ui.label(f'✅ Uploaded: {file}')


file_list_column = ui.column()    

def save_uploaded_mask(event):
    file = event.name
    path = mask_session_dir / file
    content = event.content.read()
    with open(path, 'wb') as f:
        f.write(content)
    uploaded_mask_paths.append(str(path))

def update_file_list_display():
    file_list_column.clear()
    with file_list_column:
        for f in uploaded_file_paths:
            print(Path(f).name)
        for f in uploaded_mask_paths:
            print(Path(f).name)
def handle_upload(e):
    # uploaded_files.clear()
    uploaded_file_paths.append(e)
    update_file_list_display()

# with ui.row():
#     uploader = ui.upload(on_upload=save_uploaded_file, multiple=True)
    

# Show the current file list
update_file_list_display()

######## CROP ######
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
    for src_path in uploaded_file_paths:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(temp_input, filename)
        shutil.copy2(src_path, dest_path)
        print(f"[DEBUG] Copied {filename} to {dest_path}")




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
    clicks.clear()
    image_container.clear()  # this removes the interactive image from the UI

def on_image_click(e: events.MouseEventArguments):
    global ii
    if len(clicks) < 4:
        color = 'SkyBlue' if e.type == 'mousedown' else 'SteelBlue'
        ii.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'
        # ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')
        clicks.append([e.image_x, e.image_y])
        # ui.notify(f"Point {len(clicks)}: ({int(e.image_x)}, {int(e.image_y)})")
        if len(clicks) == 4:
            ui.notify("✅ 4 points selected! You can now crop.")
            ui.timer(0.1, crop_ready, once=True)
    else:
        ui.notify("Already selected 4 points. Press Reset to start over.", type="warning")

def reset_points():
    clicks.clear()
    ui.notify("🩹 Points reset. Please click 4 new points on the image.")

image_container = ui.row()  # ✅ define your container

def show_first_image():
    global ii
    if not uploaded_file_paths:
        ui.notify("Upload files", type="warning")
        return

    first_file_path = uploaded_file_paths[0]

    if not os.path.exists(first_file_path):
        ui.notify(f"File not found: {first_file_path}", type="warning")
        return

    image_container.clear()

    with image_container:
        ii = ui.interactive_image(
            str(first_file_path),  # ⬅️ Pass path as string
            on_mouse=on_image_click,
            events=['click'],
            cross=True
        )

def process_images():
    if not uploaded_file_paths:
        ui.notify("Please upload files", type="warning")
    show_first_image()    
    if len(clicks) != 4 or not uploaded_file_paths:
        ui.notify("Please select exactly 4 points", type="warning")
        return

file_list_container = ui.column()

######## TIMELAPSE ######


def process_timelapse():
    if not uploaded_file_paths:
        ui.notify("Please upload images first", type="warning")
        return
    make_and_download_timelapse(uploaded_file_paths, 1.0)


def make_and_download_timelapse(uploaded_file_paths, fps):
    temp_input = tempfile.mkdtemp()
    temp_video = os.path.join(tempfile.gettempdir(), f"timelapse_{uuid.uuid4().hex}.mp4")

    try:
        # Save uploaded files to temp
        for src_path in uploaded_file_paths:
            filename = os.path.basename(src_path)
            dest_path = os.path.join(temp_input, filename)
            shutil.copy2(src_path, dest_path)
            print(f"[DEBUG] Copied {filename} to {dest_path}")


        print(f"[TIMELAPSE] Generating video at {temp_video}")
        success = run_timelapse(temp_input, temp_video, fps=fps)

        if success and os.path.exists(temp_video):
            ui.download(temp_video, filename="timelapse.mp4")
            ui.notify("🎬 Timelapse is ready to download!")
        else:
            ui.notify("❌ Failed to generate timelapse")
    finally:
        shutil.rmtree(temp_input, ignore_errors=True)
######### MASKS #########
def process_masking():
    if not uploaded_file_paths:
        ui.notify("Please upload images first.", type="warning")
        return

    temp_input = tempfile.mkdtemp()
    try:
        # Copy files to temp folder
        for file_path in uploaded_file_paths:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(temp_input, filename)
            shutil.copy2(file_path, dest_path)

        print("[MASK] Starting run_mask()")
        zip_path = run_mask(temp_input, tempfile.gettempdir())

        if os.path.exists(zip_path):
            ui.download(zip_path, filename="masks.zip")
            ui.notify("✅ Masks ready for download!")
        else:
            ui.notify("❌ Masking failed: No ZIP file found.", type="warning")

    except Exception as e:
        print(f"[MASK] Error: {e}")
        ui.notify(f"❌ Masking failed: {e}", type="warning")
    finally:
        shutil.rmtree(temp_input, ignore_errors=True)

######GROWTH WORKING******
def process_growth():
    if not uploaded_file_paths:
        ui.notify("Please upload BINARY images first.", type="warning")
        return

    temp_input = tempfile.mkdtemp()
    try:
        # Copy files to temp folder
        for file_path in uploaded_file_paths:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(temp_input, filename)
            shutil.copy2(file_path, dest_path)

        print("[MASK] Starting run_mask()")
        zip_path = run_graph(temp_input, tempfile.gettempdir())

        if os.path.exists(zip_path):
            ui.download(zip_path, filename="graphs.zip")
            ui.notify("✅ Graphs ready for download!")
        else:
            ui.notify("❌ Graphing failed: No ZIP file found.", type="warning")

    except Exception as e:
        print(f"[GRAPH] Error: {e}")
        ui.notify(f"❌ Graphing failed: {e}", type="warning")
    finally:
        shutil.rmtree(temp_input, ignore_errors=True)
###### GROWTH NOT WORKING #####
def downscale_image(path: Path, max_size=(800, 800)):
    with Image.open(path) as img:
        img.thumbnail(max_size)
        img.save(path)

def show_mask_uploader():
    global mask_uploader, start_growth_button
    if mask_uploader is None:
        with ui.row():
            mask_uploader = ui.upload(
                label="Upload masks here",
                multiple=True,
                on_upload=save_uploaded_mask
            )
    else:
        mask_uploader.show()

    if start_growth_button is None:
        start_growth_button = ui.button("Start Growth Analysis", on_click=process_growth)
    else:
        start_growth_button.show()
from pathlib import Path

def threaded_growth(uploaded_files, mask_dir, zip_output_path, on_success, on_failure):
    temp_input_dir = Path(tempfile.mkdtemp())
    growth_output_dir = zip_output_path.parent
    temp_mask_dir = Path(tempfile.mkdtemp())

    try:
        # Copy uploaded images into the temporary input dir
        for file_path in uploaded_files:
            dest = temp_input_dir / Path(file_path).name
            shutil.copy2(file_path, dest)
            downscale_image(dest) 

        # Copy and preprocess masks
        for mask_file in mask_session_dir.iterdir():
            dest = temp_mask_dir / mask_file.name
            shutil.copy2(mask_file, dest)
            downscale_image(dest)

        # Run your long blocking task
        run_growth(
            str(temp_input_dir),
            str(temp_mask_dir),
            str(growth_output_dir),
            str(zip_output_path)
        )

        if zip_output_path.exists():
            on_success(zip_output_path)
        else:
            on_failure("ZIP file not found.")

    except Exception as e:
        on_failure(str(e))
    finally:
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        shutil.rmtree(growth_output_dir, ignore_errors=True)

async def process_growth_BAD():
    if not uploaded_file_paths:
        ui.notify("⚠️ Please upload images first.", type="warning")
        return

    if not mask_session_dir.exists() or not any(mask_session_dir.iterdir()):
        ui.notify("⚠️ Please upload masks before running growth analysis.", type="warning")
        return

    zip_output_path = Path(tempfile.gettempdir()) / "growth_results.zip"
    ui.notify("🛠️ Running growth analysis in background...")

    def on_success(zip_path):
        ui.notify("✅ Growth analysis complete!")
        ui.download(str(zip_path), filename="growth_results.zip")

    def on_failure(msg):
        ui.notify(f"❌ Growth failed: {msg}", type="warning")

    # Start background thread
    threading.Thread(
        target=threaded_growth,
        args=(uploaded_file_paths, mask_session_dir, zip_output_path, on_success, on_failure)
    ).start()
###### MAIN ########
def main_page():
    global mask_uploader, run_analysis_button
    with ui.row():
        with ui.column():
            ui.markdown("## 🌱 **Hydroponic System Analysis**")
        with ui.column():
            ui.table(rows=[
                {'INSTRUCTIONS': 'Upload images using ➕'},
                {'INSTRUCTIONS': 'Save using ☁️'},
                {'INSTRUCTIONS': 'Press button to run'},
                {'INSTRUCTIONS': 'Reload to restart!'},
            ])
    with ui.row():
        with ui.column():
            uploader =ui.upload(on_upload=save_uploaded_file, multiple=True)
        with ui.column():
            ui.label('CROP: Pick four points to crop all images (zip)')
            with ui.row():    
                ui.label('TIMELAPSE: Makes timelapse of images uploaded (.mov)')
            with ui.row():    
                ui.label('MASKS: Makes black and white versions of images (zip)')     
            with ui.row():    
                ui.label('GROWTH: Crop to single plant, upload masks of plants, makes chart (zip)')
    update_file_list_display()
    with ui.row():
        ui.button("Crop and Download ZIP", on_click=process_images)
        ui.button("Reset Points", on_click=reset_points)
    uploader.on('finish', update_file_list_display)
    ui.button("Create Timelapse", on_click=process_timelapse)
    with ui.row():
        ui.button("Make Masks", on_click=process_masking)
    with ui.row():
        ui.button("Run Growth Analysis", on_click=process_growth)
    # with ui.row():
    #     ui.button("BAD Run Growth Analysis", on_click=show_mask_uploader)
main_page()    
ui.run()