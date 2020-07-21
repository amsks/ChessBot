import sys
from os.path import expanduser
home = expanduser("~")
sys.path.append(home + '/git/robotics-course/build')

import IPython
import time
import cv2
import numpy as np
import trio
import libry as ry
from multiprocessing import Process, Queue
import logging, multiprocessing
logger = multiprocessing.log_to_stderr()
logger.setLevel(multiprocessing.SUBDEBUG)

import robo_pkg.cv_lib as cl
import robo_pkg.tf_lib as tf
import robo_pkg.kalman_filter as kf
import robo_pkg.new_perception as pr

class Workspace:
    closing = False
    
    def __init__(self, add_imp=False):
        self.RealWorld = ry.Config()
        self.RealWorld.addFile(home + '/git/robotics-course/scenarios/challenge.g')
        
        self.V = ry.ConfigurationViewer()
        self.V.setConfiguration(self.RealWorld)
        
        self.set_objects()

        # instantiate the simulation
        self.S = self.RealWorld.simulation(ry.SimulatorEngine.physx, True)
        self.S.addSensor("camera")
        
        if add_imp:
            self.S.addImp(ry.ImpType.objectImpulses, ['obj0'], [])
        
        self.C = ry.Config()
        self.C.addFile(home + '/git/robotics-course/scenarios/pandasTable.g')
        self.V.setConfiguration(self.C)
        self.setup_camera()
        self.V.setConfiguration(self.C)
        self.add_ball() 
        self.tau = 0.01
    
    def setup_camera(self):
        self.cameraFrame = self.C.frame("camera")
        self.f = 0.895 * 360
        self.fxypxy = [self.f, self.f, 320., 180.]
    
    def set_objects(self):
        #change some colors
        self.RealWorld.getFrame("obj0").setColor([0,1,0])
        self.RealWorld.getFrame("obj1").setColor([1,0,0])
        self.RealWorld.getFrame("obj2").setColor([1,1,0])
        self.RealWorld.getFrame("obj3").setColor([1,0,1])
        self.RealWorld.getFrame("obj4").setColor([0,1,1])

        #you can also change the shape & size
        self.RealWorld.getFrame("obj0").setColor([1.,0,0])
        self.RealWorld.getFrame("obj0").setShape(ry.ST.sphere, [.028])
        #self.RealWorld.getFrame("obj0").setShape(ry.ST.ssBox, [.05, .05, .2, .01])
        self.RealWorld.getFrame("obj0").setPosition([-0.1, 0.1, 1.])

        #remove some objects
        for o in range(1,30):
            name = "obj%i" % o
#             print("deleting", name)
            self.RealWorld.delFrame(name)
        self.V.recopyMeshes(self.RealWorld)
        self.V.setConfiguration(self.RealWorld)

    
    def add_ball(self):
        self.obj = self.C.addFrame("obj0")
        self.obj.setPosition([0.8,0,1.5])
        self.obj.setQuaternion([1,0,.5,0])
        self.obj.setShape(ry.ST.sphere, [.04])
        self.obj.setColor([1,0,0])
        self.obj.setContact(1)

    
    def pick_up(self, frame):
        [y,J] = self.C.evalFeature(ry.FS.positionDiff, ["R_gripperCenter", frame])
        vel_ee = -y
        vel = J.T @ np.linalg.inv(J@J.T + 1e-2*np.eye(y.shape[0])) @ vel_ee;

        if np.linalg.norm(y) < 0.001:
            print('grasping...')
            self.S.closeGripper("R_gripper")

        if self.S.getGripperIsGrasping("R_gripper"):
            print('yaay')
            return True
        else:
            return False
        
            
    
    def go_to(self, frame):
        pass
    
    def go_to_base(self):
        pass

    
    def cv_loop(self, show):
        [frame, depth] = self.S.getImageAndDepth()
        # if frame is None:
        #     return False

        points = self.S.depthData2pointCloud(depth, self.fxypxy)
        self.cameraFrame.setPointCloud(points, frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        points = self.S.depthData2pointCloud(depth, self.fxypxy)
        self.cameraFrame.setPointCloud(points, frame)

        circles, mask = cl.detect_ball(frame)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            center = (circles[0, 0, 0], circles[0, 0, 1])

            dist = depth[circles[0, 0, 1], circles[0, 0, 0]]
            r = circles[0, 0, 2]
            R = r * dist /(self.f-r) 

            x_ball = np.array([circles[0, 0, 0], circles[0, 0, 1], dist+R])

            x_ball = tf.camera_to_world(x_ball, self.cameraFrame, self.fxypxy)
#             x_ball = np.hstack((x_ball, R))

#             pred = kalman_filter.predict()
#             print(pred)
#             x_ball, _ = kalman_filter.update(x_ball)

#                 print(x_ball)
            self.obj.setPosition(x_ball)
            self.obj.setShape(ry.ST.sphere, [R])

        if show:
            cl.draw_circles(circles, rgb)
            cv2.imshow('OPENCV - rgb', rgb)
            cv2.imshow('OPENCV - depth', 0.5* depth)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print(heh)
        
    def control_loop(self, t):  
        global state
        pseudo_inverse = False
        
        q = self.S.get_q()
        self.C.setJointState(q) #set your robot model to match the real q
        
        # pick up
        # if failed, go back to base -> pick up again
        # is succeded, go to endpos
        # drop
        # start again
        if pseudo_inverse:
            [y,J] = self.C.evalFeature(ry.FS.quaternionDiff, ["R_gripperCenter", "obj0"])
            vel_ee = -y
            vel = J.T @ np.linalg.inv(J@J.T + 1e-2*np.eye(y.shape[0])) @ vel_ee;
            
        if t > 50:    
            IK = self.C.komo_path(phases=1., stepsPerPhase=5, timePerPhase=5., useSwift=True);
            IK.addObjective([1.], ry.FS.accumulatedCollisions, [], ry.OT.eq);
            rotation = [ -0.6123724, 0.3535534, -0.3535534, 0.6123724 ]
            IK.addObjective([1.], ry.FS.quaternion, ['R_gripperCenter'], ry.OT.eq, [], [], rotation)

            IK.addObjective([1.], ry.FS.positionDiff, ["R_gripperCenter", "obj0"], ry.OT.sos, [1e2], [], [])
    #         IK.addObjective([1.], ry.FS.scalarProductXX, ['ball', 'R_gripperCenter'], ry.OT.eq)
    #         IK.addObjective([1.], ry.FS.scalarProductYY, ['ball', 'R_gripperCenter'], ry.OT.eq)

#             distance = self.C.feature(ry.FS.positionDiff, ["R_gripperCenter", "ball"])
#             [y,J] = distance.eval(self.C)

#             if np.linalg.norm(y) < 0.005:
#                 print('grasping...')
#                 self.S.closeGripper("R_gripper")
#             if self.S.getGripperIsGrasping("R_gripper"):
#                 print('yaay')
#                 ball_taken = True


            
            IK.optimize()
            result = IK.getConfiguration(0)
            
            if self.closing == False:
                y,J = self.C.evalFeature(ry.FS.positionDiff, ["R_gripperCenter", "obj0"])
                
                epsilon = abs(max(y, key=abs))
                
                if epsilon < 1e-2:
                    self.closing = True
                    self.S.closeGripper("R_gripper")
                    
            
            if self.S.getGripperIsGrasping("R_gripper"):
                [y,J] = self.C.evalFeature(ry.FS.position, ["R_gripper"]);
                control_target = control_target - J.T @ np.linalg.inv(J@J.T + 1e-2*np.eye(y.shape[0])) @ [0.,0.,-2e-4]
            
            
            
            
            
            
            
            temp_config = ry.Config()
            temp_config.addFile(home + '/git/robotics-course/scenarios/pandasTable.g')
            frame_names = self.C.getFrameNames()
            temp_config.setFrameState(result, frame_names)
            joint_state = temp_config.getJointState()
        
            control_target = joint_state
            control_mode = ry.ControlMode.position
        
#         print(control_target)

        
        
#         print(result.shape)
            
#         valami = self.C.feature(ry.FS.scalarProductXX, ["R_gripperCenter", "ball"])
#         egy, ketto = valami.eval(self.C)
        
#         control_target = vel
#         control_mode = ry.ControlMode.velocity
        
            
        else:
            control_target = []
            control_mode = ry.ControlMode.none
        
        return control_mode, control_target
        
    

    def simulation_loop(self, t):
        if not t%10:
            self.cv_loop(show=True)
        
        control_mode, control_target = self.control_loop(t)
        
        return control_mode, control_target
    
    
    def run(self):
        
#         print(self.C.getFrameNames())
      #  print(self.RealWorld.getFrameNames())
        
        tau = self.tau
        t = 0
        
        
        
        while True:
            time.sleep(tau)
            
            control_mode, control_target = self.simulation_loop(t)
         
      
            self.V.recopyMeshes(self.C)   
            self.V.setConfiguration(self.C)
            
            self.S.step(control_target, tau, control_mode)
            t += 1        
      
