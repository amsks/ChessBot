from collections import deque

import cv2
import imutils
import numpy as np


def detect_ball(frame, color='red'):
    if color is 'red':
        lower_bound = np.array([100,150,0])
        upper_bound = np.array([130,255,255])
        
    # initialize the list of tracked points, the frame counter,
    # and the coordinate deltas
    pts = deque(maxlen=32)
    counter = 0
    (dX, dY) = (0, 0)
    direction = ""
    
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    rows = mask.shape[0]
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, rows / 8,
                               param1=35, param2=15,
                               minRadius=0, maxRadius=0)
    
    return circles, mask


def draw_circles(circles, frame):
    if circles is not None:
#         circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            # circle center
            cv2.circle(frame, center, 1, (0, 100, 100), 3)
            # circle outline
            radius = i[2]
            cv2.circle(frame, center, radius, (255, 0, 255), 3)