import os
from math import floor

import geopandas as gpd
from osgeo import gdal
from osgeo_utils import gdal_calc


def points_along_line(geom, space):
    ln = geom.length
    points = [geom.interpolate(distance) for distance in range(0, ln, space)]
    return points


def get_point_elevation(points, raster):
    # thank you https://gis.stackexchange.com/a/46898
    src_ds = gdal.Open(raster)
    gt_forward = src_ds.GetGeoTransform()
    gt_reverse = gdal.InvGeoTransform(gt_forward)
    rb = src_ds.GetRasterBand(1)
    elevations = []
    for point in points:
        mx, my = point.x, point.y
        px, py = gdal.ApplyGeoTransform(gt_reverse, mx, my)
        px, py = floor(px), floor(py)
        intval = rb.ReadAsArray(px, py, 1, 1)
        elevations.append(intval[0][0])
    src_ds = None
    rb = None
    return elevations


def idw(input_shapefile, output_tif, bounds, width, height):
    # thank you https://www.youtube.com/watch?v=FSnJ2VXNV3c
    gdal.Grid(
        output_tif,
        input_shapefile,
        zfield="elevation",
        format="GTiff",
        algorithm="invdist:power=2.0",
        outputBounds=bounds,
        width=width,
        height=height,
    )


def raster_calc(input_raster1, input_raster2, output_raster):
    gdal_calc.Calc(
        A=input_raster1,
        B=input_raster2,
        outfile=output_raster,
        calc="A-B",
    )


def main():
    # INPUTS: river centerline and elevation raster and the space b/w points
    CENTERLINE = "centerline.shp"
    RASTER = "merge_clip.tif"
    SPACE = 70

    # auto created by script
    OUTPUT = "centerline_points.shp"
    ELEV = "points_elevation.shp"
    IDW_OUTPUT = "idw_interpolation.tif"

    # final output
    DIFFERENCE_OUTPUT = "difference.tif"

    # Load the data
    gdf = gpd.read_file(CENTERLINE)
    crs = gdf.crs
    geom = gdf.geometry.iloc[0]

    # Generate points along the line
    points = points_along_line(geom, SPACE)

    # Create a GeoDataFrame
    gdf_points = gpd.GeoDataFrame(geometry=points, crs=crs)

    # Get elevation data for each point
    elevations = get_point_elevation(points, RASTER)
    gdf_points["elevation"] = elevations

    # Save the new shapefile with elevation data
    gdf_points.to_file(ELEV, format="ESRI Shapefile", index=False)

    # Perform IDW interpolation
    src_ds = gdal.Open(RASTER)
    gt_forward = src_ds.GetGeoTransform()
    ulx, uly = gt_forward[0], gt_forward[3]
    res = gt_forward[1]
    xSize, ySize = src_ds.RasterXSize, src_ds.RasterYSize
    lrx, lry = ulx + xSize * res, uly - ySize * res
    bounds = [ulx, uly, lrx, lry]
    idw(ELEV, IDW_OUTPUT, bounds, xSize, ySize)

    # Calculate raster difference
    raster_calc(RASTER, IDW_OUTPUT, DIFFERENCE_OUTPUT)

    # Clean up intermediate files
    for file in [OUTPUT, ELEV, IDW_OUTPUT]:
        try:
            os.remove(file)
        except OSError:
            pass


if __name__ == "__main__":
    main()
