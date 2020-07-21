#!/usr/bin/python3

'''
	This file contains three classes:
		1. PGN_Game() : Parses a pgn file and returns a dictionary of moves
		2. Engine_Self_Game() : Makes the stockfish engine play against itself and prints a dictinary of from and to moves in the process
		3. Human_Engine_Game() : Allow a human to enetr uci input for move and play against stockfish

	NOTE: Stockfish needs to be installed for this:
		1. sudo apt update -y
		2. sudo apt install -y stockfish

'''

import chess
import chess.engine
import chess.pgn as cp
from pgn_parser import pgn, parser
import os
import sys

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


class PGN_Game():
	def __init__(self):
		self.State = []
		file = open("../robo_pkg/Adams.pgn")
		self.first_game = cp.read_game(file)
		self.second_game = cp.read_game(file)
		self.game = parser.parse(str(self.second_game.mainline_moves()), actions=pgn.Actions())
		self.moves = []
		self.moves_assoc = []

	class piece_move():
		def __init__(self, name, position):
			self.name = name
			self.position = position

	def check_odd (self, x ):
		if x % 2 == 0:
			return False
		else:
			return True
	
	def parseGame(self):
		for move in self.second_game.mainline_moves():
			self.moves.append(str(move))
		counter = 1
		for item in range(0, len(self.moves)):
			# Black will be at odd positions starting from 1
			if self.check_odd(item):
				self.moves_assoc.append({ 'From': (self.moves[item][0] + self.moves[item][1]), 'To': (self.moves[item][2] + self.moves[item][3]), 'Color': 'Black', 'PGN': str(self.game.move(counter).black) } )
				counter = counter + 1

			#White will be at even positions starting from 0
			else:
				self.moves_assoc.append({ 'From': (self.moves[item][0] + self.moves[item][1]), 'To': (self.moves[item][2] + self.moves[item][3]), 'Color': 'White', 'PGN': str(self.game.move(counter).white) } )

		self.piece_names = ['R7','N6', 'B5', 'K4','Q3', 'B2', 'N1', 'R0', 'P15', 'P14', 'P13', 'P12', 'P11', 'P10', 'P9', 'P8','p55', 'p54', 'p53', 'p52', 'p51', 'p50', 'p49', 'p48','r63', 'n62', 'b61', 'k60', 'q59', 'b58', 'n57', 'r56']
			#['R0', 'N1', 'B2', 'Q3', 'K4', 'B5', 'N6', 'R7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'p48', 'p49', 'p50', 'p51', 'p52', 'p53', 'p54', 'p55', 'r56', 'n57', 'b58', 'q59', 'k60', 'b61', 'n62', 'r63' ]
		self.positions = ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1',
					 'a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2',
					 'a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7',
					 'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8'
					]

		#Setup the pieces
		for i in range(0,len(self.piece_names)):
			self.State.append(self.piece_move(self.piece_names[i], self.positions[i]))


	def err_print(self):
		print("Error!")

	#Function to get piece ID
	def get_piece_index(self, position):
		for i in range(0,len(self.State)):
			if self.State[i].position == position:
				return i

			else:
				pass


	def reset(self):
		for i in range(0,len(self.State)):
			self.State[i].position = self.positions[i]

	def getOccupancy(self, field):
		print("Occupancy check")
		print(field)
		x = self.get_piece_index(field)
		if x == None:
			print("empty")
			return False
		else:
			print(self.State[x].name)
			return True

	def getOccupant(self, field):
		x = self.get_piece_index(field)
		return self.State[x].name

	def getPiece(self, field, board):
		print("Occupancy check: " + str(field))
		tile = field.upper()
		piece = board.squares[globals()[tile]].frame
		print(piece)
		return piece
		pass

	def getOccupancyCV(self, field, board):
		print("Occupancy check: " + str(field))
		tile = field.upper()
		occu = board.squares[globals()[tile]].frame
		if occu == '':
			print("empty")
			return False
		else:
			print("Occupied")
			return True

	def getMoveCV(self, i, board):
		print("Parsing the " + str(i) + ('th move...'))
		fr = self.moves_assoc[i]['From']
		to = self.moves_assoc[i]['To']
		occupancy = self.getOccupancyCV(to, board)
		piece = self.getPiece(fr, board)
		if(occupancy):
			occupant = self.getPiece(to, board)
			return (piece + "," + to, 2, occupant)
		else:
			return (piece + "," + to, 1, None)

	def getMove(self, i):
		print("Parsing the " + str(i) + ('th move...'))
		fr = self.moves_assoc[i]['From']
		to = self.moves_assoc[i]['To']
		occupancy = self.getOccupancy(to)
		if(occupancy):
			occupant = self.getOccupant(to)
			x = self.get_piece_index(self.moves_assoc[i]['From'])
			self.State[x].position = self.moves_assoc[i]['To']
			return (self.State[x].name + "," + self.State[x].position, 2, occupant)
		else:
			x = self.get_piece_index(self.moves_assoc[i]['From'])
			self.State[x].position = self.moves_assoc[i]['To']
			return (self.State[x].name + "," + self.State[x].position, 1, None)



class Engine_Self_Game():
	def __init__(self, pondertime = 0.5, maxmoves = 10):
		# Variables for the engine
		self.engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
		self.pondertime = pondertime 
		self.maxmoves = maxmoves  
		self.color_dict = {True:'White',False:'Black'}
		self.board = chess.Board()
		self.moves_assoc ={} 
		self.quit = False

	def self_play(self):
		'''
		This function makes stockfish evaluate the board, generate a move and then extrats teh from, 
		to and color data from the move and returns a dictionary
		'''
		if not self.board.is_game_over() and self.board.fullmove_number<=self.maxmoves:
			result = self.engine.play(self.board,chess.engine.Limit(time=self.pondertime))
			self.board.push(result.move)
			self.moves_assoc = { 'From': (str(result.move)[0] + str(result.move)[1]), 'To': (str(result.move)[2] + str(result.move)[3]), 'Color': self.color_dict[self.board.turn]}
			return (self.moves_assoc)
			# print (self.moves_assoc)
		else:
			self.quit == True
			self.engine.quit()


	def Game(self):    
		'''
		This function uses the self_play function to make stockfish generate the move and extracts the information, which is then printed
		'''
	
		self.quit = False
		
		while self.quit == False:
			# Extract the current move in thef form of a dictionary
			x = self.self_play()
			
			# if isinstance(x,dict):
			# 	print(x)
			else:
				quit = True
				# print(board)
				self.engine.quit()

	


class Human_Engine_Game():
	def __init__(self, pondertime = 0.5, maxmoves = 10):
		# Variables for the engine
		self.engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
		self.pondertime = pondertime 
		self.maxmoves = maxmoves 
		self.color_dict = {True:'White',False:'Black'}
		self.board = chess.Board() 

	def Human_Play_uci(self):
		'''
		 This function makes the human enter a move from the console and executes it on the board through uci. The board is then printed
		'''
		print("Enter your move ")
		move_uci = str(input())
		
		if chess.Move.from_uci(move_uci) in self.board.legal_moves:
			self.board.push_uci(move_uci)
			moves_assoc = { 'From': (str(move_uci)[0] + str(move_uci)[1]), 'To': (str(move_uci)[2] + str(move_uci)[3]), 'Color': self.color_dict[self.board.turn] }
			# print(self.board)
		else:
			print("Illegal Move! Play again")
			self.Human_Play_uci()

	def Engine_Play(self):
		'''
		This function makes stockfish evaluate th board and generate teh move and then prints the board
		'''
		print("Engine's turn to play!")
		result = self.engine.play(self.board,chess.engine.Limit(time=self.pondertime))
		self.board.push(result.move)	
		moves_assoc = { 'From': (str(result.move)[0] + str(result.move)[1]), 'To': (str(result.move)[2] + str(result.move)[3]), 'Color': self.color_dict[self.board.turn] }
		
		# print(self.board)	

	
	def Game(self):
		'''
		This function uses the human and engine functions to play the game alternatively
		'''
		turn_var = False 

		print (self.board)
		
		while not self.board.is_game_over() and self.board.fullmove_number<=self.maxmoves:

			if turn_var == False :
				x = self.Human_Play_uci()
				turn_var = True 

			else:
				self.Engine_Play()
				turn_var = False
	
	def getPiece(self, field, board):
	'''
		This function returns the information of th pirce given the configuration of the physical board
	'''
		print("Occupancy check: " + str(field))
		tile = field.upper()
		piece = board.squares[globals()[tile]].frame
		print(piece)
		return piece
		pass

	def getOccupancyCV(self, field, board):
	'''
		This functions takes as input the state of the physical board and the position and returns true if the square is occupied, and false if
		it is not occupied
	'''
		print("Occupancy check: " + str(field))
		tile = field.upper()
		occu = board.squares[globals()[tile]].frame
		if occu == '':
			print("empty")
			return False
		else:
			print("Occupied")
			return True

	def getMoveCV(self, board):
	'''
		This function takes as input the physical board and uses the moves_assoc array to get the piece information. Using the piece information it queries 
		the physical board to return the information of the piece that needs to be moved and the type of maneuver
	'''
		turn_var = False 
		
		if not self.board.is_game_over() and self.board.fullmove_number<=self.maxmoves:

			if turn_var == False :
				self.Human_Play_uci()
				turn_var = True 

			else:
				self.Engine_Play()
				turn_var = False

			fr = self.moves_assoc['From']
			to = self.moves_assoc['To']
			occupancy = self.getOccupancyCV(to, board)
			piece = self.getPiece(fr, board)

			if(occupancy):
				occupant = self.getPiece(to, board)
				return (piece + "," + to, 2, occupant)
			else:
				return (piece + "," + to, 1, None)
			
		else:
			print(" ---------- End of Game -----------")
			return False
			self.engine.quit()


		

if __name__ == '__main__':

	ce  = Human_Engine_Game(1,20)
	# ce.Game()



	pass
