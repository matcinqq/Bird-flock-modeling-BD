import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap


def initialize_board(size, density=0.2):
    # Create an array with size = size, 1s distributed across array with prob. = 0.2 p = [no bird, bird]
    return np.random.choice([0, 1], size=size, p=[1 - density, density])


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


def decide_direction():
    # Randomly decide the direction of movement
    directions = ["N","S","W","E"]
    return np.random.choice(directions, size = 1)


def update_board(board):
    new_board = np.copy(board)
    size_x, size_y = board.shape
    for x in range(size_x):
        for y in range(size_y):
            count = count_neighbors(board, x, y)
            if board[x, y] == 1:
                direction = decide_direction()
                if direction == "N" and y+1 < size_y and board[x,y+1] == 0:
                    new_board[x,y] = 0
                    new_board[x,y+1] = 1
                elif direction == "S" and y-1 >= 0 and board[x,y-1] == 0:
                    new_board[x,y] = 0
                    new_board[x,y-1] = 1
                elif direction == "W" and x-1 >= 0 and board[x-1,y] == 0:
                    new_board[x,y] = 0
                    new_board[x-1,y] = 1
                elif direction == "E" and x+1 < size_x and board[x+1,y] == 0:
                    new_board[x,y] = 0
                    new_board[x+1,y] = 1

        # Preventing colisions in code, should add that if they collide they die next.
    return new_board


def update(frame, img, board):
    # Update the whole board, [:] means in place,
    board[:] = update_board(board)
    img.set_array(board)
    return img


def visualize_game(size=(50, 50), density=0.2, frames=100, interval=100):
    board = initialize_board(size, density)
    fig, ax = plt.subplots() # ini plot for board
    img = ax.imshow(board, cmap=ListedColormap(['black', 'white'])) # img for animation
    ani = animation.FuncAnimation(fig, update, fargs=(img, board), frames=frames, interval=interval) # update - func each frame, fargs - args for update
    plt.show()

# Run the visualization
visualize_game()