#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# Copyright (c) 2017-2018 Joe Del Rocco
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ====================================================================
# @author: Joe Del Rocco
# @since: 10/18/2017
# @summary: Script to test reading raw images.
# ====================================================================
import sys
import argparse
# rawpy
#import rawpy
#import imageio
# rawkit
# import numpy as np
# from PIL import Image
# from rawkit.raw import Raw
# wand
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
    #     rgb = raw.postprocess(use_auto_wb=False, use_camera_wb=False, no_auto_bright=True, exp_shift=2.0)
    #     #demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD, no_auto_bright=False, use_camera_wb=True, output_bps=16) #gamma=(1, 1)
    #     imageio.imsave(args.filepath + '.tiff', rgb)

    # rawkit (libraw)
    # raw_image = Raw(args.filepath)
    # buffered_image = np.array(raw_image.to_buffer())
    # image = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
    # image.save(args.filepath + '.png', format='png')


if __name__ == '__main__':
    main()
