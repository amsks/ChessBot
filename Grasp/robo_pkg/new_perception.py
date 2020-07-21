
from collections import deque

import cv2 as cv
import imutils
import numpy as np


# Perception Pipeline 
#segment red ball using color
def segment_ball (rgb):
    rgb = cv.cvtColor(rgb, cvCOLOR_BGR2RGB)
    hsv = cv.cvtColor(rgb, cvCOLOR_BGR2RGB)
    
    mask1 = cv.inRange(hsv, (-20,120,70), (10,255,255))
    mask2 = cv.inRange(hsv, (170,120,70), (180,255,255))
    mask = mask1 + mask2
    
    #detect contours
    contours, hierarchy = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    filtered_mask = np.zeros(mask.shape, np.uint8)
    
    cv.drawContours (filtered_mask, contours, -1, (255,255,255), -1)
    
    return filtered_mask

#get image pointcloud
def image_pointcloud ( depth, mask ):
    mask_pixels = np.where(mask > 0)
    pointcloud = np.empty((mask_pixels[0].shape[0], 3))
    pointcloud[:,0] = mask_pixels[1]                    # x pixels
    pointcloud[:,0] = mask_pixels[1]                    # y pixels 
    pointcloud[:,2] = depth[mask_pixels[0], mask_pixels[1]]
    
    return pointcloud

#convert it to world frame
def meter_pointcloud (pixel_points, fxfypxpy):
    points = np.empty(np.shape(pixel_points))
    
    for i,p in enumerate(pixel_points):
        x = p[0]
        y = p[1]
        d = p[2]
        
        f = fxfypxpy[0]
        px = fxfypxpy[-2]
        py = fxfypxpy[-1]
        
        x_ = d*(x-px)/f
        y_ = - d*(y-py)/f
        z_ = - d
        
        points[i] = [x_, y_, z_]
        
    
    return points

#locate the object
def find_ball(rgb, depth, fxfypxpy):
    
    mask = segment_ball(rgb)
    pixel_points = image_pointcloud( depth, mask )
    obj_points = meter_pointcloud (pixel_points, fxfypxpy)
    
    return obj_points, mask

