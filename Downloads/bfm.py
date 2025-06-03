import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
import statistics as st
import random as rd
import pygame
import math

pygame.init()

# Pygame general setup
width, height = 1200, 800
hex_size = 15
background_color = (0, 0, 0) # white
hex_color = background_color # not visible, same as background
grid_color = (10, 10, 10)
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
clock = pygame.time.Clock()


class Bird:
    def __init__(self, col, row):
        self.parity = 0
        self.col = col  # position
        self.row = row
        self.position = (col, row)
        self.direction = (0, 0)  # direction of movement

    def update_position(self, col, row):
        self.col = col
        self.row = row
        self.position = (col, row)

    def parity(self):
        if self.col&1 == 0: # even
            self.parity = 0
        elif self.col&1 != 0: # odd
            self.parity = 1


def find_best_hex(dx, dy, possible_hexes):  # find best hex where bird can move
    possible_hexes_cube = []
    vx, vy, vz = offset_to_cube(dx, dy)
    for i in possible_hexes:
        x, y, z = offset_to_cube(i[0], i[1])
        possible_hexes_cube.append([x, y, z])
    best_dir = (0, 0, 0)
    best_score = float('-inf')

    for hex in possible_hexes_cube:
        score = vx * hex[0] + vy * hex[1] + vz * hex[2] # dot product
        if score > best_score:
            best_score = score
            best_hex = hex
    return best_hex


def decide_move_dir(bird):  # find possible hexes where bird can move
    if bird.parity == 0:
        possible_hexes = [[+1,  0], [ 0, -1], [-1, -1], [-1,  0], [-1, +1], [ 0, +1]]
    elif bird.parity == 1:
        possible_hexes = [[+1,  0], [+1, -1], [ 0, -1], [-1,  0], [ 0, +1], [+1, +1]]
    return possible_hexes


def oddr_offset_to_pixel(col, row):
    x = hex_size * math.sqrt(3) * (col+0.5*(row&1))
    y = hex_size * 3/2 * row
    return int(x), int(y)


def offset_to_cube(col, row):
    x = col - (row - (row & 1)) // 2 # & -> bitwise and (like mod but works with negative nums too)
    z = row
    y = -x-z
    return x, y, z


def cube_to_offset(x, y, z):
    y = int(y)
    # z is the original offset-row
    row = z
    col = x + ((z - (z & 1)) // 2)
    return col, row


def draw_hex(surface, center, size, color, width=3):
    # drawing a single hexagon
    x, y = center
    points = []
    for i in range(6):
        angle_deg = 60*i-30
        angle_rad = math.radians(angle_deg)
        dx = x + size * math.cos(angle_rad)
        dy = y + size * math.sin(angle_rad)
        points.append((dx, dy))
    pygame.draw.polygon(surface, color, points, width)


def draw_hex_map(surface, hex_size):
    screen.fill((0, 0, 0))  # for resize, clear old hexes
    # drawing the full map of hexagons

    # how many hexes will fit on the screen
    global hex_width, hex_height, v_spacing, h_spacing, rows, cols
    hex_width = math.sqrt(3)*hex_size
    hex_height = 2*hex_size
    v_spacing = 3/4*hex_height
    h_spacing = hex_width

    # amount of rows and columns to fill with hexes
    rows = int((screen.get_size()[1])//v_spacing)  # height of scalable screen
    cols = int((screen.get_size()[0])//h_spacing)  # width of scalable screen

    # draw hexes with px, py pixel offset using draw_hex for each - suprisingly fast
    for row in range(rows):
        for col in range(cols):
            px, py = oddr_offset_to_pixel(col, row)
            py += hex_size
            px += hex_size
            if px < (screen.get_size()[0]) and py < (screen.get_size()[1]):
                draw_hex(surface, (px, py), hex_size, grid_color)


def initialize_board(cols, rows, bird_count):
    birds = []

    center_col = cols // 2  # cols, rows around center of board
    center_row = rows // 2
    radius = 4  # how far from center the birds can be placed, !find good value later!

    # place birds around the center of the board, !should change to consider amount of birds!
    for i in range(bird_count):
        col = np.clip(np.random.randint(center_col - radius, center_col + radius + 1), 0, cols - 1) # clip - if
        row = np.clip(np.random.randint(center_row - radius, center_row + radius + 1), 0, rows - 1)
        birds.append(Bird(col, row))

    return birds


def get_neighbors(bird, birds, radius = 10):  # w/ sliding window i think?; Radius - "vision" radius, vey
    bird_col, bird_row = bird.position
    x, y, z = offset_to_cube(bird_col, bird_row)

    neighbors_pos = []

    for dx in range(-radius, radius+1):  # for hex grid with radius consideration, copied - figure out or rewrite
        for dy in range(-radius, radius+1):
            dz = -dx-dy
            if abs(dz) > radius:
                continue
            nx, ny, nz = x+dx, y+dy, z+dz
            ncol, nrow = cube_to_offset(nx, ny, nz)
            ncol %= cols
            nrow %= rows
            neighbors_pos.append((ncol, nrow))

    neighbors = []
    for possible_neighbor in birds:
        if possible_neighbor.position in neighbors_pos and possible_neighbor != bird:  # if neighb. not THE bird
            neighbors.append(possible_neighbor)
    return neighbors


def movement_forces(bird, birds):
    # setup
    separation = (0, 0)
    cohesion = (0, 0)
    alignment = (0, 0)
    neighbors = get_neighbors(bird, birds)

    # Separation
    bird_x, bird_y = bird.position
    if neighbors:
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor.position
            if abs(bird_x - neighbor_x) >= 3 or abs(bird_y - neighbor_y) >= 3:  # primitive - just with a lot of if statements
                separation = ((separation[0] + (bird_x - neighbor_x)), (separation[1] + (bird_y - neighbor_y)))
            elif abs(bird_x - neighbor_x) == 2 or abs(bird_y - neighbor_y) == 2:
                separation = 2*((separation[0] + (bird_x - neighbor_x)), (separation[1] + (bird_y - neighbor_y)))
            elif abs(bird_x - neighbor_x) <= 1 or abs(bird_y - neighbor_y) <= 1:
                separation = 3*((separation[0] + (bird_x - neighbor_x)), (separation[1] + (bird_y - neighbor_y)))

    # Cohesion (neighbors, weighed [wip])
    neighbor_pos_x = []
    neighbor_pos_y = []
    if neighbors:
        for i in neighbors:  # add all neigbor positions to list
            neighbor_pos_x.append(i.position[0])
            neighbor_pos_y.append(i.position[1])
        avg_x = sum(neighbor_pos_x)/len(neighbor_pos_x)
        avg_y = sum(neighbor_pos_y)/len(neighbor_pos_y)  # average neighbor position
        diff_x = avg_x - bird.position[0]
        diff_y = avg_y - bird.position[1]
        cohesion = (int(diff_x), int(diff_y))
    else:
        cohesion = (np.random.randint(-1, 2), np.random.randint(-1, 2))

    # Alignment
    neighbors_y = []
    neighbors_x = []
    if neighbors:
        for neighbor in neighbors:
            neighbors_x.append((neighbor.direction[0]))
            neighbors_y.append((neighbor.direction[1]))
        if neighbors_x:  # check average direction of neighb. and make it birds direction
            avg_dx = sum(neighbors_x) / len(neighbors_x)
            avg_dy = sum(neighbors_y) / len(neighbors_y)
            alignment = (int(avg_dx), int(avg_dy))

    sum_x = 2*separation[0] + 5*cohesion[0] + 7*alignment[0]  # sep > 4, coh > 3 works decently
    sum_y = 2*separation[1] + 5*cohesion[1] + 7*alignment[1]

    # randomness in movement
    random_chance = np.random.randint(0,50)
    if random_chance == 1:
        sum_x = np.random.randint(-2, 2)
        sum_y = np.random.randint(-2, 2)

    # normalize wi func.

    possible_hexes = decide_move_dir(bird)
    best_hex = find_best_hex(sum_x, sum_y, possible_hexes)
    move_x, move_y = cube_to_offset(*best_hex)
    step = (move_x, move_y)
    bird.direction = step
    return step


def update_board(birds):
    occupied_tiles = {bird.position for bird in birds}
    new_positions = set()

    for bird in birds:  # updating movement of birds
        x, y = bird.position
        x_move, y_move = movement_forces(bird, birds)
        # calc new positions, looping board, update object's position value
        new_y = (y+y_move) % rows
        new_x = (x+x_move) % cols
        new_position = (new_x, new_y)

        if new_position not in occupied_tiles and new_position not in new_positions:
            bird.update_position(new_x, new_y)
            new_positions.add(new_position)

    return birds


# Create birds and board
draw_hex_map(screen, hex_size) # just to draw birds, need globabl variables
birds = initialize_board(cols, rows, bird_count=20)
board = np.zeros((rows, cols))

running = True
while running:
    screen.fill(background_color)
    draw_hex_map(screen, hex_size)

    # Update bird positions
    birds = update_board(birds)

    for bird in birds:
        px, py = oddr_offset_to_pixel(bird.col, bird.row)

        # testing detection neighbors - if bird is red, it's a neighbor of another
        neighbors = get_neighbors(bird, birds)
        for neighbor in neighbors:
            pxz, pyz = oddr_offset_to_pixel(neighbor.col, neighbor.row)
            pxz += hex_size
            pyz += hex_size
            pygame.draw.circle(screen, (212, 8, 25), (pxz, pyz), (0.60*hex_size))

        px += hex_size
        py += hex_size
        pygame.draw.circle(screen, (134, 116, 181), (px, py), (0.60*hex_size))  # can change size but looks good

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:  # resizable window, map size updating not working
            #old_screen = screen
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    pygame.display.flip()
    clock.tick(1000)  # lower speed to observe motion
    print(clock.get_fps())

pygame.quit()

"""
to do:

figure out if it works correctly

find good values for forces

figure out or rewrite finding neighbors

optimization

add barriers or nests or smn
"""