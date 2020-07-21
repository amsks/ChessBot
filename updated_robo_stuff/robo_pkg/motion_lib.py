import sys
from os.path import expanduser
home = expanduser("~")
sys.path.append(home + '/git/robotics-course/build')
import libry as ry
import numpy as np

def modSineCurve(steps, t, q0, q1):
    q_diff = q1 - q0
    q_diff_ = np.pi/(2*(np.pi+4))*q_diff
    
    q = q0
    C1 = np.pi/(4+np.pi)
    C2 = 1/(16+4*np.pi)
    C3 = 1/(4+np.pi)
    
    if t < (steps/8):
        q = q0 + q_diff * (C1 * t / steps - C2 * np.sin(4*np.pi*t/steps))
        return q
    elif t >= (steps/8) and t <= (steps*7/8):
        q = q0 + q_diff * (2*C3 + C1 * t/steps - 9*C2 * np.sin(4*np.pi/3*t/steps+np.pi/3))
        return q
    elif t>(steps*7/8):
        q = q0 + q_diff * (4*C3 + C1 * t/steps - C2 * np.sin(4*np.pi*t/steps))
        return q

def move_to(pt, IK, arm):
    pass