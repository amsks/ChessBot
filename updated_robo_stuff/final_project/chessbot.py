import argparse
import sys
from os.path import expanduser
import random

import chess
from chess import COLORS, COLOR_NAMES, PIECE_NAMES, PIECE_TYPES, PIECE_SYMBOLS, STARTING_FEN, STARTING_BOARD_FEN, svg

from robo_pkg.workspace import Workspace
from robo_pkg.chess_engine import Human_Engine_Game

home = expanduser("~")
sys.path.append(home + '/git/robotics-course/build')
sys.path.append('../')  # add robo_pkg to path

parser = argparse.ArgumentParser(description='Chess robot')
# parser.add_argument('-r', '--radius', type=int, metavar='', help='radius of something')
args = parser.parse_args()

SQUARES = [
    A1, B1, C1, D1, E1, F1, G1, H1,
    A2, B2, C2, D2, E2, F2, G2, H2,
    A3, B3, C3, D3, E3, F3, G3, H3,
    A4, B4, C4, D4, E4, F4, G4, H4,
    A5, B5, C5, D5, E5, F5, G5, H5,
    A6, B6, C6, D6, E6, F6, G6, H6,
    A7, B7, C7, D7, E7, F7, G7, H7,
    A8, B8, C8, D8, E8, F8, G8, H8,
] = range(64)


class Square:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.w = 0.0
        self.piece = 0
        self.color = 0
        self.frame = ''


class PhysicalBoard:
    def __init__(self):
        self.squares = [Square() for square in SQUARES]


class ChessBot(Workspace):
    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.physical_board = PhysicalBoard()
        self.engine = Human_Engine_Game()
        #Precomputed game
        # self.engine.parseGame()
        print("""\
          ___           _____ __                   ____        __         ___
         (___)         / ____/ /_  ___  __________/ __ )____  / /_       (___)
          )_(         / /   / __ \/ _ \/ ___/ ___/ __  / __ \/ __/        )_(
         |___|       / /___/ / / /  __(__  |__  ) /_/ / /_/ / /_         |___|
        (_____)      \____/_/ /_/\___/____/____/_____/\____/\__/        (_____)
        """)


def main():
    chessbot = ChessBot()
    color = "white"
    count = 1
    movecount = 0
    gameon = True
    
    while gameon == True:
        count += 1
        if count % 100 == 0:
            print("moving")
            # reset board at each iteration
            chessbot.physical_board = PhysicalBoard()

            # PERCEPTION
            # get state of the board from the camera
            chessbot.physical_board, board_vertices, depth, board_dist = chessbot.run_perception(chessbot.physical_board)
            chessbot.physical_board = chessbot.update_C(depth, chessbot.physical_board, board_vertices, board_dist)
            
            # Overwrite it for now from the actual board
            position = chessbot.board.board_fen()

            # set virtual board to the perceived position
            chessbot.board.set_board_fen(position)

            # MOVE GENERATION
            # generate a move either from a predefined game or from the engine
            
            print("getting move")
            nextmove, movetype, occupant = chessbot.engine.getMoveCV(movecount, chessbot.physical_board)
            
            if not nextmove == False:
                movecount += 1
                print(nextmove)
                print(movetype)
                print(occupant)
                if (movetype == 1):
                    chessbot.execute_move(nextmove, color, movetype)
                    pass
                elif (movetype == 2):
                    chessbot.execute_move(nextmove, color, movetype, occupant)
                    pass
                print("Executed")
                if color == "white":
                    color = "black"
                else:
                    color = "white"
            else:
                print(" ---------- End of Game -----------")
                gameon = False


        chessbot.runRealWorld()
     


if __name__ == '__main__':
    main()
