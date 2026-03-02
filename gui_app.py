import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

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
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        # Variables
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.mosaic_block_var = tk.IntVar(value=20)
        self.status_var = tk.StringVar(value="Ready.")

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
        run_frame = tk.Frame(self.root, pady=20)
        run_frame.pack(fill=tk.X, padx=20)
        self.run_button = tk.Button(run_frame, text="Run Processing", command=self.start_processing, bg="green", fg="white", font=("Helvetica", 12, "bold"))
        self.run_button.pack(fill=tk.X)

        # Status Bar
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar (Indeterminate)
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')


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
        self.progress.start()

        # Run processing in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.run_process_thread, args=(input_path, output_path, mosaic_block))
        thread.start()

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

            # Redirect stdout to capture "Processed X frames..."
            old_stdout = sys.stdout
            class StdoutRedirector:
                def __init__(self, main_gui):
                    self.main_gui = main_gui
                def write(self, text):
                    if "Processed" in text or "Merging audio" in text:
                        # Schedule standard update on main thread
                        self.main_gui.root.after(0, self.main_gui.status_var.set, text.strip())
                def flush(self):
                    pass
            
            sys.stdout = StdoutRedirector(self)

            if ext in image_exts:
                process_image(
                    input_path, output_path, mosaic_block,
                    yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device
                )
            else:
                process_video(
                    input_path, output_path, mosaic_block,
                    yolo_weights, yolo_imgsz, yolo_conf, yolo_iou, device
                )

            sys.stdout = old_stdout # Restore stdout
            
            self.root.after(0, self.processing_complete, True, f"Successfully saved to: {output_path}")

        except Exception as e:
            sys.stdout = old_stdout # Restore stdout on error
            print(f"Error details: {e}")
            self.root.after(0, self.processing_complete, False, str(e))

    def processing_complete(self, success, message):
        self.progress.stop()
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
