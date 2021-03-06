#!/usr/bin/env python3
# A 1080p display has 1920 pixels wide by 1080 high
# Most mosaic builders walk through each pixel of the target image and
# determine which tile image best fits. Reverse_mosaic does the opposite. It walks
# through each tile image and determines the best fitting location in the target image.

# Because this program was built to be run without any intervention, there are some hard
# coded things like the target and source directories. Sorry.

import os
import sys
import scipy
import numpy as np
import math
import cv2
import re
import time
import collections
from collections import defaultdict
import datetime
import argparse

HI_RES_MULT = 1
tile_size = 50
MAXREPEAT = 500
THRESHOLD = 40
SATURATION = 10
mosaic = defaultdict(list)  # {tile_file_name: [x-coord, y-coord],[x-coord, y-coord]}
ENLARGEMENT = 2 # the mosaic image will be this many times wider and taller than the original
day_of_year = str(datetime.datetime.now().timetuple().tm_yday)
tiles_path = os.path.join("/home/pi/Pictures/", day_of_year)
target_file = os.path.join(tiles_path, 'target.jpg')


def show(img):
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

class Mosaic:
    def __init__(self, target):
        """
        Initialize an empty mosaic with information about the target image.
        """
        self.populated_coords = []
        self.path = os.path.join(os.path.dirname(target.path), 'mosaic-'+day_of_year+'.jpg')

        # tile_data stores tile path and best fitting coords {tile_path:[[x,y],[x,y]]}
        self.tile_data = defaultdict(list)
        self.tile_repeat = MAXREPEAT
        self.tile_size = tile_size
        self.logfile = os.path.join(os.path.dirname(target.path), 'tile_placement.log')
        self.target_img = target.img
        self.target = target
        self.hsv = defaultdict(list) # {"xcoord,ycoord":[blue,green,red]}
        self.tiles = [] # list of all tile filenames in the mosiac
        self.ntiles = lambda x:len(self.tiles) #

        self.empty_coords = []
        for row in target.rows:
            for col in target.cols:
                self.empty_coords.append([row,col])
        self.n_empty_coords = len(self.empty_coords)

        self.read_log()


    def add_tile(self, tile):
        """
        Add a single image to the mosaic.
        """
        if self.n_empty_coords == 0:
            print("no more room, mosaic is done.")
            return

        if self.check_tile(tile) != "skip":
            self.tiles.append(tile.name)
            print("number of tiles in mosaic = {}".format(self.ntiles))
            self.find_best_fit(tile)
            self.write_log()
            self.save(tile)

    def check_tile(self, tile):
        if tile.path in self.tile_data:
            print("{} is already in log file. Skipping.".format(tile.name))
            return "skip"
        if 'mosaic' in tile.name or 'target' in tile.name:
            print("skipping " + tile.name)
            return "skip"

    def calc_diff(self, target_img, tile):
        target_avg_h, target_avg_s, target_avg_v, t = cv2.mean(target_img)
        tile_avg_h, tile_avg_s, tile_avg_v, tile_avg_t = cv2.mean(tile.img_hsv)

        # .1 is to avoid huge diffs when target tile is black
        target_avg_h = max(target_avg_h, 0.1)
        target_avg_s = max(target_avg_s, 0.1)
        target_avg_v = max(target_avg_v, 0.1)

        diff = math.sqrt((target_avg_h - tile_avg_h)**2 +
                         (target_avg_s - tile_avg_s)**2 +
                         (target_avg_v - tile_avg_v)**2)
        return diff


    def find_best_fit(self, tile):
        """
        Loop through all pixels of the target image.
        Find best N coordinates.
        Save those coords in self.tile_data
        """
        diff_dict = {}

        for coords in self.empty_coords:
            target_tile = self.get_tile(self.target.img_hsv, coords)
            diff = self.calc_diff(target_tile, tile)
            diff_dict[diff] = coords


        # sort coords dictionary and keep best tile_repeat tiles
        best_coords = collections.OrderedDict(sorted(diff_dict.items()))
        count = 0
        for diff, coords in best_coords.items():
            # print(self.hsv)
            # time.sleep(10)
            # show(tile.img)
            # show(target_tile)
            # print(tile.name, diff, coords)

            if float(diff) > THRESHOLD:
                if count == 0:
                    print(tile.name)
                    print(coords)
                    print("difference: {} is greater than threshold".format(diff))
                    print("tweak image and try again")

                    # show(tile.img)
                    # time.sleep(3)
                    # new_h = math.fabs(target_avg_h - tile.avg_h) / 2
                    # new_s = math.fabs(target_avg_s - tile.avg_s) / 2
                    # new_v = math.fabs(target_avg_v - tile.avg_v) / 2
                    # self.tile_data[tile.path].append(coords)
                    # self.populated_coords.append(coords)
                    # self.empty_coords.remove(coords)
                    # self.hsv[str(coords[0])+','+str(coords[1])] = [new_h,new_s,new_v]


                    print("Best diff was {} at {}".format(diff, coords))

                    target_tile = self.get_tile(self.target.img_hsv, coords)
                    targ_h, targ_s, targ_v, t = cv2.mean(target_tile)
                    h,s,v = cv2.split(tile.img_hsv)
                    # print(targ_h, targ_s, targ_v)
                    # print(tile.avg_h, tile.avg_s, tile.avg_v)

                    # s.fill(targ_s)

                    # start by tweaking saturation, has least impact on image recognition
                    new_s = np.array(s, copy=True)
                    # new_s.fill(targ_s)
                    for i,rows in enumerate(s):
                        for j,val in enumerate(rows):
                            avg = (targ_s - val) / 2
                            new_s[i][j] = val + avg

                    # if avg_s diff is less than 10, start tweaking hue
                    print("avg s diff")
                    print(math.fabs(np.mean(targ_s - s)))
                    new_h = np.array(h, copy=True)
                    if math.fabs(np.mean(targ_s - s)) < 10:
                        print("tweaking hue")
                        # new_h.fill(targ_h)
                        for i,rows in enumerate(h):
                            for j,val in enumerate(rows):
                                avg = (targ_h - val) / 2
                                new_h[i][j] = val + avg

                    print("avg h diff")
                    print(math.fabs(np.mean(targ_h - h)))
                    new_v = np.array(v, copy=True)
                    if math.fabs(np.mean(targ_h - h)) < 10:
                        print("tweaking value")
                        for i,rows in enumerate(v):
                            for j,val in enumerate(rows):
                                avg = (targ_v - val) / 2
                                new_v[i][j] = val + avg

                    tile.img_hsv = cv2.merge([new_h,new_s,new_v])
                    tile.img = cv2.cvtColor(tile.img_hsv, cv2.COLOR_HSV2BGR)

                    print("old diff = {}, new diff = {}".format(diff, self.calc_diff(target_tile, tile)))
                    self.find_best_fit(tile) # everyone deserves match, try again with new hsv
                    return

                print("this tile fit {} locations".format(count))
                break
            else:
                print("fitting {} at target of {}".format(tile.name, coords))
                print("tile hsv = {},{},{}".format(tile.avg_h, tile.avg_s, tile.avg_v))
                print("diff = {}".format(diff))

                tile.best_coords.append(coords)
                # self.tile_data[tile.path].append(coords)
                data = [coords[0], coords[1],tile.avg_h, tile.avg_s, tile.avg_v]
                print(data)
                self.tile_data[tile.path].append(data)
                self.populated_coords.append(coords)
                self.empty_coords.remove(coords)
                self.hsv[str(coords[0])+','+str(coords[1])] = [tile.avg_h,tile.avg_s,tile.avg_v]

            if count >= self.tile_repeat:
                print("this tile fit {} locations".format(count))
                break
            count+=1

    def read_log(self):
        """
        Build mosaic dictionary from log file.
        Generate empty_coords list
        """
        if not os.path.isfile(self.logfile):
            print("there is no log file")
            with open(self.logfile, "w") as f:
                f.writelines("")

        with open(self.logfile, 'r') as f:
            lines = f.readlines()
            if len(lines) < 1:
                print("log file is empty")
                return
            for line in lines:
                line = line.strip()
                line = re.sub(r"\[|\]", "", line)
                filename, *coords = line.split(',')
                if len(coords) > 2:
                    for row, col, h, s, v in zip(coords[0::5], coords[1::5],
                                                 coords[2::5], coords[3::5], coords[4::5]):
                        self.tile_data[filename].append([int(row),int(col),
                                                         float(h),float(s), float(v)])
                else:
                    self.tile_data[filename].append([int(coords[0]), int(coords[1]),
                                                     float(coords[2]), float(coords[3]),
                                                     float(coord[4])])


    def write_log(self):
        """
        Overwrite log file with current mosaic dictionary
        """
        with open(self.logfile, 'w') as f:
            for filename, coords in self.tile_data.items():
                line = filename
                for coord in coords:
                    line += "," + str(coord)
                line += "\n"
                f.writelines(line)

    def get_tile(self, img, coords):
        """
        Pass in the x and y starting coordinates
        return the opencv image containing all pixels in that range
        """
        start_x, start_y = coords
        return img[start_x:start_x + tile_size, start_y:start_y + tile_size]
        # return img[start_y:start_y + tile_size, start_x:start_x + tile_size]


    def save(self, tile):
        """
        Build mosaic image from self.tile_data. Allows for partial build.
        Intended for 1080p display.
        """
        # if partial mosaic exists
        if os.path.isfile(self.path):
            mosaic_img = cv2.imread(self.path)
        else:
            mosaic_img = np.zeros((self.target_img.shape), np.uint8)

        # Define mask
        mask = np.zeros(mosaic_img.shape, dtype=np.bool)
        mask[0:tile_size, 0:tile_size] = True

        best_coords = self.tile_data[tile.path]

        for coords in best_coords:
            row,col,*hsv = coords

            mosaic_img[row:row+tile_size,
                col:col+tile_size] = tile.img[0:tile_size, 0:tile_size]

        cv2.imwrite(self.path, mosaic_img)


    def save_hi_res(self, target):
        """
        Build high resolution version of the mosaic.
        tile_size x HI_RES
        """
        pass

    def save_hi_res_old(self, target):
        """
        Build high resolution version of the mosaic.
        Meant to be run after all images have been collected, not
        gradually like the low-res version.
        tile_size x HI_RES

        logfile has already been read into memory
        walk through tile_data and build larger mosaic, don't try to recreate the best fits.
        """
        rows = self.target_img.shape[0] * HI_RES
        cols = self.target_img.shape[1] * HI_RES
        mosaic_img = np.zeros((rows,cols,3), np.uint8)

        # Define mask
        mask = np.zeros(mosaic_img.shape, dtype=np.bool)
        mask[0:tile_size*HI_RES, 0:tile_size* HI_RES] = True

        for tilename, best_fits in self.tile_data.items():
            for data in best_fits:
                row,col,h,s,v = data
                startrow = HI_RES * row
                startcol = HI_RES * col
                tile = Tile(tilename)


                tile.img_hi_hsv = cv2.merge([h,s,v])
                tile.img_hi = cv2.cvtColor(tile.img_hi_hsv, cv2.COLOR_HSV2BGR)

                # print(tilename)
                # print("target rows={} cols={}".format(rows,cols))
                # print("tile orig position row={}, col={}".format(row,col))
                # print("tile hires position row={}, col={}".format(startrow,startcol))
                # print(tile_size, HI_RES)

                mosaic_img[startrow:startrow + (tile_size * HI_RES),
                           startcol:startcol + (tile_size * HI_RES)] = tile.img_hi[0:tile_size * HI_RES,
                                                                      0:tile_size * HI_RES]

        cv2.imwrite(self.path+"-hi-res", mosaic_img)


class Target:
    def __init__(self, path):
        self.path = path
        target_img = cv2.imread(path)
        height, width = target_img.shape[:2]
        w_diff = (width % tile_size)/2
        h_diff = (height % tile_size)/2

        # if necesary, crop the image slightly so we use a whole number of tiles horizontally and vertically
        if w_diff or h_diff:
            target_img = target_img[0:int(height-2*h_diff), 0:int(width-2*w_diff)]
            height, width = target_img.shape[:2]

        self.img = cv2.resize(target_img,
                                     (int(width*ENLARGEMENT),
                                      int(height*ENLARGEMENT)))
        # self.img_hi_res = cv2.resize(target_img, (width*ENLARGEMENT*HI_RES,
        #                              height * ENLARGEMENT * HI_RES))

        self.img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        height, width = self.img.shape[:2]
        self.xpx, self.ypx = width, height
        self.num_y_tiles = int(self.ypx / tile_size)
        self.num_x_tiles = int(self.xpx / tile_size)

        self.rows = []
        self.cols = []
        for col in range(0, width, tile_size):
            self.cols.append(col)
        for row in range(0, height, tile_size):
            self.rows.append(row)

        self.check_resolution()
        # self.desaturate()


    def desaturate(self):
        self.avg_h, self.avg_s, self.avg_v, t = cv2.mean(self.img_hsv)
        h, s, v = cv2.split(self.img_hsv)
        new_s = s - SATURATION
        new_s.fill(SATURATION)
        self.img_hsv = cv2.merge([h, new_s, v])
        self.img = cv2.cvtColor(self.img_hsv, cv2.COLOR_HSV2BGR)


    def check_resolution(self):
        print("Image is {} px wide by {} px tall".format(self.xpx, self.ypx))
        if self.xpx < 1080:
            print("x resolution of {} is too low".format(self.xpx))
        if self.ypx < 720:
            print("y resolution of {} is too low".format(self.ypx))


class Tile:
    def __init__(self, tile_path):
        if self.check_file(tile_path):
            return

        self.path = tile_path
        self.name = os.path.basename(tile_path)
        self.full_img = cv2.imread(tile_path)
        height, width = self.full_img.shape[:2]
        self.full_img = self.full_img[:, 0:height] # crop into square
        self.img = cv2.resize(self.full_img, (tile_size, tile_size))
        self.img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        # self.desaturate()

        self.avg_b, self.avg_g, self.avg_r, self.avg_t = cv2.mean(self.img)
        self.avg_h, self.avg_s, self.avg_v, self.avg_t = cv2.mean(self.img_hsv)
        self.hsv = [self.avg_h, self.avg_s, self.avg_v]

        self.best_coords = []

    def check_file(self, tile_path):
        """
        Skip files for various reasons
        0 filesize
        name = target.jpg or mosaic.jpg
        """
        self.filesize = os.path.getsize(tile_path)
        if self.filesize == 0:
            print("file is empty, skipping")
            return 1
        else:
            return 0


    def desaturate(self):
        self.avg_h, self.avg_s, self.avg_v, t = cv2.mean(self.img_hsv)
        h, s, v = cv2.split(self.img_hsv)
        new_s = s - SATURATION
        new_s.fill(SATURATION)
        self.img_hsv = cv2.merge([h, new_s, v])
        self.img = cv2.cvtColor(self.img_hsv, cv2.COLOR_HSV2BGR)


def check_files(tiles_path, target_file):
    """
    Make sure the tile path and target image exist
    """
    if not os.path.exists(tiles_path):
        print("{} does not exist".format(tiles_path))
        sys.exit()
    if not os.path.exists(target_file):
        print("{} does not exist".format(target_file))
        sys.exit()


def main():
    check_files(tiles_path, target_file)

    target = Target(target_file)
    mosaic = Mosaic(target)

    while True: # constantly look for new pictures
        time.sleep(1)
        for (dirpath, dirnames, filenames) in os.walk(tiles_path):
            for tile_name in filenames:
                if tile_name.lower().endswith('.jpg'):
                    print("Finding home for {}".format(tile_name))
                    tile = Tile(os.path.join(dirpath, tile_name))
                    if tile.filesize == 0:
                        break
                    mosaic.add_tile(tile)
                    print("There are {} empty coords remaining".
                          format(len(mosaic.empty_coords)))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-hi", "--hires", action='store_true', help="generate a hi-resolution mosaic")
    parser.add_argument("-t", "--tiledir", type=str, help="optionally provide tile source directory")
    parser.add_argument("-targ", "--target", type=str, help="optionally provide target file")
    parser.add_argument("-c", "--clean", action='store_true', help="remove tile_placement.log file located in tiledir")

    args = parser.parse_args()

    hires = False
    if args.tiledir:
        print(args.tiledir)
        tiles_path = args.tiledir
        target_file = os.path.join(tiles_path, 'target.jpg')
    if args.target:
        target_file = args.target
    if args.hires:
        print("make hi-res")
        hires = True
        ENLARGEMENT = ENLARGEMENT * HI_RES_MULT
        tile_size = tile_size * HI_RES_MULT
        time.sleep(1)
    if args.clean and args.tiledir:
        os.remove(os.path.join(tiles_path, 'tile_placement.log'))
        os.remove(os.path.join(tiles_path, 'mosaic-'+day_of_year+'.jpg'))
        print("remove tile_placement.log")
        print("remove mosaic.jpg")

    main()
