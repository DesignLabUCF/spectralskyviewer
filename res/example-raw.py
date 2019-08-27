#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 10/18/2017
# @summary: Script to test reading raw images.
# ====================================================================
import sys
import argparse
from PIL import Image as Img
import imageio
import numpy as np
# rawpy
import rawpy
# # rawkit
# from rawkit.raw import Raw
# # wand
# from wand.image import Image
# from wand.display import display


def main():
    # handle command line args
    parser = argparse.ArgumentParser(description='Script to test working with a raw image file.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_help = True
    parser.add_argument('filepath', help='a raw image file')
    args = parser.parse_args()

    # filepath required as parameter
    if (not args.filepath):
        print("Error: no filepath specified.")
        sys.exit(2)

    # wand (imagemagick)
    # #exif = {}
    # with Image(filename=args.filepath) as image:
    #     print(image.type)
    #     print(image.mimetype)
    #     print(image.format)
    #     print(image.size)
    #     print(image.colorspace)
    #     print(image.depth)
    #     print(image.resolution)
    #     print(image.units)
    #     #exif.update((k[5:], v) for k, v in image.metadata.items())
    #     #print(exif)
    #     with image.convert('png') as converted:
    #         converted.save(filename=args.filepath+'.tiff')

    # rawpy (libraw, dcraw)
    # with rawpy.imread(args.filepath) as raw:
    #     #print(raw.raw_type)
    #     rgb = raw.postprocess()
    #     #rgb = raw.postprocess(use_auto_wb=False, use_camera_wb=False, no_auto_bright=True, exp_shift=2.0)
    #     #demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD, no_auto_bright=False, use_camera_wb=True, output_bps=16) #gamma=(1, 1)
    #     imageio.imsave(args.filepath + '.tiff', rgb)

    # rawpy (libraw, dcraw)
    raw = rawpy.imread(args.filepath)
    #rgb = raw.postprocess(use_auto_wb=True)
    # rgb = raw.postprocess(use_camera_wb=True)
    #rgb = raw.postprocess(no_auto_bright=True, user_wb=raw.daylight_whitebalance) #POST1 # gamma=(1, 1), output_bps=8
    #rgb = raw.postprocess(no_auto_bright=True, user_wb=raw.camera_whitebalance)  # POST2
    #rgb = raw.postprocess(no_auto_bright=True, use_camera_wb=False, user_wb=[1.0, 1.0, 1.0, 1.0], bright=1.0, gamma=(1, 1), output_bps=8)  # POST3
    rgb = raw.postprocess(no_auto_bright=True, user_wb=raw.camera_whitebalance, gamma=(1, 1), output_bps=8)  # POST4
    #Img.fromarray(rgb).save(args.filepath + '.tiff')
    #save(args.filepath + ".POST.tiff", rgb)
    imageio.imsave(args.filepath + ".POST.tiff", rgb)
    raw.close()

    # rawkit (libraw)
    # raw_image = Raw(args.filepath)
    # buffered_image = np.array(raw_image.to_buffer())
    # image = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
    # image.save(args.filepath + '.png', format='png')


if __name__ == '__main__':
    main()
