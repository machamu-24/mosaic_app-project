import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import cv2

# Add the current directory to sys.path so we can import run_mosaic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from run_mosaic import process_video, process_image, pick_device
except ImportError as e:
    print(f"Error importing run_mosaic: {e}")
    sys.exit(1)


class MosaicAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosaic App")
        self.root.geometry("500x320")
        self.root.resizable(False, False)

        # Variables
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.mosaic_block_var = tk.IntVar(value=20)
        self.status_var = tk.StringVar(value="Ready.")

        # Tracking variables for UI updates
        self.latest_progress = None
        self.is_processing = False

        self.create_widgets()

    def create_widgets(self):
        # Input Frame
        input_frame = tk.Frame(self.root, pady=10)
        input_frame.pack(fill=tk.X, padx=20)

        tk.Label(input_frame, text="Input File:").pack(anchor=tk.W)
        input_entry = tk.Entry(input_frame, textvariable=self.input_path_var, width=40)
        input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side=tk.LEFT, padx=5)

        # Output Frame
        output_frame = tk.Frame(self.root, pady=10)
        output_frame.pack(fill=tk.X, padx=20)

        tk.Label(output_frame, text="Output File:").pack(anchor=tk.W)
        output_entry = tk.Entry(output_frame, textvariable=self.output_path_var, width=40)
        output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.LEFT, padx=5)

        # Settings Frame
        settings_frame = tk.Frame(self.root, pady=10)
        settings_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(settings_frame, text="Mosaic Block Size (larger = stronger):").pack(side=tk.LEFT)
        tk.Spinbox(settings_frame, from_=5, to=100, textvariable=self.mosaic_block_var, width=5).pack(side=tk.LEFT, padx=5)

        # Run Button
        run_frame = tk.Frame(self.root, pady=10)
        run_frame.pack(fill=tk.X, padx=20)
        
        # In macOS Tkinter, setting a colored button background is hard without `tkmacosx`.
        # Using a clean ttk style with a large explicit text instead.
        style = ttk.Style()
        style.configure("Run.TButton", font=("Helvetica", 14, "bold"), padding=10)
        
        self.run_button = ttk.Button(run_frame, text="▶️ モザイク処理を実行", command=self.start_processing, style="Run.TButton")
        self.run_button.pack(fill=tk.X, ipady=5)

        # Status Bar
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar (Determinate)
        self.progress = ttk.Progressbar(self.root, mode='determinate', maximum=100)


    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=(
                ("Video/Image files", "*.mp4 *.mov *.avi *.jpg *.jpeg *.png *.webp"),
                ("All files", "*.*")
            )
        )
        if filename:
            self.input_path_var.set(filename)
            # Auto-generate output path
            base, ext = os.path.splitext(filename)
            self.output_path_var.set(f"{base}_masked{ext}")

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".mp4",
            filetypes=(
                ("MP4 files", "*.mp4"),
                ("MOV files", "*.mov"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            )
        )
        if filename:
            self.output_path_var.set(filename)

    def start_processing(self):
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        mosaic_block = self.mosaic_block_var.get()

        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid input file.")
            return
        if not output_path:
            messagebox.showerror("Error", "Please select an output file path.")
            return

        self.run_button.config(state=tk.DISABLED)
        self.status_var.set("Processing... Please wait.")
        self.progress.pack(fill=tk.X, padx=20, pady=5)
        self.progress["value"] = 0

        self.is_processing = True
        self.latest_progress = (0, 1)
        
        # Start UI polling
        self.poll_updates()

        # Run processing in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.run_process_thread, args=(input_path, output_path, mosaic_block))
        thread.start()

    def poll_updates(self):
        if not self.is_processing:
            return

        # Update progress bar
        if self.latest_progress:
            curr, total = self.latest_progress
            if total > 0:
                percent = (curr / total) * 100
                self.progress["value"] = percent
                self.status_var.set(f"Processing... {curr}/{total} frames ({percent:.1f}%)")
            
        # Schedule next poll
        self.root.after(100, self.poll_updates)

    def run_process_thread(self, input_path, output_path, mosaic_block):
        try:
            # Hardcoded standard parameters for simplicity as discussed
            yolo_weights = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "yolov8m-face.pt")
            yolo_imgsz = 960
            yolo_conf = 0.25
            yolo_iou = 0.45
            device = pick_device("") # Auto pick
            
            ext = os.path.splitext(input_path.lower())[1]
            image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

            # We removed StdoutRedirector because `root.after` called from standard 
            # output threads on macOS causes "main thread is not in main loop" errors.
            # Instead of capturing prints, our `poll_updates` directly reads `self.latest_progress`
            # and updates `self.status_var` smoothly.

            if ext in image_exts:
                process_image(
                    input_path, output_path, mosaic_block,
                    yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device,
                    progress_callback=self.progress_callback
                )
            else:
                process_video(
                    input_path, output_path, mosaic_block,
                    yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device,
                    progress_callback=self.progress_callback
                )

            self.root.after(0, self.processing_complete, True, f"Successfully saved to: {output_path}")

        except Exception as e:
            print(f"Error details: {e}")
            self.root.after(0, self.processing_complete, False, str(e))

    def progress_callback(self, curr, total, frame):
        self.latest_progress = (curr, total)
        # We ignore 'frame' now since the preview feature was removed for simplicity.

    def processing_complete(self, success, message):
        self.is_processing = False
        self.progress.pack_forget()
        self.run_button.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("Ready.")
            messagebox.showinfo("Success", message)
        else:
            self.status_var.set("Error during processing.")
            messagebox.showerror("Error", f"An error occurred:\n{message}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MosaicAppGUI(root)
    root.mainloop()
