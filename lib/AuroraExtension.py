"""
Generic Extension class
"""

import cv2
import os, sys
import logging
import time
import numpy as np


class AuroraExtension:
    def __init__(self, NeoPixels, HDMI):
        # Generic variables
        self.Author = "Andrew MacPherson (@AndrewMohawk)"
        self.Description = "Aurora Extension class"
        self.Name = "Aurora Extension Class"

        self.vid = HDMI
        self.vid_w = 1
        self.vid_h = 1
        self.channels = 0
        self.pixels = False

        self.FPS_count = 0
        self.FPS_avg = 0
        self.FPS_start_time = 0

        self.debug = bool(os.environ["AURORA_DEBUG"])
        self.noHDMI = False

        self.pixels = NeoPixels

        self.darkThreshhold = 20  # this defines if we are gonna bother lighting up the pixels if they are below this threshold
        # This is no longer used as it makes it noticably slower :(

        self.pixels.brightness = 1

        self.gamma = 1.0

        # Aurora Specifics
        try:
            self.pixelsCount = int(os.environ.get("AURORA_PIXELCOUNT_TOTAL"))
            self.pixelsLeft = int(os.environ["AURORA_PIXELCOUNT_LEFT"])
            self.pixelsRight = int(os.environ["AURORA_PIXELCOUNT_RIGHT"])
            self.pixelsTop = int(os.environ["AURORA_PIXELCOUNT_TOP"])
            self.pixelsBottom = int(os.environ["AURORA_PIXELCOUNT_BOTTOM"])
            self.gamma = float(os.environ["AURORA_GAMMA"])
            self.darkThreshhold =  int(os.environ["AURORA_DARKTHRESHOLD"])  # this defines if we are gonna bother lighting up the pixels if they are below this threshold
        # This is no longer used as it makes it noticably slower :(

        except Exception as e:
            self.log(
                "Error during initialisation of {}:{}".format(self.Name, str(e)), True
            )

            sys.exit(1)

    def fade_out_pixels(self):
        allout = False
        x = 0
        while allout == False:

            if x == self.pixelsCount:
                x = 0

            allout = True
            for z in range(0, self.pixelsCount):

                if self.pixels[z] != [0, 0, 0]:
                    allout = False
                    self.fadeToBlack(z)

            self.pixels.show()
            x += 1

    def fadeToBlack(self, pixelPos):
        fadeValue = 64
        b, g, r = self.pixels[pixelPos]

        r = 0 if r <= 10 else int(r - (r * fadeValue / 255))
        g = 0 if g <= 10 else int(g - (g * fadeValue / 255))
        b = 0 if b <= 10 else int(b - (b * fadeValue / 255))

        self.pixels[pixelPos] = (b, g, r)

    # Setup LEDs and Capture
    def setup(self):
        self.log("Setting Up {}".format(self.Name))

    def teardown(self):
        # incase things need to be broken down
        self.log("Tearing down {}".format(self.Name))
        self.fade_out_pixels()

    def makePixelFrame(self, filepath):
        if self.pixels != False:
            pixel_size = 15
            pixel_size_skew = pixel_size * 2
            border = 15
            if self.pixelsLeft > self.pixelsRight:
                pixelImageHeight = (
                    (self.pixelsLeft * pixel_size) + border + (pixel_size_skew * 2)
                )
            else:
                pixelImageHeight = (
                    (self.pixelsRight * pixel_size) + border + (pixel_size_skew * 2)
                )

            if self.pixelsTop > self.pixelsBottom:
                pixelImageWidth = (self.pixelsTop * pixel_size) + border
            else:
                pixelImageWidth = (self.pixelsBottom * pixel_size) + border

            pixelImage = np.zeros((pixelImageHeight, pixelImageWidth, 3), np.uint8)

            top_y = 5
            top_x = 5

            start_coordinate = 5 + pixel_size_skew

            # Left Rows
            for x in range(
                self.pixelsLeft - 1, -1, -1
            ):  # -1 since this actually starts at 0 and goes to num-1
                start = (top_x, start_coordinate)
                end = (top_x + pixel_size_skew, start_coordinate + pixel_size)
                colour = (self.pixels[x][2], self.pixels[x][1], self.pixels[x][0])
                pixelImage = cv2.rectangle(pixelImage, start, end, colour, -1)
                start_coordinate += pixel_size

            start_coordinate = 5
            # Top rows

            for x in range(self.pixelsLeft, self.pixelsLeft + self.pixelsTop):
                start = (start_coordinate, top_y)
                end = (start_coordinate + pixel_size, top_y + pixel_size_skew)
                colour = (self.pixels[x][2], self.pixels[x][1], self.pixels[x][0])
                pixelImage = cv2.rectangle(pixelImage, start, end, colour, -1)
                start_coordinate += pixel_size

            start_coordinate = 5 + pixel_size_skew
            # Right Rows
            for x in range(
                self.pixelsLeft + self.pixelsTop,
                self.pixelsLeft + self.pixelsTop + self.pixelsRight,
            ):
                start = (
                    top_x + (self.pixelsTop * pixel_size) - pixel_size_skew,
                    start_coordinate,
                )
                end = (
                    top_x + (self.pixelsTop * pixel_size),
                    start_coordinate + pixel_size,
                )

                colour = (self.pixels[x][2], self.pixels[x][1], self.pixels[x][0])
                color = (255, 0, 0)
                pixelImage = cv2.rectangle(pixelImage, start, end, colour, -1)
                start_coordinate += pixel_size

            start_coordinate = 5
            # Bottom rows
            for x in range(
                self.pixelsCount - 1,
                self.pixelsLeft + self.pixelsTop + self.pixelsRight - 1,
                -1,
            ):
                start = (
                    start_coordinate,
                    top_y
                    + (self.pixelsLeft * pixel_size)
                    + pixel_size_skew
                    + pixel_size_skew,
                )
                end = (
                    start_coordinate + pixel_size,
                    top_y + (self.pixelsLeft * pixel_size) + pixel_size_skew,
                )
                colour = (self.pixels[x][2], self.pixels[x][1], self.pixels[x][0])
                pixelImage = cv2.rectangle(pixelImage, start, end, colour, -1)
                start_coordinate += pixel_size

            # Save Image
            if pixelImageWidth > 800:
                r = 800 / float(pixelImageWidth)
                dim = (800, int(pixelImageHeight * r))
                pixelImage = cv2.resize(pixelImage, dim, interpolation=cv2.INTER_AREA)

            cv2.imwrite(filepath, pixelImage)
            # self.log("Saved PixelImage")
        else:
            self.log("Pixels not available, no image saved")

    def adjust_gamma(self, image, gamma=1.0):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values
        invGamma = 1.0 / gamma
        table = np.array(
            [((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]
        ).astype("uint8")
        # apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    def getFrame(self, video=True):

        self.FPS_count += 1
        time_diff_fps = time.time() - self.FPS_start_time
        if time_diff_fps >= 1:
            self.FPS_avg = self.FPS_count
            self.FPS_start_time = time.time()
            self.FPS_count = 0

        if video == True:
            # Capture the video frame
            ret, frame = self.vid.read()
            if ret == False:
                self.log(
                    "We cannot connect to video device anymore, hopefully restarting.."
                )
                os._exit(1)
            # TODO: Gamma evaluation -- this slows stuff down, I'm not sure we need it.
            elif self.gamma > 1:
                frame = self.adjust_gamma(frame, self.gamma)
            return [ret, frame]

        return [False, False]

    def autocrop(self, image, threshold=0):
        """Crops any edges below or equal to threshold
        Crops blank image to 1x1.
        Returns cropped image.
        """
        if len(image.shape) == 3:
            flatImage = np.max(image, 2)
        else:
            flatImage = image
        assert len(flatImage.shape) == 2

        rows = np.where(np.max(flatImage, 0) > threshold)[0]
        if rows.size:
            cols = np.where(np.max(flatImage, 1) > threshold)[0]
            image = image[cols[0] : cols[-1] + 1, rows[0] : rows[-1] + 1]
        else:
            image = image[:1, :1]

        return image

    def takeScreenShot(self, filepath, autocrop=False):
        # logging.info("Taking Screenshot in Aurora Extension")
        ret, self.current_frame = self.getFrame()
        screenshot_frame = self.current_frame

        if autocrop != False:
            screenshot_frame = self.autocrop(self.current_frame, autocrop)
            # logging.info(f"Cropped Screenshot to {screenshot_frame.shape}")

        self.vid_h, self.vid_w, self.channels = screenshot_frame.shape
        widthPixels = int(self.vid_w * (self.percent / 100)) + 1
        heightPixels = int(self.vid_h * (self.percent / 100) * 2) + 1

        colour = (0, 0, 255)

        # top
        screenshot_frame = cv2.rectangle(
            screenshot_frame, (0, 0), (self.vid_w, heightPixels), (0, 0, 255), 1
        )

        # bottom
        screenshot_frame = cv2.rectangle(
            screenshot_frame,
            (0, self.vid_h - heightPixels),
            (self.vid_w, self.vid_h),
            (0, 0, 255),
            1,
        )
        # left
        screenshot_frame = cv2.rectangle(
            screenshot_frame, (0, 0), (widthPixels, self.vid_h), (0, 0, 255), 1
        )
        # right
        screenshot_frame = cv2.rectangle(
            screenshot_frame,
            (self.vid_w - widthPixels, 0),
            (self.vid_w, self.vid_h),
            (0, 0, 255),
            1,
        )

        cv2.imwrite(filepath, screenshot_frame)

        return True

    def log(self, log_string, error=False):
        if error == True:
            logging.error("{} : {}".format(self.Name, log_string))
        elif self.debug == True:
            logging.debug("DEBUG {} : {}".format(self.Name, log_string))

    # This class runs the visualisation (mandatory)
    def visualise(self):

        try:
            # In your inheritted class run things here
            self.example = True
        except Exception as e:
            print("Error: {}".format(e))

    # Returns the current FPS of the application ( not mandatory)
    def showFPS(self):
        return 0
