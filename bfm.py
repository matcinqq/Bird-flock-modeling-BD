import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
import random as rd


class Bird:
    def __init__(self, y, x):
        self.x = x  # position
        self.y = y
        self.position = (y, x)
        self.direction = (0, 0)  # direction of movement


class Leader:  # unused
    def __init__(self, size):
        self.y = size[0]//2
        self.x = size[1]//2

    def get_leader_position(self):
        return self.y, self.x

    def move(self, board_size):
        self.y = (self.y + 1) % board_size[0]


def initialize_board(size, bird_count):
    # create board and birds
    birds = []
    for i in range(bird_count):
        birds.append(Bird(np.random.randint(0, size[0]),(np.random.randint(0, size[1]))))
    # birds placed on board, birds = list of bird objects with set position
    board = np.zeros(shape=size, dtype=int)
    for c in birds:
        y, x = c.position
        board[y, x] = 1
    return birds, board


def movement_forces(bird, birds):
    separation = (0, 0)
    coheision = (0, 0)
    alignment = (0, 0)

    neighbors = []  # list of neighbors
    radius = 3  # radius of "vision", how far away neihbors can be

    # get neigbors
    for neighbor in birds:
        if neighbor == bird:
            continue  # don't count the bird itself

        neighbor_diff_y = neighbor.position[0] - bird.position[0]
        neighbor_diff_x = neighbor.position[1] - bird.position[1]

        if abs(neighbor_diff_y) <= radius and abs(neighbor_diff_x) <= radius:  # check if other birds in radius range
            neighbors.append(neighbor)

    # separation
    separation_y = 0
    separation_x = 0
    if neighbors:
        for neighbor in neighbors:
            # change separation to store value, will normalize later
            separation_y = separation[0] + (bird.position[0] - neighbor.position[0])  # move away from neigbor
            separation_x = separation[1] + (bird.position[1] - neighbor.position[1])
        separation = (np.sign(separation_y), np.sign(separation_x))  # normalize to (-1,1)
    else:
        separation = (0, 0)

    #  coheision
    all_y = []
    all_x = []
    for i in birds:  # add all neigbor positions to list
        all_y.append(i.position[0])
        all_x.append(i.position[1])
    avg_y = round(sum(all_y)/len(all_y))  # average neighbor position
    avg_x = round(sum(all_x)/len(all_x))
    diff_y = avg_y - bird.position[0]
    diff_x = avg_x - bird.position[1]
    coheision = (np.sign(diff_y), np.sign(diff_x))  #
    # alignment

    neighbors_y = []
    neighbors_x = []
    margin = 5  # margin where average is not calculated, avoid wraparound issues
    if neighbors:
        for neighbor in neighbors:
            if neighbor == bird:
                continue
            neighbors_y.append(neighbor.direction[0])
            neighbors_x.append(neighbor.direction[1])
        if neighbors_y:
            neighbor_avg_y = round(sum(neighbors_y)/len(neighbors_y))
            neighbor_avg_x = round(sum(neighbors_x)/len(neighbors_x))
            alignment = (np.sign(neighbor_avg_y), np.sign(neighbor_avg_x))
    # sum of forces
    sum_y = 1.2 * separation[0] + coheision[0] + alignment[0]
    sum_x = 1.2 * separation[1] + coheision[1] + alignment[1]
    # normalize with sign func.
    step_y = int(np.sign(sum_y))
    step_x = int(np.sign(sum_x))

    if step_x != 0 and step_y != 0:
        bird.direction = step_y, step_x
    else:
        bird.direction = (np.random.randint(-1,1), np.random.randint(-1,1))
    return bird.direction


def update_board(board, birds):
    new_board = np.copy(board)
    size_y, size_x = board.shape
    for bird in birds:  # updating movement of birds
        y, x = bird.position
        movement_forces(bird, birds)
        y_move, x_move = bird.direction

        # calc new positions, looping board, update object's position value
        new_y = (y+y_move) % size_y
        new_x = (x+x_move) % size_x
        bird.position = new_y, new_x

        # clear old positon, place in new position
        new_board[y, x] = 0
        new_board[new_y, new_x] = 1

    return new_board, birds


def update(frame, img, board, birds):
    # Update the whole board, [:] means in place,
    board[:], birds = update_board(board, birds)
    img.set_array(board)
    print(len(birds))
    return img


def visualize_game(size=(120, 120), bird_count=60, frames=500, interval=0):
    birds, board = initialize_board(size, bird_count)
    fig, ax = plt.subplots()  # ini plot for board

    # img for animation, vmax vmin required for 3 colors.
    img = ax.imshow(board, cmap=ListedColormap(['black', 'white']), origin='lower', vmin = 0, vmax = 2)

    # update - func each frame, fargs - args for update
    ani = animation.FuncAnimation(fig, update, fargs=(img, board, birds), frames=frames, interval=interval)
    plt.show()


# Run the visualization
visualize_game()

"""
separation: done(?)

alignment: 

coheision:
all birds, get average "cell" of all birds, move towards it

also do optimization (laterrrrr)

movement works, update above

also need to find a way to normalize movement vector so x and y are between -1 and 1


"""