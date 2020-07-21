import sys
from os.path import expanduser
import time

import cv2
import numpy as np

home = expanduser("~")
sys.path.append(home + '/git/robotics-course/build')
import libry as ry

import robo_pkg.cv_lib as cl
import robo_pkg.tf_lib as tf
import robo_pkg.kalman_filter as kf

import chess.pgn as cp


class Workspace:
    def __init__(self):
        # Set up Real World
        self.RealWorld = ry.Config()
        self.RealWorld.addFile(home + '/git/robotics-course/scenarios/chessbot.g')

        #Add friction
        for piece in self.RealWorld.getFrameNames()[83:]:
            #print(piece)
            self.RealWorld.getFrame(piece).addAttribute("friction", 200000)

        self.V = ry.ConfigurationViewer()
        self.V.setConfiguration(self.RealWorld)

        self.initContacts()

        # instantiate the simulation
        self.S = self.RealWorld.simulation(ry.SimulatorEngine.physx, verbose=5)
        self.fxypxy = [0.895 * 360., 0.895 * 360., 320., 180.]
        self.tau = 0.01
        self.S.addSensor("camera")
        self.C = ry.Config()
        self.C.addFile(home + '/git/robotics-course/scenarios/chessbot.g')
        self.cameraFrame = self.C.frame("camera")
        self.V.setConfiguration(self.C)

        table = self.C.getFrame('table')
        table.setContact(0)

    def run_perception(self, physical_board):
        [frame, depth] = self.S.getImageAndDepth()

        pointcloud = np.array(self.S.depthData2pointCloud(depth, self.fxypxy)).squeeze()
        board_vertices_tf, depth_int, board_dist = cl.find_board(frame, depth, pointcloud)
        physical_board = cl.detect_pieces(board_vertices_tf, depth_int, physical_board, frame)
        return physical_board, board_vertices_tf, depth, board_dist

    def update_C(self, depth, physical_board, board_vertices, board_dist):
        abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        size = 0.06
        height = 0.1
        for i, v in enumerate(board_vertices):
            pt = [v[0], v[1], board_dist]
            coord = tf.camera_to_world(pt, self.cameraFrame, self.fxypxy)
            coord[2] -= height / 2
            square_name = abc[i % 8] + str(i // 8 + 1)
            frame = self.C.getFrame(square_name)
            frame.setPosition(coord)

        heights = [0.03, 0.035, 0.035, 0.04, 0.04, 0.05]
        counter = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]
        piece_names = [["P", "N", "B", "R", "Q", "K"], ["p", "n", "b", "r", "q", "k"]]

        print(self.C.getFrameNames())

        for i, p in enumerate(physical_board.squares):
            if p.piece == 0:
                continue

            piece_ind = counter[p.color][p.piece - 1]
            counter[p.color][p.piece - 1] += 1

            # Transform point from camera to world
            pt = [p.y, p.x, depth[p.x, p.y]]
            coord = tf.camera_to_world(pt, self.cameraFrame, self.fxypxy)

            # Set z coordinate to the middle of the piece
            coord[2] -= heights[p.piece - 1] / 2

            # Set position of the piece
            piece_frame = piece_names[p.color][p.piece - 1] + '_' + str(piece_ind)
            physical_board.squares[i].frame = piece_frame
            frame = self.C.getFrame(piece_frame)
            frame.setPosition(coord)
        self.V.setConfiguration(self.C)
        return physical_board


        ###############################################################
        ################### Oliver's Safe Space #######################
        ###############################################################
    def updateC(self):
        for frame in self.C.getFrameNames():
            self.C.getFrame(frame).setPosition((self.RealWorld.getFrame(frame).getPosition()))
        self.V.setConfiguration(self.C)
        pass

    def runRealWorld(self, control=[]):
        self.S.step([], self.tau, ry.ControlMode.none)
        time.sleep(self.tau)
        pass

    def getFrame(self, loc, rob):  # ToDo: Not needed anymore?
        # ToDo: determine which piece occupies a given location
        if rob == 'R':
            return "n62"
        else:
            return "N1"

    def moveHandAbove(self, rob, piece, align=False):
        print("init komo")
        steps = 30
        # self.C.getFrame(piece).setContact(1)
        komo = self.C.komo_path(1., steps, 2, True)
        komo.addObjective([1.], ry.FS.positionDiff, [rob, piece], ry.OT.sos, [3e1], target=[0., 0., 0.15])


        if (rob[0] == 'R' and align):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L' and align):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])

        komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger2"], ry.OT.eq, [1e2], order=1)
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        # komo.addObjective([1.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[3e2])
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[3e2])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(10 * self.tau)

    def moveHandDown(self, rob, piece):
        print("init komo")
        steps = 20
        phases=2
        # self.C.getFrame(piece).setContact(1)
        # self.C.setJointState(self.C.getJointState())
        komo = self.C.komo_path(phases, steps, 2, True)
        if (rob[0] == 'R'):
            komo.addObjective([2.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            komo.addObjective([2.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])

        #komo.addObjective([1.,2.], ry.FS.position, [rob], ry.OT.sos, [1e1], target=[0,0,-.05], order=1)
        #komo.addObjective([1.,2.], ry.FS.vectorZ, [rob], ry.OT.eq, [1e1], target=[0,0,1])

        komo.addObjective([2.], ry.FS.positionDiff, [rob, piece], ry.OT.eq, [1e2], target=[0,0,.015])
        komo.addObjective([2.], ry.FS.oppose, [(rob[:2] + "finger2"), (rob[:2] + "finger1"), piece], ry.OT.eq,
                          [1e1])
        komo.addObjective([], ry.FS.qItself, [(rob[:2] + "finger1")], ry.OT.eq, [1e2], order=1)
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([], ry.FS.qItself, [], ry.OT.sos, [80], order=2)
        komo.addObjective([2.], ry.FS.qItself, [], ry.OT.sos, [700], order=1)
        # komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.ineq, scale=[1e3])
        komo.addObjective([1.,2.], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[1e3])
        komo.addObjective([1.,2.], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[1e3])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps*phases):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(20 * self.tau)

    def moveHandDownVelo(self, rob, piece):
        print("init komo")
        steps = 20
        phases=1
        # self.C.getFrame(piece).setContact(1)
        # self.C.setJointState(self.C.getJointState())
        komo = self.C.komo_path(phases, steps, 2, True)
        if (rob[0] == 'R'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])


        komo.addObjective([1.], ry.FS.positionDiff, [rob, piece], ry.OT.eq, [1e3], target=[0,0,.017])
        komo.addObjective([], ry.FS.position, [rob], ry.OT.sos, [5e3], order=1, target=[0,0,-.05])
        komo.addObjective([], ry.FS.qItself, [(rob[:2] + "finger1")], ry.OT.eq, [1e2], order=1)
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([], ry.FS.qItself, [], ry.OT.sos, [80], order=2)
        komo.addObjective([1.], ry.FS.qItself, [], ry.OT.sos, [700], order=1)
        # komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.ineq, scale=[1e3])
        komo.addObjective([], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[1e3])
        komo.addObjective([], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[1e3])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps*phases):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(20 * self.tau)

    def moveHandDownIK(self, rob, piece):
        IK = self.C.komo_IK(False)
        IK.addObjective([], ry.FS.accumulatedCollisions, [], ry.OT.ineq, [1e3])
        if (rob[0] == 'R'):
            IK.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            IK.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])
        IK.addObjective([], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[1e3])
        IK.addObjective([], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[1e3])
        IK.optimize()
        print(IK.getConfiguration(0).shape)
        print('yup')

    def moveHandSmooth(self, rob, piece):
        print("init komo")
        steps = 30
        # self.C.getFrame(piece).setContact(1)
        # self.C.setJointState(self.C.getJointState())
        komo = self.C.komo_path(1., steps, 2, True)
        if (rob[0] == 'R'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])
        komo.addObjective([.8], ry.FS.positionDiff, [rob, piece], ry.OT.sos, [3e2], target=[0, 0, .1])

        komo.addObjective([1.], ry.FS.positionDiff, [rob, piece], ry.OT.eq, [3e2], target=[0, 0, .015])
        komo.addObjective([1.], ry.FS.oppose, [(rob[:2] + "finger2"), (rob[:2] + "finger1"), piece], ry.OT.eq,
                          [2e1])
        komo.addObjective([], ry.FS.qItself, [(rob[:2] + "finger1")], ry.OT.eq, [1e3], order=1)
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([1.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        # komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.ineq, scale=[10e4])
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[3e4])
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[3e4])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(20 * self.tau)
        pass

    def moveHandTo(self, rob, piece, twostep=True):
        if twostep:
            self.moveHandAbove(rob, piece, align=True)
            self.openGripper(rob)
            self.moveHandDownVelo(rob, piece)
            #self.moveHandDownIK(rob, piece)
            #self.moveHandDown(rob, piece)
        else:
            self.moveHandSmooth(rob, piece)
        # print(self.C.evalFeature(ry.FS.oppose, [(str(rob[0])+"_finger2"),(str(rob[0])+"_finger1"), piece]))

    def movePiece2(self, rob, piece, goal):
        # self.C.attach("R_gripper", piece)
        self.moveHandUp(rob)
        print("init komo")
        toppos = self.C.getFrame(str(rob[0]) + "_gripper").getPosition() + [0., 0., 0.1]
        komo = self.C.komo_path(2., 15, 2, True)

        #Velocity based steering ~ weird
        #komo.addObjective([0.,1.], ry.FS.position, ["R_gripperCenter"], ry.OT.sos, [1e1], target=[0,0,.05], order=1)##
        komo.addObjective([1.,2.], ry.FS.position, [str(rob[0])+"_gripperCenter"], ry.OT.sos, [1e4], target=[0,0,-.05], order=1)##

        if (rob[0] == 'R'):
            komo.addObjective([2.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            komo.addObjective([2.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[1e3],
                              target=[1, 0, 0])

        komo.addObjective([2.], ry.FS.positionDiff, [piece, goal], ry.OT.eq, [1e4], target=[.0, .0, .07])
        #komo.addObjective([1.], ry.FS.positionDiff, [piece, goal], ry.OT.sos, [1e2], target=[.0, .0, .15])
        komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger1"], ry.OT.eq, [1e3], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.eq, scale=[1e3])
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([2.], ry.FS.qItself, [], ry.OT.sos, [1e2], order=1)
        komo.addObjective([], ry.FS.vectorZ, [piece], ry.OT.eq, [1e1], target=[0,0,1])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, 30):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)

            self.C.computeCollisions()  # this calls broadphase collision detection
            # print(self.C.getCollisions(belowMargin=.01))

            time.sleep(self.tau)#(10 * self.tau)
        # self.C.attach("world", piece)

    def return2init(self, pos):
        print("init komo")
        komo = self.C.komo_path(1., 30, 2, True)
        komo.addObjective([1.], ry.FS.qItself, [], ry.OT.eq, [3e2], target=pos)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.ineq, scale=[10e3])
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([1.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, 30):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            # print(pos)
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(10 * self.tau)

    def grab(self, rob, piece):
        print("Trying to grab")
        self.RealWorld.frame(piece).setContact(-1)
        self.C.frame(piece).setContact(-1)
        self.S.closeGripper(rob[:9])
        print(self.S.getGripperIsGrasping(rob[:9]))
        self.C.attach(rob[:9], piece)
        count = 0
        while not self.S.getGripperIsGrasping(rob[:9]):
            count += 1
            self.S.step([], self.tau, ry.ControlMode.none)
            time.sleep(self.tau)
            if count > 200:
                print("Grasp not working?")
                break

    def release(self, rob, piece):
        print("Releasing Object")
        self.C.attach("world", piece)
        self.C.getFrame(piece).setContact(1)
        self.RealWorld.getFrame(piece).setContact(1)
        self.openGripper(rob)

    def openGripper(self, rob):
        self.S.openGripper(rob[:9])
        while self.S.getGripperWidth(rob[:9])<0.02:
            self.S.step([], self.tau, ry.ControlMode.none)
            q = self.S.get_q()
            self.C.setJointState(q)
            time.sleep(self.tau)

    def movePiece(self, rob, piece, goal, move_back=True, twostepto=True):
        initialPose = self.C.getJointState()
        print("moving hand to piece")
        self.moveHandTo(rob, piece, twostepto)
        self.grab(rob, piece)
        # self.C.getFrame("R_gripper").setContact(0)
        self.movePiece2(rob, piece, goal)
        self.release(rob, piece)
        self.moveHandUp(rob)
        if move_back:
            self.return2init(initialPose)

    def setPieceAside(self, rob, piece):  # ToDo: place in row, not on a pile

        self.moveHandTo(rob, piece)
        self.grab(rob, piece)
        self.moveHandUp(rob)
        steps=15
        phases=2
        #toppos = self.C.getFrame(str(rob[0]) + "_gripper").getPosition() + [0., 0., 0.1]
        komo = self.C.komo_path(phases, steps, 2, True)
        komo.addObjective([2.], ry.FS.position, [piece], ry.OT.eq, [3e4], target=[-0.21, -0.3, .7])
        komo.addObjective([1.], ry.FS.position, [piece], ry.OT.sos, [3e4], target=[-0.21, -0.3, 1])
        #komo.addObjective([1.], ry.FS.position, [str(rob[0]) + "_gripper"], ry.OT.sos, [3e4], target=toppos)
        komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger1"], ry.OT.eq, [1e2], order=1)
        #komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger2"], ry.OT.eq, [1e2], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.eq, scale=[10e4])
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([2.], ry.FS.qItself, [], ry.OT.sos, [1e3], order=1)
        komo.addObjective([], ry.FS.qItself, [], ry.OT.sos, [100], order=2)
        komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective([2.], type=ry.OT.eq, feature=ry.FS.vectorZ, frames=[piece], scale=[3e5],
                          target=[0., 0., 1.])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps*phases):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)

            time.sleep(self.tau)#(10 * self.tau)

        self.release(rob, piece)
        pass

    def moveHandUp(self, rob):
        toppos = self.C.getFrame(str(rob[0]) + "_gripper").getPosition() + [0., 0., 0.2]

        komo = self.C.komo_path(1., 15, 2, True)
        #komo.addObjective([1.], ry.FS.position, [str(rob[0]) + "_gripper"], ry.OT.sos, [3e4], target=toppos)
        #komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger1"], ry.OT.eq, [1e2], order=1)
        komo.addObjective([], ry.FS.position, [rob], ry.OT.eq, [1e3], order=1, target=[0,0,0.05])
        komo.addObjective([], ry.FS.qItself, [str(rob[0]) + "_finger2"], ry.OT.eq, [1e2], order=1)
        komo.addObjective(feature=ry.FS.accumulatedCollisions, type=ry.OT.eq, scale=[10e4])
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([], ry.FS.qItself, [], ry.OT.sos, [50], order=2)
        komo.addObjective([0.], ry.FS.qItself, [], ry.OT.sos, [1000], order=1)
        komo.addObjective([], type=ry.OT.eq, feature=ry.FS.vectorZ, frames=[rob], scale=[3e5],
                          target=[0., 0., 1.])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, 15):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(10 * self.tau)
        pass

    def take_piece(self, rob, piece, goal, piece2take):
        # 1st piece to take goes to [-0.21 -0.25 .7]
        initialPose = self.C.getJointState()
        self.setPieceAside(rob, piece2take)
        self.moveHandUp(rob)
        self.movePiece(rob, piece, goal, False, True)
        self.return2init(initialPose)

    def initContacts(self):
        for piece in self.RealWorld.getFrameNames()[len(self.RealWorld.getFrameNames()) - 32:]:
            self.RealWorld.getFrame(piece).setContact(1)
        for piece in self.RealWorld.getFrameNames()[83:len(self.RealWorld.getFrameNames()) - 32]:
            self.RealWorld.getFrame(piece).setContact(0)
        pass

    def testSideAlign(self, rob, piece):
        print("init komo")
        steps = 30
        # self.C.getFrame(piece).setContact(1)
        komo = self.C.komo_path(1., steps, 2, True)
        komo.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq)
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductYZ, frames=[rob, piece], scale=[3e2])
        komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.scalarProductXZ, frames=[rob, piece], scale=[3e2])

        if (rob[0] == 'R'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[3e2],
                              target=[-1, 0, 0])
        if (rob[0] == 'L'):
            komo.addObjective([1.], type=ry.OT.eq, feature=ry.FS.vectorY, frames=[rob], scale=[3e2],
                              target=[1, 0, 0])
        print("optimize komo")
        komo.optimize()
        print("exec komo steps...")
        for i in range(0, steps):
            self.C.setFrameState(komo.getConfiguration(i))
            self.V.setConfiguration(self.C)
            pos = self.C.getJointState()
            self.S.step(pos, self.tau, ry.ControlMode.position)
            time.sleep(self.tau)#(10 * self.tau)

    def execute_move(self, move, color, movetype=1, other_piece=None):
        # Available Movetypes:
        # 1 = Normal move
        # 2 = Taking a piece
        # Movetypes to implement:
        # 3 = Castling
        # 4 = Queening (consideration: more than once?)
        # 5 = en passant
        # ToDo else: Additional variable "piece"
        print(move)
        for piece in self.C.getFrameNames()[len(self.C.getFrameNames()) - 32:]:
            self.C.getFrame(piece).setContact(1)
        for piece in self.C.getFrameNames()[83:len(self.C.getFrameNames()) - 32]:
            self.C.getFrame(piece).setContact(0)
        robot2move = ''
        movetile = move[len(move) - 2:]

        if color == 'black':
            robot2move = "R_gripperCenter"
        else:
            robot2move = "L_gripperCenter"
        # ToDo: Below will become obsolete with implementation of piece parameter
        piece2move = move[:len(move) - 3]
        print(move)
        if movetype == 1:
            # self.testSideAlign(robot2move, piece2move)
            self.movePiece(robot2move, piece2move, movetile)
            # self.movePiece(robot2move,piece2move,moveplaceholder)
        elif movetype == 2:
            print("Gonna take a pawn")
            self.take_piece(robot2move, piece2move, movetile, other_piece)
        # self.C.getFrame(piece2move)
