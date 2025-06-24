import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
import os

tiff = "C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00.tif"

tiff = os.path.expanduser(tiff)

# KSA bounding box in EPSG:3857 (Web Mercator)
ksa_bounds = [3540000, 1560000, 6330000, 4090000]

with rasterio.open(tiff) as src:
    bounds = transform_bounds("EPSG:4326", src.crs, *ksa_bounds)
    window = from_bounds(*bounds, src.transform)
    data = src.read(window=window)
    profile = src.profile
    profile.update({
        "height": data.shape[1],
        "width": data.shape[2],
        "transform": src.window_transform(window)
    })
with rasterio.open("C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00.tif_cropped.tif", "w", **profile) as dst:
    dst.write(data)