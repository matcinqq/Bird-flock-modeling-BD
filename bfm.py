import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
import statistics as st
import random as rd
import pygame
import math
import pygame_textinput

pygame.init()

# Pygame general setup
width, height = 1200, 800
hex_size = 5
background_color = (0, 0, 0) # white
hex_color = background_color # not visible, same as background
grid_color = (50, 10, 10)
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
clock = pygame.time.Clock()
sim_surf = pygame.surface.Surface((width*(4/5), height))
hex_surf = pygame.surface.Surface((width*(4/5), height))


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
    global cols, rows
    # drawing the full map of hexagons

    # how many hexes will fit on the screen
    global hex_width, hex_height, v_spacing, h_spacing, rows, cols
    hex_width = math.sqrt(3)*hex_size
    hex_height = 2*hex_size
    v_spacing = 3/4*hex_height
    h_spacing = hex_width

    # amount of rows and columns to fill with hexes
    rows = int((surface.get_size()[1])//v_spacing)  # height of scalable screen
    cols = int((surface.get_size()[0])//h_spacing)  # width of scalable screen

    # draw hexes with px, py pixel offset using draw_hex for each - suprisingly fast
    for row in range(rows):
        for col in range(cols):
            px, py = oddr_offset_to_pixel(col, row)
            py += hex_size
            px += hex_size
            if px < (surface.get_size()[0]) and py < (surface.get_size()[1]):
                draw_hex(surface, (px, py), hex_size, grid_color)


def initialize_board(cols, rows, bird_count):
    birds = []

    center_col = cols // 2  # cols, rows around center of board
    center_row = rows // 2
    spawn_radius = 4  # how far from center the birds can be placed, !find good value later!

    # place birds around the center of the board, !should change to consider amount of birds!
    for i in range(bird_count):
        col = np.clip(np.random.randint(center_col - spawn_radius, center_col + spawn_radius + 1), 0, cols - 1) # clip - if
        row = np.clip(np.random.randint(center_row - spawn_radius, center_row + spawn_radius + 1), 0, rows - 1)
        birds.append(Bird(col, row))

    return birds


def get_neighbors(bird, birds, radius = 5):  # w/ sliding window i think?; Radius - "vision" radius, vey
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


def movement_forces(bird, birds, radius):
    # setup
    separation = (0, 0)
    cohesion = (0, 0)
    alignment = (0, 0)
    neighbors = get_neighbors(bird, birds, radius)

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

    sum_x = sep_force*separation[0] + coh_force*cohesion[0] + alig_force*alignment[0]  # sep > 4, coh > 3 works decently
    sum_y = sep_force*separation[1] + coh_force*cohesion[1] + alig_force*alignment[1]

    # randomness in movement
    random_chance = np.random.randint(0,10)
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
        x_move, y_move = movement_forces(bird, birds, radius)
        # calc new positions, looping board, update object's position value
        new_y = (y+y_move) % rows
        new_x = (x+x_move) % cols
        new_position = (new_x, new_y)

        if new_position not in occupied_tiles and new_position not in new_positions:
            bird.update_position(new_x, new_y)
            new_positions.add(new_position)

        else:
            new_y = y + np.random.randint(-1,1) % rows
            new_x= x + np.random.randint(-1,1) % cols
            new_position = (new_x, new_y)
            bird.update_position(new_x, new_y)
            new_positions.add(new_position)


    return birds


# Create birds and board
draw_hex_map(hex_surf, hex_size) # just to draw birds, need globabl variables
birds = initialize_board(cols, rows, bird_count=20)
board = np.zeros((rows, cols))

# setup forces
sep_force = 2
coh_force = 5
alig_force = 7
radius = 10

# create input boxes and text
textinput = pygame_textinput.TextInputVisualizer()
text_surf = pygame.surface.Surface((width*(1/5), height))

text_1 = pygame.font.SysFont("arialunicode", 30)
text_2 = pygame.font.SysFont("arialunicode", 20)

text_surf.fill((89, 97, 43))
sim_surf.set_colorkey((255, 0, 255))
running = True
needs_redraw = True
while running:
    text_surf.fill((89, 97, 43))
    # create text boxes
    text_separation = text_1.render(f"Separation = {sep_force}", False, (255, 255, 255))
    text_cohesion = text_1.render(f"Cohesion = {coh_force}", True, (255, 255, 255))
    text_alignment = text_1.render(f"Alignment = {alig_force}", True, (255, 255, 255))
    text_radius = text_1.render(f"Radius = {radius}", True, (255, 255, 255))

    text_add_sep = text_2.render('Add 1', False, (255, 255, 255))
    text_rm_sep = text_2.render('Remove 1', False, (255, 255, 255))

    text_add_coh = text_2.render('Add 1', False, (255, 255, 255))
    text_rm_coh = text_2.render('Remove 1', False, (255, 255, 255))

    text_add_align = text_2.render('Add 1', False, (255, 255, 255))
    text_rm_align = text_2.render('Remove 1', False, (255, 255, 255))

    text_add_radius = text_2.render('Add 1', False, (255, 255, 255))
    text_rm_radius = text_2.render('Remove 1', False, (255, 255, 255))

    # separation, buttons and text
    text_surf.blit(text_separation, (0, 0*height))
    text_surf.blit(text_add_sep, (0, (0*height)+50))
    text_surf.blit(text_rm_sep, ((width*(1/5))-100, (0*height)+50))  # width is absolute not relative to surface here

    # cohesion, buttons and text
    text_surf.blit(text_cohesion, (0,(1/5)*height))
    text_surf.blit(text_add_coh, (0, (1/5)*height+50))
    text_surf.blit(text_rm_coh, ((width*(1/5))-100, (1/5)*height+50))

    # alignment, buttons and text
    text_surf.blit(text_alignment, (0, (2/5)*height))
    text_surf.blit(text_add_align, (0, (2/5)*height+50))
    text_surf.blit(text_rm_align, ((width*(1/5))-100, (2/5)*height+50))

    # radius buttons and text
    text_surf.blit(text_radius, (0, (3 / 5) * height))
    text_surf.blit(text_add_radius, (0, (3 / 5) * height + 50))
    text_surf.blit(text_rm_radius, ((width * (1 / 5)) - 100, (3 / 5) * height + 50))

    # create other objects on screen
    screen.blit(text_surf, (width*(4/5), 0))
    text_surf.blit(textinput.surface,(0, 10))
    sim_surf.fill((0, 0, 0))
    sim_surf.blit(hex_surf, (0, 0))

    if needs_redraw:
        draw_hex_map(hex_surf, hex_size)
        needs_redraw = False

    # clear old board
    sim_surf.fill((0,0,0))
    sim_surf.blit(hex_surf,(0,0))

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
            pygame.draw.circle(sim_surf, (212, 8, 25), (pxz, pyz), (0.60*hex_size))

        px += hex_size
        py += hex_size
        pygame.draw.circle(sim_surf, (134, 116, 181), (px, py), (0.60*hex_size))  # can change size but looks good

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:  # resizable window, map size updating not working
            width, height = event.w, event.h
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            sim_surf = pygame.surface.Surface((event.w * (4 / 5), event.h))
            hex_surf = pygame.surface.Surface((event.w * (4 / 5), event.h))
            text_surf = pygame.surface.Surface((event.w * (1 / 5), event.h))
            needs_redraw = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        # checking for button presses, button functionality
        # Adding separation
        rect_add_sep = text_add_sep.get_rect(topleft = (width*(4/5),(0*height)+50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_add_sep.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if sep_force >= 0:
                sep_force += 1

        # Removing separation
        rect_rm_sep = text_rm_sep.get_rect(topleft=((width*(4/5))+100, (0*height)+50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_rm_sep.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if sep_force >= 0:
                sep_force -= 1

        # Adding cohesion
        rect_add_coh = text_add_coh.get_rect(topleft=((width * (4 / 5)), ((1/5) * height) + 50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_add_coh.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if coh_force >= 0:
                coh_force += 1

        # Removing cohesion
        rect_rm_coh = text_rm_coh.get_rect(topleft=((width*(4/5))+100, ((1/5)*height)+50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_rm_coh.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if coh_force >= 0:
                coh_force -= 1

        # Adding alignment
        rect_add_align = text_add_align.get_rect(topleft=((width * (4 / 5)), ((2/5) * height) + 50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_add_align.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if alig_force >= 0:
                alig_force += 1

        # Removing cohesion
        rect_rm_alig = text_rm_align.get_rect(topleft=((width*(4/5))+100, ((2/5)*height)+50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_rm_alig.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if alig_force >= 0:
                alig_force -= 1

        # Adding radius
        rect_add_radius = text_add_radius.get_rect(topleft=((width * (4 / 5)), ((3/5) * height) + 50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_add_radius.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if radius >= 0:
                radius += 1

        # Removing radius
        rect_rm_radius = text_rm_radius.get_rect(topleft=((width*(4/5))+100, ((3/5)*height)+50))
        if event.type == pygame.MOUSEBUTTONDOWN and rect_rm_radius.collidepoint(pygame.mouse.get_pos()):
            text_surf.fill((89, 97, 43))
            if radius >= 0:
                radius -= 1

    screen.blit(sim_surf, (0, 0))
    pygame.display.flip()
    clock.tick(10)  # lower speed to observe motion
    print(clock.get_fps())

pygame.quit()

"""
to do:

figure out if it works correctly

find good values for forces

figure out or rewrite finding neighbors

optimization

add barriers or nests or smn

oddzielny surface dla hexmap tylko na poczatku albo po resize, co frame tylko blit
"""
