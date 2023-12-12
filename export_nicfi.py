import ee
import subprocess
import argparse
def _init(project):
    try:
        ee.Initialize(project=project)
    except:
        raise Exception

def export_nicfi(cloud_project,nicfi_region, aoi, start, end):
    nicfi_assets = {'americas':'projects/planet-nicfi/assets/basemaps/americas',
                    'africa':'projects/planet-nicfi/assets/basemaps/americas',
                    'asia':'projects/planet-nicfi/assets/basemaps/asia'}
    valid_regions = ['americas','africa','asia']
    
    # catch Value errors
    nicfi_region = nicfi_region.lower()
    if nicfi_region not in valid_regions:
        raise ValueError(f'nicfi_region must be one of {valid_regions}: got {nicfi_region}')
    
    if isinstance(aoi,ee.FeatureCollection):
        aoi=aoi.geometry()
    
    collection_asset = nicfi_assets[nicfi_region]
    collection = ee.FeatureCollection(collection_asset).filterDate(start,end)
    n_images = collection.size().getInfo()
    image_list = collection.toList(n_images)
    collection = f'projects/{cloud_project}/assets/nicfi'
    make_ee_container(collection,'collection')
    
    for i in list(range(1,n_images)):
        img = ee.Image(ee.List(image_list).get(i))
        id = img.get('system:index').getInfo()
        desc = f'exportNICFI_image{i}'
        asset_id = f'{collection}/{id}'
        export_img_to_asset(image=img,
                            description=desc,
                            assetId=asset_id,
                            region=aoi,
                            scale=3,
                            maxPixels=1e12)
        # break

def make_ee_container(path, type):
    """Makes a GEE asset folder or collection (type) at the specified asset path (path)"""
    if check_exists(path):
        cmd = f"earthengine create {type} {path}"
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = proc.communicate()

def export_img_to_asset(image,
    description="myExportImageTask",
    assetId=None,
    pyramidingPolicy=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    **kwargs):
    """Creates a task to export an EE Image to an EE Asset.

    Args:
        image: The image to be exported.
        description: Human-readable name of the task.
        assetId: The destination asset ID.
        pyramidingPolicy: The pyramiding policy to apply to each band in the
            image, a dictionary keyed by band name. Values must be
            one of: "mean", "sample", "min", "max", or "mode".
            Defaults to "mean". A special key, ".default", may be used to
            change the default for all bands.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image assset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.
    """

    if isinstance(image, ee.Image) or isinstance(image, ee.image.Image):
        pass
    else:
        raise ValueError("Input image must be an instance of ee.Image")

    if isinstance(assetId, str):
        if assetId.startswith("users/") or assetId.startswith("projects/"):
            pass
        else:
            assert check_exists(assetId) == 0, f"{assetId} not a valid asset path"
            # assetId = f"{ee_user_id()}/{assetId}"

    task = ee.batch.Export.image.toAsset(
        image,
        description,
        assetId,
        pyramidingPolicy,
        dimensions,
        region,
        scale,
        crs,
        crsTransform,
        maxPixels,
        **kwargs,
    )
    task.start()
    print(f"Export Started (Asset): {assetId}")

def check_exists(ee_path:str):
    try:
        ee.data.getAsset(ee_path)
        return 0 # does exist returns 0/False
    except ee.ee_exception.EEException:
        return 1 # doesn't exist returns 1/True

def main():
    # initalize new cli parser
    parser = argparse.ArgumentParser(
        description="CLI process for exporting Planet NICFI analytical basemaps for your AOI and time period."
    )

    parser.add_argument(
        "-project",
        type=str,
        help="GEE cloud project to work in and save basemaps in",
    )

    parser.add_argument(
        "-nicfi_region",
        type=str,
        help="NICFI regional product, one of: americas, africa, asia",
    )

    parser.add_argument(
        "-aoi",
        type=str, 
        help="GEE asset string for your AOI (example: projects/sig-ee-cloud/assets/SeshekeSmall)"
    )

    parser.add_argument(
        "-start",
        type=str,
        help="start date, YYYYMMdd format",
    )

    parser.add_argument(
        "-end",
        type=str,
        help="end date, YYYYMMdd format",
    )


    args = parser.parse_args()
    
    cp = args.project
    # initialize EE library with cloud project
    _init(cp)

    nicfi_r = args.nicfi_region
    aoi = ee.FeatureCollection(args.aoi)
    start=args.start
    end=args.end
    
    export_nicfi(cloud_project=cp,
                 nicfi_region=nicfi_r,
                 aoi=aoi,
                 start=start,
                 end=end)

main()