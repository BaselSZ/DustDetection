FROM python:3.11
RUN apt-get update && apt-get install -y \
    python3-tk \
    libgl1 \
    libgdal-dev
WORKDIR /app
COPY . /app
RUN pip install numpy matplotlib rasterio opencv-python shapely geopandas
CMD ["python3", "DustService.py"]