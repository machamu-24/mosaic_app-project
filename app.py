import os
import tempfile
import sys
import importlib.util


def _bootstrap_import_paths() -> None:
    """Ensure local bundle paths are importable in both dev and PyInstaller runtime."""
    candidates = []
    try:
        candidates.append(sys._MEIPASS)  # type: ignore[attr-defined]
    except Exception:
        pass
    candidates.append(os.path.dirname(os.path.abspath(__file__)))

    for path in candidates:
        if path and path not in sys.path:
            sys.path.insert(0, path)

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def _load_core_modules():
    """Import core processing module, with a file-based fallback for packaged builds."""
    _bootstrap_import_paths()
    try:
        from run_mosaic import process_video, process_image, pick_device
        return process_video, process_image, pick_device
    except Exception as first_error:
        run_mosaic_path = resource_path("run_mosaic.py")
        if not os.path.exists(run_mosaic_path):
            raise first_error

        spec = importlib.util.spec_from_file_location("run_mosaic", run_mosaic_path)
        if spec is None or spec.loader is None:
            raise first_error

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules["run_mosaic"] = module
        return module.process_video, module.process_image, module.pick_device


def _run_self_test() -> int:
    process_video, process_image, pick_device = _load_core_modules()
    _ = (process_video, process_image, pick_device)

    import ultralytics  # noqa: F401
    import moviepy  # noqa: F401
    try:
        from moviepy import VideoFileClip  # noqa: F401
    except Exception:
        from moviepy.editor import VideoFileClip  # noqa: F401
    import imageio  # noqa: F401
    import imageio_ffmpeg

    model_path = resource_path(os.path.join("models", "yolov8m-face.pt"))
    if not os.path.exists(model_path):
        raise RuntimeError(f"Model file missing: {model_path}")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg_exe or not os.path.exists(ffmpeg_exe):
        raise RuntimeError("imageio-ffmpeg binary is missing in the bundle.")

    print("MOSAICAPP_SELF_TEST_OK")
    return 0


if os.environ.get("MOSAICAPP_SELF_TEST") == "1":
    try:
        raise SystemExit(_run_self_test())
    except Exception as exc:
        print(f"MOSAICAPP_SELF_TEST_FAIL: {exc}", file=sys.stderr)
        raise

import streamlit as st

try:
    process_video, process_image, pick_device = _load_core_modules()
except Exception as e:
    st.error(f"Error importing core app modules: {e}")
    st.stop()


def main():
    st.set_page_config(page_title="Mosaic App (Web)", page_icon="🕵️", layout="centered")

    st.title("Face Mosaic Application 🕵️")
    st.markdown("Upload a video or image to automatically detect faces and apply a mosaic effect.")

    # Sidebar settings
    st.sidebar.header("Settings")
    mosaic_block = st.sidebar.slider("Mosaic Strength", min_value=5, max_value=100, value=20, help="Larger means stronger mosaic.")
    
    # Advanced settings hidden by default since it's for non-engineers usually, but good for demo
    with st.sidebar.expander("Advanced Settings"):
        yolo_imgsz = st.number_input("Inference Size (imgsz)", min_value=320, max_value=1280, value=960, step=32)
        yolo_conf = st.slider("Confidence Threshold", 0.0, 1.0, 0.25, 0.05)
        yolo_iou = st.slider("IoU Threshold", 0.0, 1.0, 0.45, 0.05)
    
    # Use standard models path
    yolo_weights = resource_path(os.path.join("models", "yolov8m-face.pt"))
    device = pick_device("")

    # Main area
    uploaded_file = st.file_uploader("Choose a video or image file", type=["mp4", "mov", "avi", "jpg", "jpeg", "png", "webp"])

    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        is_image = file_ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"]

        if is_image:
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        else:
            st.video(uploaded_file, format="video/mp4")

        if st.button("Apply Mosaic", type="primary"):
            process_uploaded_file(uploaded_file, is_image, mosaic_block, yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device, file_ext)


def process_uploaded_file(uploaded_file, is_image, mosaic_block, yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device, file_ext):
    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_in:
        tmp_in.write(uploaded_file.read())
        input_path = tmp_in.name

    # Determine output path
    output_ext = file_ext if is_image else ".mp4" # Force mp4 for videos for better browser compatibility
    fd, output_path = tempfile.mkstemp(suffix=output_ext)
    os.close(fd)

    try:
        st.write("Processing... Please wait (this may take a while for long videos).")
        progress_bar = st.progress(0, text="Initializing processing...")

        def update_progress(curr, total, frame):
            # Streamlit progress bar accepts values 0-100 (or float 0.0-1.0)
            if total > 0:
                percent_float = min(1.0, max(0.0, curr / total))
                percent_int = int(percent_float * 100)
                text_msg = f"Processing... {curr}/{total} frames ({percent_int}%)"
                progress_bar.progress(percent_float, text=text_msg)

        if is_image:
            process_image(
                input_path, output_path, mosaic_block,
                yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device,
                progress_callback=update_progress
            )
            progress_bar.empty() # Remove progress bar when done
            st.success("Image processing complete!")
            st.image(output_path, caption="Masked Image", use_container_width=True)
            
            with open(output_path, "rb") as file:
                st.download_button(
                    label="Download Masked Image",
                    data=file,
                    file_name=f"masked_{uploaded_file.name}",
                    mime=f"image/{file_ext[1:]}"
                )

        else:
            process_video(
                input_path, output_path, mosaic_block,
                yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device,
                progress_callback=update_progress
            )
            progress_bar.empty() # Remove progress bar when done
            st.success("Video processing complete!")
            
            # Attempt to show video in browser
            try:
                with open(output_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                st.video(video_bytes)
            except Exception as e:
                st.warning("Could not preview video in browser. Please download it.")
            
            with open(output_path, "rb") as file:
                st.download_button(
                    label="Download Masked Video",
                    data=file,
                    file_name=f"masked_{os.path.splitext(uploaded_file.name)[0]}.mp4",
                    mime="video/mp4"
                )
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
    finally:
        # Cleanup temp files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    main()
