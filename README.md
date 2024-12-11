# rem-maker

Download data from [USGS](https://apps.nationalmap.gov/downloader/#/)

Merge TIFs and clip to where relevant

```
gdal_merge.py -o merge.tif -co COMPRESS=LZW -co PREDICTOR=2 input1.tif input2.tif input3.tif
gdalwarp -cutline clipper.shp -crop_to_cutline -co COMPRESS=LZW -co PREDICTOR=2 merge.tif clipped_output.tif
```

Draw the river centerline

Run process.py

Example from the Mississippi Oxbow SNA (Science and Natural Area)
![image](https://github.com/user-attachments/assets/d4b93c9f-526b-45ef-b3c0-49d08fd469ab)
