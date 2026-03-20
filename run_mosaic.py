#!/usr/bin/env python3
import argparse
import os
import sys

# Apple Silicon (MPS) において未対応の演算（nms等）が発生した場合に自動的にCPUにフォールバックさせるための環境変数を設定。
# これを設定しないとNotImplementedErrorでクラッシュする可能性があります。
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from typing import List, Tuple

import cv2
import numpy as np


def download_file(url: str, dst_path: str) -> None:
    import requests

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(dst_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def ensure_yolo_face_weights(weights_path: str) -> str:
    if os.path.exists(weights_path):
        return weights_path

    basename = os.path.basename(weights_path).lower()
    if "v8m" in basename or "yolov8m" in basename:
        url_candidates = [
            "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8m-face-lindevs.pt",
        ]
    elif "v8l" in basename or "yolov8l" in basename:
        url_candidates = [
            "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8l-face-lindevs.pt",
        ]
    elif "v8x" in basename or "yolov8x" in basename:
        url_candidates = [
            "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8x-face-lindevs.pt",
        ]
    elif "v8s" in basename or "yolov8s" in basename:
        url_candidates = [
            "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8s-face-lindevs.pt",
        ]
    else:
        url_candidates = [
            "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8n-face-lindevs.pt",
        ]

    last_error = None
    for url in url_candidates:
        try:
            print(f"Downloading YOLOv8 face model from: {url}")
            download_file(url, weights_path)
            return weights_path
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if os.path.exists(weights_path):
                os.remove(weights_path)

    raise RuntimeError(f"Failed to download YOLOv8 face weights: {last_error}")


def mosaic_region(frame: np.ndarray, bbox: Tuple[int, int, int, int], block_size: int) -> None:
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(frame.shape[1], x2)
    y2 = min(frame.shape[0], y2)

    if x2 <= x1 or y2 <= y1:
        return

    roi = frame[y1:y2, x1:x2]
    h, w = roi.shape[:2]
    if h < 2 or w < 2:
        return

    small = cv2.resize(roi, (max(1, w // block_size), max(1, h // block_size)), interpolation=cv2.INTER_LINEAR)
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    frame[y1:y2, x1:x2] = mosaic


def pick_device(user_device: str) -> str:
    if user_device:
        return user_device

    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:  # noqa: BLE001
        pass

    return "cpu"


def process_video(
    input_path: str,
    output_path: str,
    mosaic_block: int,
    yolo_weights: str,
    yolo_imgsz: int,
    yolo_conf: float,
    yolo_iou: float,
    device: str,
    progress_callback=None,
) -> None:
    from ultralytics import YOLO
    try:
        from moviepy import VideoFileClip, AudioFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip, AudioFileClip
    import tempfile
    import shutil

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 1  # Fallback to prevent division by zero

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Create a temporary file for the video without audio
    fd, temp_video_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    weights_path = ensure_yolo_face_weights(yolo_weights)
    yolo_model = YOLO(weights_path)

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        bboxes: List[Tuple[int, int, int, int]] = []

        results = yolo_model.predict(
            frame,
            imgsz=yolo_imgsz,
            conf=yolo_conf,
            iou=yolo_iou,
            device=device,
            verbose=False,
        )
        for box in results[0].boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = box.astype(int)
            bboxes.append((x1, y1, x2, y2))

        for bbox in bboxes:
            mosaic_region(frame, bbox, block_size=mosaic_block)

        writer.write(frame)

        if progress_callback is not None:
            # frame is BGR Numpy array, progress_callback expects it
            progress_callback(frame_count, total_frames, frame)

        if frame_count % 60 == 0:
            print(f"Processed {frame_count} frames...", flush=True)

    cap.release()
    writer.release()

    # Audio merging with moviepy
    print("Merging audio...", flush=True)
    original_clip = None
    processed_clip = None
    final_clip = None
    try:
        original_clip = VideoFileClip(input_path)
        if original_clip.audio is not None:
            processed_clip = VideoFileClip(temp_video_path)
            # moviepy v2.x uses with_audio(), v1.x uses set_audio()
            if hasattr(processed_clip, 'with_audio'):
                final_clip = processed_clip.with_audio(original_clip.audio)
            else:
                final_clip = processed_clip.set_audio(original_clip.audio)
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                logger=None, # Disable moviepy's verbose bar
                preset="fast"
            )
        else:
            # If no audio, just copy the temp file to the output path
            shutil.copyfile(temp_video_path, output_path)
    except Exception as e:
        print(f"Error during audio merge/copy: {e}")
        print("Saving video without audio as fallback.")
        # Close all clips before moving the file (Windows file lock)
        for clip in [final_clip, processed_clip, original_clip]:
            if clip is not None:
                try:
                    clip.close()
                except Exception:
                    pass
        # Fallback copy
        import time
        time.sleep(1) # Give Windows a moment to release handles
        try:
            shutil.copyfile(temp_video_path, output_path)
        except OSError as copy_err:
            print(f"Fallback copy failed: {copy_err}")
    finally:
        # Close all clips first to release file handles (important on Windows)
        for clip in [final_clip, processed_clip, original_clip]:
            if clip is not None:
                try:
                    clip.close()
                except Exception:
                    pass
        
        # Now safe to clean up temp file, with retries for Windows locks
        if os.path.exists(temp_video_path):
            import time
            for _ in range(5):
                try:
                    os.remove(temp_video_path)
                    break
                except OSError:
                    time.sleep(0.5)



def process_image(
    input_path: str,
    output_path: str,
    mosaic_block: int,
    yolo_weights: str,
    yolo_imgsz: int,
    yolo_conf: float,
    yolo_iou: float,
    device: str,
    progress_callback=None,
) -> None:
    from ultralytics import YOLO

    frame = cv2.imread(input_path)
    if frame is None:
        raise RuntimeError(f"Failed to read image: {input_path}")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    weights_path = ensure_yolo_face_weights(yolo_weights)
    yolo_model = YOLO(weights_path)

    bboxes: List[Tuple[int, int, int, int]] = []

    results = yolo_model.predict(
        frame,
        imgsz=yolo_imgsz,
        conf=yolo_conf,
        iou=yolo_iou,
        device=device,
        verbose=False,
    )
    for box in results[0].boxes.xyxy.cpu().numpy():
        x1, y1, x2, y2 = box.astype(int)
        bboxes.append((x1, y1, x2, y2))

    for bbox in bboxes:
        mosaic_region(frame, bbox, block_size=mosaic_block)

    if progress_callback is not None:
        progress_callback(1, 1, frame)

    cv2.imwrite(output_path, frame)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLOv8 face mosaic processor (YOLOv8m + imgsz=960).")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--mosaic", type=int, default=20, help="Mosaic block size (larger = stronger)")
    parser.add_argument("--yolo-weights", default="models/yolov8m-face.pt", help="YOLOv8 face weights path")
    parser.add_argument("--yolo-imgsz", type=int, default=960, help="YOLOv8 inference image size")
    parser.add_argument("--yolo-conf", type=float, default=0.25, help="YOLOv8 confidence threshold")
    parser.add_argument("--yolo-iou", type=float, default=0.45, help="YOLOv8 IoU threshold")
    parser.add_argument("--device", default="", help="Device override: cpu / mps / 0")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    device = pick_device(args.device)
    print(f"Using device: {device}")

    ext = os.path.splitext(args.input.lower())[1]
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

    if ext in image_exts:
        process_image(
            args.input,
            args.output,
            mosaic_block=args.mosaic,
            yolo_weights=args.yolo_weights,
            yolo_imgsz=args.yolo_imgsz,
            yolo_conf=args.yolo_conf,
            yolo_iou=args.yolo_iou,
            device=device,
        )
    else:
        process_video(
            args.input,
            args.output,
            mosaic_block=args.mosaic,
            yolo_weights=args.yolo_weights,
            yolo_imgsz=args.yolo_imgsz,
            yolo_conf=args.yolo_conf,
            yolo_iou=args.yolo_iou,
            device=device,
        )

    print("Done.")
