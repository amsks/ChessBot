from collections import deque

import cv2
import imutils
import numpy as np


def find_board(frame, depth, pointcloud):
    board_vertices = np.mgrid[0.0:8.0:1.0, 0.0:8.0:1.0].reshape(2, -1).T

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # detect edges and apply morphological transformation
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    edges = cv2.dilate(edges, np.array([[1, 1], [1, 1]], np.uint8), iterations=1)

    # detect contours
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # segment contours of the squares
    contours, areas, centroids = prune_contours(contours)

    centroids = np.float32(centroids).squeeze()

    # select corner squares and find homography
    corners = find_corners(centroids)
    H, mask = cv2.findHomography(board_vertices[[0, 7, 56, 63]], corners)

    # transform the centers of squares by applying homography
    board_vertices_tf = []
    for i, v in enumerate(board_vertices):
        board_vertices_tf.append((H @ np.hstack([v, 1]))[:2])
    board_vertices_tf = np.array(board_vertices_tf).reshape(-1, 2)
    board_vertices_tf = np.rint(board_vertices_tf).astype(np.int)

    # calculate distance of the beard
    depth_at_vertices = depth[board_vertices_tf[:, 1], board_vertices_tf[:, 0]]
    pc_at_vertices = pointcloud[board_vertices_tf[:, 1], board_vertices_tf[:, 0]]
    board_dist = np.max(depth_at_vertices)
    board_height = np.min(pc_at_vertices)

    depth_int = (- depth + board_dist) * 1000.0
    depth_int = depth_int.astype(np.int)

    # ---------------------- Debug images ----------------------- #
    # cv2.drawContours(rgb, contours, -1, (0, 255, 0), 1)
    # # for i, inter in enumerate(centroids):
    # #     cv2.circle(rgb, (inter[0], inter[1]), 3, (0, 0, 255))
    # # show corners
    # for i, inter in enumerate(corners):
    #     cv2.circle(rgb, (inter[0], inter[1]), 3, (255, 0, 0))
    # # Show the centers of each square
    # for i, inter in enumerate(board_vertices_tf):
    #     cv2.circle(rgb, (inter[0], inter[1]), 5, (0, 0, 255))
    # cv2.namedWindow("rgb", cv2.WINDOW_NORMAL)
    # cv2.imshow('edges', edges)
    # cv2.imshow('rgb', rgb)
    #
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     pass

    return board_vertices_tf, depth_int, board_dist


def detect_pieces(board_vertices_tf, depth_int, physical_board, frame):
    [PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING] = range(1, 7)
    # Calculate grid distance
    grid_dist = np.int(np.sqrt((board_vertices_tf[0, 0] - board_vertices_tf[1, 0]) ** 2 + (
            board_vertices_tf[0, 1] - board_vertices_tf[1, 1]) ** 2))
    half_grid_dist = np.floor_divide(grid_dist, 2) - 1

    for i, s in enumerate(board_vertices_tf):
        depth_at_square = depth_int[s[1] - half_grid_dist:s[1] + half_grid_dist,
                          s[0] - half_grid_dist:s[0] + half_grid_dist]
        height = np.max(depth_at_square)
        cnts, segment = detect_contour(depth_at_square)
        square_frame = frame[s[1] - half_grid_dist:s[1] + half_grid_dist,
                       s[0] - half_grid_dist:s[0] + half_grid_dist]
        avg_color = np.average(square_frame[segment == 1])
        color = 0
        if avg_color > 127:
            physical_board.squares[i].color = 0
        else:
            physical_board.squares[i].color = 1
        if not cnts:
            continue

        f = lambda i: cnts[i].size
        cnts_ind = max(range(len(cnts)), key=f)
        shape = detect_shape(cnts[cnts_ind])

        cx, cy = contour_center(cnts[cnts_ind])
        physical_board.squares[i].x = s[1] - half_grid_dist + cy
        physical_board.squares[i].y = s[0] - half_grid_dist + cx

        if np.abs(height - 30) < 2:  # and sd == 'circle'
            physical_board.squares[i].piece = PAWN
        elif np.abs(height - 35) < 2 and shape == 'circle':
            physical_board.squares[i].piece = BISHOP
        elif np.abs(height - 35) < 2:
            physical_board.squares[i].piece = KNIGHT
        elif np.abs(height - 40) < 2 and (shape == 'square' or shape == 'rectangle'):
            physical_board.squares[i].piece = ROOK
        elif np.abs(height - 45) < 2:  # and sd == 'circle'
            physical_board.squares[i].piece = QUEEN
        elif np.abs(height - 50) < 2:  # and sd == 'circle'
            physical_board.squares[i].piece = KING
    return physical_board


def find_corners(centers):
    min_x = np.min(centers[:, 0])
    max_x = np.max(centers[:, 0])
    min_y = np.min(centers[:, 1])
    max_y = np.max(centers[:, 1])

    return np.array([[min_x, min_y], [min_x, max_y], [max_x, min_y], [max_x, max_y]]).reshape(-1, 2)


def detect_contour(depth):
    max_height = np.max(depth)
    depth[depth < 0.9 * max_height] = 0
    depth[depth > 0] = 1
    depth = np.uint8(depth)
    # canny = cv2.Canny(depth, 1, 3, apertureSize=3)
    sobel_x = np.abs(cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=1))
    sobel_y = np.abs(cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=1))
    sobel = np.uint8(sobel_x + sobel_y)
    cnts, _ = cv2.findContours(sobel.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    return cnts, depth


def contour_center(c):
    M = cv2.moments(c)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    return cX, cY


def detect_shape(c):
    # initialize the shape name and approximate the contour
    shape = "unidentified"
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    # if the shape is a triangle, it will have 3 vertices
    if len(approx) == 3:
        shape = "triangle"
    # if the shape has 4 vertices, it is either a square or
    # a rectangle
    elif len(approx) == 4:
        # compute the bounding box of the contour and use the
        # bounding box to compute the aspect ratio
        (x, y, w, h) = cv2.boundingRect(approx)
        ar = w / float(h)
        # a square will have an aspect ratio that is approximately
        # equal to one, otherwise, the shape is a rectangle
        shape = "square" if 0.95 <= ar <= 1.05 else "rectangle"
    # if the shape is a pentagon, it will have 5 vertices
    elif len(approx) == 5:
        shape = "rectangle"
    # otherwise, we assume the shape is a circle
    else:
        shape = "circle"
    # return the name of the shape
    return shape


def prune_contours(cnts):
    new_cnts = []
    areas = []
    sizes = []
    centroids = []
    for cnt in cnts:
        sizes.append(cnt.size)
        area = cv2.contourArea(cnt)
        areas.append(area)
        if area < 400 or area > 710:
            continue
        # elif asd > 55:
        #     continue
        else:
            M = cv2.moments(cnt)
            centroids.append([int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])])
            new_cnts.append(cnt)
    return new_cnts, areas, centroids


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