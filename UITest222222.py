# Required imports
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import rasterio
import cv2
from rasterio.features import shapes
import geopandas as gpd
import os

# Initialize main GUI window
root = tk.Tk()
root.title("Dust Detection App")
root.geometry("900x650")

# ----------- Scrollable Frame Setup -----------
# Allows vertical scrolling if many images are loaded
container = tk.Frame(root)
container.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(container)
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

canvas_widgets = []  # stores displayed image widgets

# ----------- Progress Bar Setup -----------
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=400)
progress_bar.pack(pady=5)

progress_label = tk.Label(root, text="")  # text under progress bar
progress_label.pack()

# ----------- Utility: Clear all displayed figures -----------
def clear_all_plots():
    for widget in canvas_widgets:
        widget.get_tk_widget().destroy()
    canvas_widgets.clear()

# ----------- Core Function: Process a single TIFF file -----------
def process_tiff(tiff_path):
    try:
        # Read the RGB bands from TIFF
        with rasterio.open(tiff_path) as src:
            rgb = src.read([1, 2, 3])
            transform = src.transform
            crs = src.crs

        # Convert from (bands, height, width) to (height, width, bands)
        img = np.transpose(rgb, (1, 2, 0)).astype(np.uint8)

        # Convert image to BGR then HSV (OpenCV uses BGR by default)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Define HSV range for detecting dust (pink/magenta)
        lower_hsv = np.array([140, 40, 40])
        upper_hsv = np.array([170, 255, 255])

        # Create a binary mask for the dust regions
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        binary_mask = (mask > 0).astype(np.uint8)

        # Extract polygon shapes from the binary mask
        results = (
            {"properties": {"value": v}, "geometry": s}
            for s, v in shapes(binary_mask, mask=binary_mask, transform=transform)
            if v == 1
        )

        # Save polygons as GeoJSON
        gdf = gpd.GeoDataFrame.from_features(results, crs=crs).to_crs("EPSG:4326")
        geojson_path = tiff_path.replace('.tif', '_dust.geojson').replace('.tiff', '_dust.geojson')
        gdf.to_file(geojson_path, driver='GeoJSON')

        # Plot original image and dust mask side by side
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        axes[0].imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        axes[0].set_title(f"Original: {os.path.basename(tiff_path)}")
        axes[0].axis('off')

        axes[1].imshow(binary_mask, cmap='gray')
        axes[1].set_title("Detected Dust")
        axes[1].axis('off')

        fig.tight_layout()
        return fig, geojson_path

    except Exception as e:
        messagebox.showerror("Error", f"Error processing {tiff_path}:\n{e}")
        return None, None

# ----------- UI Handler: Select and process a single file -----------
def select_file():
    path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif *.tiff")])
    if not path:
        return
    clear_all_plots()
    fig, geojson_path = process_tiff(path)
    if fig:
        fig_canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
        fig_canvas.draw()
        fig_canvas.get_tk_widget().pack(pady=10)
        canvas_widgets.append(fig_canvas)
        messagebox.showinfo("Success", f"GeoJSON saved at:\n{geojson_path}")

# ----------- UI Handler: Select folder and batch process all TIFF files -----------
def select_folder():
    folder_path = filedialog.askdirectory()
    if not folder_path:
        return

    # List TIFF files in the folder
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.tif', '.tiff'))]
    if not files:
        messagebox.showwarning("No files", "No TIFF files found in the selected folder.")
        return

    clear_all_plots()

    # Setup progress bar
    total = len(files)
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    progress_label.config(text="Processing...")

    success_count = 0

    for idx, f in enumerate(sorted(files), 1):
        full_path = os.path.join(folder_path, f)
        fig, geojson_path = process_tiff(full_path)

        # Show plot and update progress
        if fig:
            success_count += 1
            fig_canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
            fig_canvas.draw()
            fig_canvas.get_tk_widget().pack(pady=10)
            canvas_widgets.append(fig_canvas)

        # Update progress bar and label
        progress_bar["value"] = idx
        progress_label.config(text=f"Processed {idx}/{total}")
        root.update_idletasks()

    # Final status message
    if success_count > 0:
        messagebox.showinfo("Done", f"Processed {success_count} files.\nGeoJSONs saved next to images.")
    else:
        messagebox.showwarning("Warning", "No files were successfully processed.")

    progress_label.config(text="Done.")

# ----------- UI Buttons and Labels -----------
tk.Label(root, text="Dust Detection from Satellite TIFF Images", font=("Arial", 14)).pack(pady=10)
tk.Button(root, text="📄 Select Single TIFF File", command=select_file).pack(pady=5)
tk.Button(root, text="📁 Select Folder with TIFF Files", command=select_folder).pack(pady=5)

# Run the GUI main loop
root.mainloop()
