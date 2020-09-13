# ♙ ChessBot ♙
### AI & Robotics Practical Course

In this project, two robotic hands play a game of chess against each other. The environment of the engine is Nvidia PhysX. The hands are controlled by the KOMO library, which takes care of the forward and inverse kinematics. The opencv library in python is used to generate the representation of the states on the board. The moves are generated using a chess engine, in this case stockfish, which can be interfaced with the existing vision and manipulation framework.

![Screenshot](screenshot.png)

# Module Instalation

The following modules are needed, in addition to the basci python3 stuff and the aforementioned repository:
1. [PhysX](https://github.com/MarcToussaint/rai-maintenance/blob/master/help/localSourceInstalls.md#PhysX)
2. [Stockfish](https://www.howtoinstall.me/ubuntu/18-04/stockfish/)


## Base Repository

[Robotics Course](https://github.com/MarcToussaint/robotics-course)

## Setup

    cd final_project
    ./setup.py

This will copy the necessary .g files to `~/git/robotics-course/scenarios`


## Authors: 

- Aditya Mohan
- Benjamin Berta
- Oliver Horst
