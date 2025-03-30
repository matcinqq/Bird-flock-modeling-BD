import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap


class Leader:
    def __init__(self, size):
        self.y = size[0]//2
        self.x = size[1]//2

    def get_leader_position(self):
        return self.y, self.x

    def move(self, board_size):
        self.y = (self.y + 1) % board_size[0]


class Food:
    pass


def initialize_board(size, density=0.2):
    board = np.random.choice([0, 1], size=size, p=[1 - density, density])
    leader = Leader(size)
    board[leader.y, leader.x] = 2
    return board, leader


def count_neighbors(board, x, y):
    # Relative positions of neighbours
    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),         (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

    count = 0 # Count neighbours

    # Specific positions of neighbours around checked cell
    for dx, dy in neighbors:
        nx, ny = x + dx, y + dy
        if 0 <= nx < board.shape[0] and 0 <= ny < board.shape[1]:
            count += board[nx, ny]  # Add amount of neighbours
    return count


def decide_direction(bird_y, bird_x, leader):
    # Randomly decide the direction of movement
    leader_y, leader_x = leader.get_leader_position()
    directions = ["N", "S", "W", "E"]
    weights = [1, 1, 1, 1]
    leader_strenght = 1

    if leader_y > bird_y: # leader up from bird, higher probability to move north
        weights[0] = weights[0] + leader_strenght
    elif leader_y < bird_y: # leader down from bird, higher probability to move south
        weights[1] = weights[1] + leader_strenght

    if leader_x > bird_x: # leader right from bird, higher probability to move east
        weights[3] = weights[3] + leader_strenght
    elif leader_x < bird_x: # leader left from bird, higher probability to move west
        weights[2] = weights[2] + leader_strenght

    weights = np.array(weights)/sum(weights) # normalize to sum = 1, needed for probability calculation
    return np.random.choice(directions, size=1, p=weights)


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
                direction = decide_direction(y, x, leader)
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


def visualize_game(size=(150, 150), density=0.05, frames=100, interval=50):
    board, leader = initialize_board(size, density)
    fig, ax = plt.subplots() # ini plot for board
    img = ax.imshow(board, cmap=ListedColormap(['black', 'white', 'red']), origin = 'lower', vmin = 0, vmax = 2) # img for animation, vmax vmin required for 3 colors.
    #ax.invert_xaxis()
    ani = animation.FuncAnimation(fig, update, fargs=(img, board, leader), frames=frames, interval=interval) # update - func each frame, fargs - args for update
    plt.show()
# Run the visualization
visualize_game()