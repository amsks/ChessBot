def depth_data_to_point(pt, fxypxy):
    pt = pt.copy()
    pt[0] = pt[2] * (pt[0] - fxypxy[2]) / fxypxy[0]
    pt[1] = -pt[2] * (pt[1] - fxypxy[3]) / fxypxy[1]
    pt[2] = -pt[2]
    return pt


def camera_to_world(pt, cameraFrame, fxfypxpy):
    """
    pt = np.array([u, v, distance])
    """
    cam_rot = cameraFrame.getRotationMatrix()
    cam_trans = cameraFrame.getPosition()

    pt_tf = depth_data_to_point(pt, fxfypxpy) @ cam_rot.T + cam_trans
    return pt_tf
