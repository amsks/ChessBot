def create_board():
    abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    black = '[.1 .1 .1]'
    white = '[.9 .9 .9]'
    size = 0.06
    height = 0.1

    f = open("../scenarios/chessBoard.g", "w+")
    for i in range(8):
        for j in range(8):
            if (i+j) % 2:
                color = white
            else:
                color = black
            position = '(' + str(-3.5*size + j*size) + ' ' + str(3.5*size - i*size) + ' .7)'
            f.write(
                abc[i] + str(j+1) + ' (world){\n' +
                '\tshape:ssBox, Q:<t' + position + '>, size:[.06 .06 ' + str(height) + ' .0001], color:' + color + '\n' +
                '\tmass:2.0\n' +
                '\tcontact, logical:{ }\n' +
                '\tfriction:.1\n' +
                '}\n'
            )
    f.close()


def create_pieces():
    black = '[.0 .0 .0]'
    white = '[1. 1. 1.]'
    counter = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]
    square_size = 0.06
    height = 0.03
    diameter = 0.01
    pieces = 'RNBQKBNRPPPPPPPP8888pppppppprnbqkbnr'
    ind = 0
    p_ind = 0
    piece = None
    f = open('../scenarios/pieces.g', 'w+')
    for c in pieces:
        if c.isnumeric():
            ind += int(c)
            continue
        if c == 'P':
            piece = pawn
            p_ind = counter[0][0]
            counter[0][0] += 1
        elif c == 'R':
            piece = rook
            p_ind = counter[0][1]
            counter[0][1] += 1
        elif c == 'N':
            piece = knight
            p_ind = counter[0][2]
            counter[0][2] += 1
        elif c == 'B':
            piece = bishop
            p_ind = counter[0][3]
            counter[0][3] += 1
        elif c == 'K':
            piece = king
            p_ind = counter[0][4]
            counter[0][4] += 1
        elif c == 'Q':
            piece = queen
            p_ind = counter[0][5]
            counter[0][5] += 1
        elif c == 'p':
            piece = pawn
            p_ind = counter[1][0]
            counter[1][0] += 1
        elif c == 'r':
            piece = rook
            p_ind = counter[1][1]
            counter[1][1] += 1
        elif c == 'n':
            piece = knight
            p_ind = counter[1][2]
            counter[1][2] += 1
        elif c == 'b':
            piece = bishop
            p_ind = counter[1][3]
            counter[1][3] += 1
        elif c == 'k':
            piece = king
            p_ind = counter[1][4]
            counter[1][4] += 1
        elif c == 'q':
            piece = queen
            p_ind = counter[1][5]
            counter[1][5] += 1
        shape = piece.get("shape")
        size = piece.get("size")
        if c.isupper():
            color = white
        else:
            color = black
        i = ind // 8
        j = ind % 8
        position = '(' + str(-3.5 * square_size + i * square_size) + ' ' + str(-3.5 * square_size + j * square_size) + ' .77)'
        pose = '[' + str(-3.5 * square_size + i * square_size) + ', ' + str(3.5 * square_size - j * square_size) + ', .9, 0, 0, 0, 1]'
        f.write(
            c + '_' + str(p_ind) + '\t{  shape:' + shape +', size:[' + size + '], color:' + color + ', mass: 0.02 X:<' + pose + ', friction:.1> }\n'
            # c + str(ind) + ' (world){\n' +
            # '\tshape:cylinder, Q:<t' + position + '>, size:[' + str(height) + ' .01], color:' + color + '\n' +
            # '\tcontact, logical:{ }\n' +
            # '\tfriction:.1\n' +
            # '}\n'
        )

        ind += 1


pawn = {
    "name": "p",
    "shape": "cylinder",
    "size": "0.03, 0.01"
}

rook = {
    "name": "r",
    "shape": "box",
    "size": "0.025, 0.025, 0.04",
}

knight = {
    "name": "n",
    "shape": "box",
    "size": "0.015, 0.025, 0.035",
}

bishop = {
    "name": "b",
    "shape": "cylinder",
    "size": "0.035, 0.012"
}

king = {
    "name": "k",
    "shape": "cylinder",
    "size": "0.05, 0.014"
}

queen = {
    "name": "q",
    "shape": "cylinder",
    "size": "0.04, 0.014"
}

if __name__ == '__main__':
    # create_board()
    create_pieces()
