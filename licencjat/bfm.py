import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
import random as rd

class Leader:
    def __init__(self, size):
        self.y = size[0]//2
        self.x = size[1]//2

    def get_leader_position(self):
        return self.y, self.x

    def move(self, board_size):
        self.y = (self.y + 1) % board_size[0]


def initialize_board(size, density=0.2):
    board = np.random.choice([0, 1], size=size, p=[1 - density, density])
    print(type(board))
    leader = Leader(size)
    board[leader.y, leader.x] = 2
    return board, leader


def count_neighbors(board, x, y):
    # Relative positions of neighbours
    neighbors = [
    (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
    (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2),
    (0, -2), (0, -1),            (0, 1), (0, 2),
    (1, -2), (1, -1), (1, 0), (1, 1), (1, 2),
    (2, -2), (2, -1), (2, 0), (2, 1), (2, 2),
    ]

    count = 0 # Count neighbours

    # Specific positions of neighbours around checked cell
    for dx, dy in neighbors:
        nx, ny = (x + dx) % board.shape[1], (y + dy) % board.shape[0]
        if board[ny, nx] == 1:
            count += 1
    return count

val = [[],[],[],[],[],[],[]]


def decide_direction(bird_y, bird_x, leader, board):
    # Randomly decide the direction of movement
    leader_y, leader_x = leader.get_leader_position()
    directions = ["N", "S", "W", "E"]
    weights = [1, 1, 1, 1]
    leader_strength = 5
    repulsion = 60
    near_repulsion = 100
    coheision_strength = 0.5

    if leader_y > bird_y: # leader up from bird, higher probability to move north
        weights[0] = weights[0] + leader_strength

    elif leader_y < bird_y: # leader down from bird, higher probability to move south
        weights[1] = weights[1] + leader_strength

    if leader_x > bird_x: # leader right from bird, higher probability to move east
        weights[3] = weights[3] + leader_strength
    elif leader_x < bird_x: # leader left from bird, higher probability to move west
        weights[2] = weights[2] + leader_strength

    # cone of vision in front of bird
    neighbors = [
        (-3, -3), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-3, 3),
                  (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2),
                  (0, -2),  (0, -1),           (0, 1),  (0, 2),
                            (1, -1),  (1, 0),  (1, 1)
    ]
    neighbors_pos = []

    # Specific positions of neighbours around checked cell
    for dx, dy in neighbors:
        nx, ny = (bird_x + dx) % board.shape[1], (bird_y + dy) % board.shape[0]
        if board[ny, nx] == 1:
            neighbors_pos.append((dy, dx))

    if neighbors_pos: #if list not empty
        neighbors_pos_sort = sorted(neighbors_pos, key=lambda tup: np.sqrt(tup[0]**2 + tup[1]**2)) # get nearest bird, euclidean distance

        if neighbors_pos_sort[0] in [neighbors[0], neighbors[1], neighbors[7]]:
            val[0].append(0)
            # closest neighbour at (-3, -3), (-2,-2), (-1,-2): move S or E
            weights[1] = weights[1] + repulsion
            weights[3] = weights[3] + repulsion

        if neighbors_pos_sort[0] in [neighbors[2], neighbors[3], neighbors[4]]:
            val[1].append(1)
            # closest neighbour at (-2, -1), (-2, 0) move S
            weights[1] = weights[1] + repulsion

        if neighbors_pos_sort[0] in [neighbors[5], neighbors[6]]:
            # closest neighbour at (-2, 2), (-3, 3), (-1, 2): move S or W
            weights[1] = weights[1] + repulsion
            weights[2] = weights[2] + repulsion
            val[2].append(2)

        if neighbors_pos_sort[0] in [neighbors[8], neighbors[12], neighbors[13]]:
            # closest neighbour at (-1, -1), (0,-1): move E
            weights[3] = weights[3] + near_repulsion
            val[3].append(3)

        if neighbors_pos_sort[0] in [neighbors[10], neighbors[11], neighbors[14], neighbors[15]]:
            # closest neighbour at (-1, 1), (0,1): move W
            weights[2] = weights[2] + near_repulsion
            val[4].append(4)

        if neighbors_pos_sort[0] == (-1, 0):
            #when bird above move down
            weights[0] = weights[0] + near_repulsion # 1->0
            val[5].append(5)

        if neighbors_pos_sort[0] in [neighbors[16], neighbors[17], neighbors[18]]:
            #when bird below move up
            weights[1] = weights[1] + near_repulsion # 0 -> 1
            val[6].append(6)
        print(
            f"0:{len(val[0])}, 1:{len(val[1])}, 2:{len(val[2])}, 3:{len(val[3])}, 4:{len(val[4])}, 5:{len(val[5])}, 6:{len(val[6])}")
    y_active, x_active = np.where(board == 1) # find birds
    avg_y = int(round(sum(y_active)/len(y_active), 0))
    avg_x = int(round(sum(x_active)/len(x_active), 0))

    if bird_y - avg_y > 0:
        # bird above avg, move S
        weights[1] = weights[1] + coheision_strength

    if bird_y - avg_y < 0:
        # bird below avg, move N
        weights[0] = weights[0] + coheision_strength

    if bird_x - avg_x > 0:
        # bird right of avg, move W
        weights[2] = weights[2] + coheision_strength

    if bird_x - avg_x < 0:
        #bird left of avg, move E
        weights[3] = weights[3] + coheision_strength

    weights = np.array(weights)/sum(weights) # normalize to sum = 1, needed for probability calculation
    return np.random.choice(directions, size=1, p=weights)


def calc_dist(bird_y, bird_x, food_list):
    dist = 1000 # placeholder, some very large number idk how to do it well
    for i in range(len(food_list)):
        dist_new = np.linalg.norm(np.array([bird_y,bird_x])-food_list[i])
        if dist_new < dist:
            dist = dist_new
    # not used, kept for future
    return dist


def update_board(board, leader):
    new_board = np.copy(board)
    size_x, size_y = board.shape

    leader.move((size_y, size_x))
    new_board[:, :] = np.where(new_board == 2, 0, new_board)  # Clear old director position

    if leader.y < size_y and leader.x < size_x:
        new_board[leader.y, leader.x] = 2  # Place director in new position

    for y in range(size_y):  # Start with y as the vertical axis (rows)
        for x in range(size_x):  # x as the horizontal axis (columns)
            count = count_neighbors(board, x, y)
            if board[y, x] == 1:  # Access the board with flipped coordinates
                direction = decide_direction(y, x, leader, board)
                if direction == "N":
                    new_y = (y+1) % size_y
                    if new_board[new_y, x] != 1:
                        new_board[y, x] = 0
                        new_board[new_y, x] = 1
                if direction == "S":
                    new_y = (y - 1) % size_y
                    if new_board[new_y, x] != 1:
                        new_board[y, x] = 0
                        new_board[new_y, x] = 1
                elif direction == "W":
                    new_x = (x - 1) % size_x
                    if new_board[y, new_x] != 1:
                        new_board[y, x] = 0
                        new_board[y, new_x] = 1
                elif direction == "E":
                    new_x = (x + 1) % size_x
                    if new_board[y, new_x] != 1:
                        new_board[y, x] = 0
                        new_board[y, new_x] = 1
        # Preventing colisions in code, maybe add chance to reproduce if they collide idk

    return new_board


def update(frame, img, board, leader):
    # Update the whole board, [:] means in place,
    board[:] = update_board(board, leader)
    img.set_array(board)
    return img


def visualize_game(size=(80, 80), density=0.02, frames=100, interval=30):
    board, leader = initialize_board(size, density)
    fig, ax = plt.subplots() # ini plot for board
    img = ax.imshow(board, cmap=ListedColormap(['black', 'red', 'white', 'purple']), origin = 'lower', vmin = 0, vmax = 2)  # img for animation, vmax vmin required for 3 colors.
    ani = animation.FuncAnimation(fig, update, fargs=(img, board, leader), frames=frames, interval=interval)  # update - func each frame, fargs - args for update
    plt.show()


# Run the visualization
visualize_game()

"""
separation: done(?)

alignment: 

coheision:
all birds, get average "cell" of all birds, move towards it

also do optimization
"""