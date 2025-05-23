#!/bin/env python3

import pygame
from pygame.math import Vector2 as Vec2
from pygame import (Surface, Rect)
import sys
import time

import logger

if (__name__ != "__main__"):
    print("Need to run directly")
    sys.exit(1)

VERSION_MAJOR = 0
VERSION_MINOR = 11
VERSION_PATCH = 0

log = logger.LOG()
log.set_warnlevel(logger.LOG_level("INFO"))

pygame.init()

class Image:
    def __init__(self, surface: Surface, position: Vec2):
        '''
        param: position is the center of the surface, and will always stay the same.
        '''
        self.surface = surface
        self.trans_rect = None
        self.trans_surface = None
        self.scale_mul = 1.0
        self.max_scale = 5.0
        self.min_scale = 1.0
        self.calc_transform()
    def set_max_scale(new_scale: float) -> None:
        self.max_scale = max_scale
        if (max_scale < self.max_scale):
            self.scale_mul = min(max_scale, self.scale_mul)
            self.calc_transform()
    def offset_scale(scale_offset: float) -> None:
        if scale_offset + self.scale_mul <= self.max_scale:
            self.scale_mul += scale_offset
    def calc_transform(self) -> None:
        self.trans_surface = pygame.transform.scale(self.surface, (self.surface.get_width()*self.scale_mul, self.surface.get_height()*self.scale_mul))
        self.trans_rect = self.trans_surface.get_rect(center=self.trans_rect.center)
    def get_twidth(self) -> int:
        '''
        Get transformed surface pixel width
        '''
        return self.trans_surface.get_width()
    def get_theight(self) -> int:
        '''
        Get transformed surface pixel height
        '''
        return self.trans_surface.get_height()
    def get_tsize(self) -> Vec2:
        '''
        Get transformed surface pixel size
        '''
        return Vec2(self.trans_surface.get_size())
    def get_owidth(self) -> int:
        '''
        Get original surface pixel width
        '''
        return self.surface.get_width()
    def get_owidth(self) -> int:
        '''
        Get original surface pixel height
        '''
        return self.surface.get_height()
    def get_osize(self) -> Vec2:
        '''
        Get original surface pixel size
        '''
        return Vec2(self.surface.get_size())
    def get_cpos(self) -> Vec2:
        '''
        Get image center pixel position
        '''
        return self.trans_rect.center
    def get_tpos(self) -> Vec2:
        '''
        Get transformed surface top left pixel position
        '''
        return self.trans_rect.topleft

class Key:
    return_normal_mode = pygame.K_ESCAPE
    select_mode_select_color = pygame.K_s
    select_mode_set_color = pygame.K_c
    layer_mode_toggle = pygame.K_l
    resize_editing_surface = pygame.K_r
    undo_editing_surface_modification = pygame.K_u
    save_current_layer_surface = pygame.K_w
    pick_color = pygame.K_p
    confirm = pygame.K_RETURN
    move_camera = pygame.K_m
    fill_bucket = pygame.K_f
    toggle_grid_lines = pygame.K_g
    quit = pygame.K_q
            
class State:
    unsaved_changes: bool = False
    main_mouse_button_clicked_this_frame = False
    main_mouse_button_held = False
    move_camera = False
    camera_position = [0, 0]
    last_mouse_position = (0, 0)
    max_undo_objects = 512
    current_selected_surface_layer_index = 0
    editing_surface_zoom = 30
    max_editing_surface_zoom = 100
    min_editing_surface_zoom = 0
    display_grid_lines = True
    text_io_buffer = ""
    max_text_buffer_char_count = 64
    clear_text_buffer_on_write = False # clear text buffer on next write
    default_surface = Surface((32, 32), pygame.SRCALPHA)
    default_surface_color = ((200, 200, 200))
State.default_surface.fill(State.default_surface_color)

def write_str_to_text_buffer(string: str) -> None:
    State.text_io_buffer = string[:State.max_text_buffer_char_count]
def append_str_to_text_buffer(string: str) -> None:
    if State.clear_text_buffer_on_write:
        State.text_io_buffer = ""
        State.clear_text_buffer_on_write = False
    append_char_count = State.max_text_buffer_char_count - len(State.text_io_buffer)
    if append_char_count <= 0:
        return None
    State.text_io_buffer = State.text_io_buffer + string[:append_char_count]
def clear_text_buffer() -> None:
    State.text_io_buffer = ""

class Mode:
    NORMAL = 0
    SELECT_COLOR = 1
    SET_COLOR = 2
    SAVE_FILE = 3
    RESIZE_SURFACE = 4
    LAYERS = 5
    current = NORMAL

class ImageLayerBuffer:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.surface = None
        self.undo_object = []
    def load(self) -> (bool, str):
        error_str = ""
        try:
            self.surface = pygame.image.load(self.filepath)
        except FileNotFoundError:
            error_str = "File '{self.filepath}' was not found"
            self.surface = None
            return (True, error_str)
        except pygame.error:
            error_str = "Pygame error: {sys.exc_info()[1]}"
            self.surface = None
            return (True, error_str)
        return (False, "")

app_font_size = 20
app_font_object = pygame.font.Font(None, app_font_size)

class UITextElement:
    def __init__(self, position: Vec2, text: str, frame_x_px_margin: int, frame_y_px_margin: int):
        self.text: str = text
        if not isinstance(position, Vec2):
            position = Vec2(position)
        self.position = position
        self.margin: Vec2 = Vec2(frame_x_px_margin, frame_y_px_margin)
        self.regenerate_surfaces()
    def set_top_left_pos(self, position: Vec2) -> None:
        if not isinstance(position, Vec2): # Try help if position is of incorrect type
            position = Vec2(position)
        self.position = position
    def set_top_right_pos(self, position: Vec2) -> None:
        self.regenerate_surfaces() # incase there are changes
        if not isinstance(position, Vec2): # Try help if position is of incorrect type
            position = Vec2(position)
        self.position = Vec2(position.x -self.get_width(), position.y)
    def set_bottom_right_pos(self, position: Vec2) -> None:
        self.regenerate_surfaces() # incase there are changes
        if not isinstance(position, Vec2): # Try help if position is of incorrect type
            position = Vec2(position)
        self.position = position - self.get_size()
    def set_bottom_left_pos(self, position: Vec2) -> None:
        self.regenerate_surfaces()
        if not isinstance(position, Vec2): # Try help if position is of incorrect type
            position = Vec2(position)
        self.position = Vec2(position.x, position.y -self.get_height())
    def get_width(self) -> int:
        return self.bg_surface.get_width()
    def get_height(self) -> int:
        return self.bg_surface.get_height()
    def get_size(self) -> Vec2:
        return Vec2(self.get_width(), self.get_height())
    def get_pos(self) -> Vec2:
        return self.position
    def render(self, render_surface: pygame.Surface) -> None:
        render_surface.blit(self.bg_surface, self.position)
        render_surface.blit(self.text_surface, self.position+self.margin)
    def regenerate_surfaces(self) -> None:
        self.text_surface: pygame.Surface = app_font_object.render(self.text, True, app_text_color)
        self.bg_surface: pygame.Surface = pygame.Surface((self.text_surface.get_width()+self.margin.x*2, self.text_surface.get_height()+self.margin.y*2))
        self.bg_surface.fill(app_text_background_color)
        self.bg_surface.set_alpha(app_text_background_alpha)
    def update_text(self, new_text: str) -> None:
        self.text = new_text
        self.regenerate_surfaces()

def print_keybindings():
    print("Key bindings:")
    print(" Can escape back to normal mode with key", pygame.key.name(Key.return_normal_mode))
    print(" - select color (In normal mode): ", pygame.key.name(Key.select_mode_select_color))
    print(" - set color (In normal mode): ", pygame.key.name(Key.select_mode_set_color))
    print(" - resize editing surface (In normal mode): ", pygame.key.name(Key.resize_editing_surface))
    print(" - layers management (In normal mode): ", pygame.key.name(Key.layer_mode_toggle))
    print(" - undo editing surface modification (In normal mode): ", pygame.key.name(Key.undo_editing_surface_modification))
    print(" - save current layer (In normal mode): ", pygame.key.name(Key.save_current_layer_surface))
    print(" - pick current hovered color (In normal mode): ", pygame.key.name(Key.pick_color))
    print(" - confirm (In any mode, used for prompts): ", pygame.key.name(Key.confirm))
    print(" - fill bucket paint brush (In normal mode): " , pygame.key.name(Key.fill_bucket))
    print(" - toggle grid lines (In normal mode): ", pygame.key.name(Key.toggle_grid_lines))
    print(" - quit program without saving (or save warning) (In normal mode): ", pygame.key.name(Key.quit))

input_layer_filepaths = []
surface_layers = []

argv = sys.argv
argc = len(argv)

if (argc > 1):
    if (argv[1] == "--help" or argv[1] == "-h"):
        print( "Description: Pixel art editor with key bindings")
        print(f"\'python3 {argv[0]} --version \' for version infomation")
        print(f"Usage: python3 {argv[0]}")
        print(f"Usage: python3 {argv[0]} [Options] [--] <FILE>...")
        print(f"Options:")
        print(f"  --key-bindings  - output key bindings and exit")
        print(f"Note:")
        print(f"  - Any arguments past a '--' argument would only be considered as a file")
        sys.exit()
    if (argv[1] == "--version"):
        print(f"VERSION: {VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}")
        sys.exit()

class ImageLoadStates:
    NO_ERROR = 0
    NOT_FOUND = 1
    PYGAME_ERROR = 2
def load_image(path: str) -> (Surface or None, ImageLoadStates, str):
    try:
        surface = pygame.image.load(path)
    except FileNotFoundError:
        return None, ImageLoadStates.NOT_FOUND, f"Could not load file '{path}'"
    except pygame.error:
        return None, ImageLoadStates.PYGAME_ERROR, f"Pygame could not load in the image file '{path}', {sys.exc_info()[1]}"
    return surface, ImageLoadStates.NO_ERROR, ""

def assume_or_exception(condition: bool) -> None:
    if (not condition):
        Exception(f"Assumption not met")

arg_skip_count = 0
cli_error_count = 0
cli_only_files_remain = False
for arg_index in range(1, argc):
    if (arg_skip_count > 0):
        arg_skip_count -= 1
        continue

    arg = argv[arg_index]

    if (arg == "--" and not cli_only_files_remain):
        cli_only_files_remain = True
    elif (arg == "--key-bindings" and not cli_only_files_remain):
        print_keybindings()
        sys.exit()
    elif (arg[:2] == "--" and not cli_only_files_remain):
        print(f"[{arg_index}] argument {arg} is not recognised")
        cli_error_count += 1
    else:
        # is a file path
        input_layer_filepaths.append(arg)

if (cli_error_count > 0):
    sys.exit(f"Exiting. {cli_error_count} error(s) occured")
del cli_error_count

load_file_error_count = 0
handled_filepaths = []
for input_filepath in input_layer_filepaths:
    input_surface, status, message = load_image(input_filepath)
    if status == ImageLoadStates.NOT_FOUND:
        print(message)
        input_surface = None
    elif status == ImageLoadStates.PYGAME_ERROR:
        print(message)
        load_file_error_count += 1
        continue
    if (input_filepath in handled_filepaths):
        print(f"Layers cannot have the same file paths, path '{input_filepath}'")
        load_file_error_count += 1
        continue
    handled_filepaths.append(input_filepath)
    if (input_surface == None):
        print(f"Making a new image surface for layer '{input_filepath}'")
        input_surface = State.default_surface.copy()
    surface_layers.append(input_surface)
if (load_file_error_count > 0):
    sys.exit(f"Exiting. {load_file_error_count} error(s) occured when loading image files from disk")
del load_file_error_count

assume_or_exception(len(input_layer_filepaths) == len(surface_layers))

if (len(input_layer_filepaths) == 0):
    print("No input image files given. Loading a default surface. Setting output file to 'a.png'.")
    surface_layers.append(State.default_surface.copy())
    input_layer_filepaths.append("a.png")

per_layer_undo_objects = [[]] * len(input_layer_filepaths)
log.output(logger.LOG_level("INFO"), f"per_layer_undo_objects: {per_layer_undo_objects}")

def add_layer(path: str, surface: Surface) -> None:
    global surface_layers, input_layer_filepaths, per_layer_undo_objects
    log.output(logger.LOG_level("INFO"), f"Attempting to add new layer path:'{path}' surface:{surface}")
    input_layer_filepaths.append(path)
    surface_layers.append(surface)
    per_layer_undo_objects.append([])
    log.output(logger.LOG_level("INFO"), f"Successfully added new layer")

def get_mode_type_code_to_str(mode_type_code):
    if (mode_type_code == Mode.NORMAL):
        return "normal"
    elif (mode_type_code == Mode.SELECT_COLOR):
        return "select color"
    elif (mode_type_code == Mode.SET_COLOR):
        return "set color"
    elif (mode_type_code == Mode.SAVE_FILE):
        return "save file"
    elif (mode_type_code == Mode.RESIZE_SURFACE):
        return "resize surface"
    elif (mode_type_code == Mode.LAYERS):
        return "layers management"
    else:
        return "unknown"

def paint_tool_bucket(surface: pygame.Surface, start_point: pygame.math.Vector2, new_color: pygame.Color, mask: pygame.Mask=None) -> pygame.Mask:
    if (mask != None):
        assume_or_exception(surface.get_size() != mask.get_size())
    log.output(logger.LOG_level("INFO"), f"Paint bucket started to draw, mask={mask}")
    fill_mask = pygame.Mask(surface.get_size())
    fill_mask.clear()
    have_been_stack = [(start_point.x, start_point.y)]
    try:
        search_color = surface.get_at((start_point.x, start_point.y))
    except IndexError:
        log.output(logger.LOG_level("WARNING"), "Position given is invalid")
        return None
    if (search_color == new_color):
        log.output(logger.LOG_level("WARNING"), "Search color and new color are the same")
        return None
    surface.set_at(start_point, new_color)
    # debug
    visited = [(start_point.x, start_point.y)]
    # /debug
    while len(have_been_stack) != 0:
        log.output(logger.LOG_level("INFO"), f"\n{len(have_been_stack)} elements in the have_been_visited_stack")
        current_pixel_pos = have_been_stack[-1]
        # debug
        #log.output(logger.LOG_level("INFO"), f"stack={have_been_stack}")
        visited.append(current_pixel_pos)
        if (visited.count(current_pixel_pos) > 50): # worringly large number of occurances
            # potentially stuck in a loop
            log.output(logger.LOG_level("ERROR"), f"pixel {current_pixel_pos} has been visited more than 50 times")
            log.output(logger.LOG_level("INFO"), f"output current image state to ./a-debug.png")
            pygame.image.save(surface, "./a-debug.png")
            sys.exit(1)
        # /debug
        if (current_pixel_pos[0]-1 >= 0):
            search_pixel_pos = (current_pixel_pos[0]-1, current_pixel_pos[1])
            log.output(logger.LOG_level("INFO"), f"left pixel color = {surface.get_at(search_pixel_pos)}")
            if (surface.get_at(search_pixel_pos) == search_color and not(search_pixel_pos in have_been_stack)):
                if (mask == None or mask.get_at(search_pixel_pos)):
                    surface.set_at(search_pixel_pos, new_color)
                    fill_mask.set_at(search_pixel_pos, 1)
                    have_been_stack.append(search_pixel_pos)
                    log.output(logger.LOG_level("INFO"), f"Moved left")
                    continue
        if (current_pixel_pos[1]-1 >= 0):
            search_pixel_pos = (current_pixel_pos[0], current_pixel_pos[1]-1)
            log.output(logger.LOG_level("INFO"), f"up pixel color = {surface.get_at(search_pixel_pos)}")
            if (surface.get_at(search_pixel_pos) == search_color and not(search_pixel_pos in have_been_stack)):
                if (mask == None or mask.get_at(search_pixel_pos)):
                    surface.set_at(search_pixel_pos, new_color)
                    fill_mask.set_at(search_pixel_pos, 1)
                    have_been_stack.append(search_pixel_pos)
                    log.output(logger.LOG_level("INFO"), f"Moved up")
                    continue
        if (current_pixel_pos[0]+1 < surface.get_width()):
            search_pixel_pos = (current_pixel_pos[0]+1, current_pixel_pos[1])
            log.output(logger.LOG_level("INFO"), f"right pixel color = {surface.get_at(search_pixel_pos)}")
            if (surface.get_at(search_pixel_pos) == search_color and not(search_pixel_pos in have_been_stack)):
                if (mask == None or mask.get_at(search_pixel_pos)):
                    surface.set_at(search_pixel_pos, new_color)
                    fill_mask.set_at(search_pixel_pos, 1)
                    have_been_stack.append(search_pixel_pos)
                    log.output(logger.LOG_level("INFO"), f"Moved right")
                    continue
        if (current_pixel_pos[1]+1 < surface.get_height()):
            search_pixel_pos = (current_pixel_pos[0], current_pixel_pos[1]+1)
            log.output(logger.LOG_level("INFO"), f"down pixel color = {surface.get_at(search_pixel_pos)}")
            if (surface.get_at(search_pixel_pos) == search_color and not(search_pixel_pos in have_been_stack)):
                if (mask == None or mask.get_at(search_pixel_pos)):
                    surface.set_at(search_pixel_pos, new_color)
                    fill_mask.set_at(search_pixel_pos, 1)
                    have_been_stack.append(search_pixel_pos)
                    log.output(logger.LOG_level("INFO"), f"Moved down")
                    continue
        log.output(logger.LOG_level("INFO"), f"poped, moved back by one")
        have_been_stack.pop()
    log.output(logger.LOG_level("INFO"), "paint bucket has finished drawing")
    return fill_mask

buffer_colors = []
current_buffer_colors_index = 0

for _ in range(10):
    buffer_colors.append(pygame.Color(255, 255, 255, 255))

class UndoObject:
    def __init__(self):
        pass
class UndoSinglePixel(UndoObject):
    def __init__(self, pixel_pos: pygame.math.Vector2, color: pygame.Color):
        self.pixel_position = pixel_pos
        self.color = color
    def __str__(self):
        return f"UndoSinglePixel(pixel_pos={self.pixel_position}, color={self.color})"
class UndoBucketFill(UndoObject):
    def __init__(self, pixel_pos: pygame.math.Vector2, old_color: pygame.Color, mask: pygame.Mask):
        self.pixel_position: pygame.math.Vector2 = pygame.math.Vector2(pixel_pos)
        self.old_color: pygame.Color = old_color
        self.mask: pygame.Mask = mask
    def __str__(self):
        return f"UndoBucketFill(pixel_pos={self.pixel_position}, old_color={self.old_color}, mask:{self.mask})"
class UndoResize(UndoObject):
    def __init__(self, old_surface: pygame.Surface):
        self.old_surface: pygame.Surface = old_surface
    def __str__(self):
        return f"UndoResize(old_surface={self.old_surface})"

def add_undo_to_cur_layer(undo_object: UndoObject):
    global per_layer_undo_objects
    log.output(logger.LOG_level("INFO"), f"per_layer_undo_objects: {per_layer_undo_objects}, cur_sel_surf_layer_ind: {State.current_selected_surface_layer_index}")
    per_layer_undo_objects[State.current_selected_surface_layer_index].append(undo_object)
    if (len(per_layer_undo_objects[State.current_selected_surface_layer_index]) > State.max_undo_objects):
        per_layer_undo_objects[State.current_selected_surface_layer_index].pop(0)
def pop_undo_from_cur_layer() -> UndoObject: # Or return None when empty
    global per_layer_undo_objects
    if len(per_layer_undo_objects[State.current_selected_surface_layer_index]) == 0:
        return None
    return per_layer_undo_objects[State.current_selected_surface_layer_index].pop()

display_color_rect_horizontal_gap = 5 # pixels
display_color_rect_screen_verticle_gap = 10 # pixels

app_text_background_alpha = 150

screen_size = Vec2(640, 480)
screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
editing_surface_screen_proportionality_xy = Vec2((screen_size[0]/640, screen_size[1]/480))

bg_color = (100, 100, 100)
app_text_color = (0, 0, 0)
app_text_background_color = (255 - app_text_color[0], 255 - app_text_color[1], 255 - app_text_color[2], 100)
max_fps = 60

def camera_transform(vec2f_position):
    return (vec2f_position[0] - State.camera_position[0] + screen_size[0]/2, vec2f_position[1] - State.camera_position[1] + screen_size[1]/2)

def camera_reverse_transform(vec2f_position):
    return (vec2f_position[0] + State.camera_position[0] - screen_size[0]/2, vec2f_position[1] + State.camera_position[1] - screen_size[1]/2)
error_string = ""

def position_rel_to_surface(surface: pygame.Surface) -> Vec2:
    pass
def mouse_pos_on_cur_image_layer() -> Vec2:
    reverse_camera_mouse_position = camera_reverse_transform(State.last_mouse_position)
    assume_or_exception(not (editing_surface_screen_proportionality_xy[0] == 0 and editing_surface_screen_proportionality_xy[1] == 0))
    assume_or_exception(State.editing_surface_zoom != 0)
    take_away_x, take_away_y = 0, 0
    if (reverse_camera_mouse_position[0] < 0):
        take_away_x = +1
    if (reverse_camera_mouse_position[1] < 0):
        take_away_y = +1
    mouse_position_on_editing_surface_position = (int(reverse_camera_mouse_position[0]/(editing_surface_screen_proportionality_xy[0]*State.editing_surface_zoom))+surface_layers[State.current_selected_surface_layer_index].get_width()//2-take_away_x, int(reverse_camera_mouse_position[1]/(editing_surface_screen_proportionality_xy[1]*State.editing_surface_zoom))+surface_layers[State.current_selected_surface_layer_index].get_height()//2-take_away_y)
    return mouse_position_on_editing_surface_position

ui_display_layer_index = UITextElement(Vec2(0, 0), f"{State.current_selected_surface_layer_index}/{len(surface_layers)}", 1, 1)
ui_display_layer_index.set_top_right_pos(Vec2(10, 0))
ui_display_surface_size = UITextElement(Vec2(5, 5), f"{surface_layers[State.current_selected_surface_layer_index].get_width()}w {surface_layers[State.current_selected_surface_layer_index].get_height()}h", 5, 5)

previous_frame_time = time.time()
clock = pygame.time.Clock()
while True:
    clock.tick(max_fps)
    fps = clock.get_fps()
    pygame.display.set_caption(f"edit - {input_layer_filepaths[State.current_selected_surface_layer_index]} - {fps : 0.1f}")
    delta_time_seconds = time.time() - previous_frame_time
    previous_frame_time = time.time()

    State.main_mouse_button_clicked_this_frame = False

    State.last_mouse_position = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if (event.type == pygame.QUIT or Mode.current == Mode.NORMAL and event.type == pygame.KEYDOWN and event.key == Key.quit):
            if (State.unsaved_changes):
                write_str_to_text_buffer("Warning: Unsaved changes, quit to ignore")
                State.clear_text_buffer_on_write = True
                State.unsaved_changes = False # TODO: Make a more permenant solution, with a timer
                continue
            pygame.quit()
            sys.exit()

        if (event.type == pygame.WINDOWRESIZED):
            screen_size = (event.x, event.y)
            width, height = screen_size[0]/640, screen_size[1]/480
            average = (width+height)/2
            app_font_size = int(20 * average)
            app_font_object = pygame.font.Font(None, app_font_size)
            # update ui elements on window resize.
            ui_display_surface_size.regenerate_surfaces()
            ui_display_layer_index.regenerate_surfaces()

        if (event.type == pygame.MOUSEWHEEL):
            if (State.min_editing_surface_zoom < State.editing_surface_zoom + event.y < State.max_editing_surface_zoom):
                State.editing_surface_zoom += event.y

        if (event.type == pygame.MOUSEBUTTONDOWN):
            if (event.button == 1):
                log.output(logger.LOG_level("INFO"), f"Clicked main mouse button")
                State.main_mouse_button_clicked_this_frame = True
                State.main_mouse_button_held = True

        if (event.type == pygame.MOUSEBUTTONUP):
            if (event.button == 1):
                State.main_mouse_button_held = False

        if (event.type == pygame.KEYDOWN):

            if (Mode.current == Mode.NORMAL and event.key == Key.toggle_grid_lines):
                State.display_grid_lines = not State.display_grid_lines
            if (Mode.current != Mode.NORMAL and event.key == Key.return_normal_mode):
                log.output(logger.LOG_level("INFO"), f"Escaped to normal mode from {get_mode_type_code_to_str(Mode.current)}")
                Mode.current = Mode.NORMAL
                clear_text_buffer()
            if (Mode.current == Mode.NORMAL and event.key == Key.select_mode_select_color):
                Mode.current = Mode.SELECT_COLOR
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(Mode.current)}")
                clear_text_buffer()
            if (Mode.current == Mode.NORMAL and event.key == Key.select_mode_set_color):
                Mode.current = Mode.SET_COLOR
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(Mode.current)}")
                clear_text_buffer()
            if (Mode.current == Mode.NORMAL and event.key == Key.resize_editing_surface):
                Mode.current = Mode.RESIZE_SURFACE
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(Mode.current)}")
                clear_text_buffer()
            if (Mode.current == Mode.NORMAL and event.key == Key.layer_mode_toggle):
                log.output(logger.LOG_level("INFO"), "Entered layer mode")
                Mode.current = Mode.LAYERS
                clear_text_buffer()
                continue
            if (Mode.current == Mode.NORMAL and event.key == Key.move_camera):
                State.move_camera = True
            if (Mode.current == Mode.NORMAL and event.key == Key.undo_editing_surface_modification):
                undo_package = pop_undo_from_cur_layer()
                if (undo_package != None):
                    log.output(logger.LOG_level("INFO"), f"undoing package {undo_package}")
                    if isinstance(undo_package, UndoSinglePixel):
                        surface_layers[State.current_selected_surface_layer_index].set_at(undo_package.pixel_position, undo_package.color)
                        State.unsaved_changes = True
                    elif isinstance(undo_package, UndoBucketFill):
                        paint_tool_bucket(surface_layers[State.current_selected_surface_layer_index], undo_package.pixel_position, undo_package.old_color, undo_package.mask)
                        State.unsaved_changes = True
                    elif isinstance(undo_package, UndoResize):
                        surface_layers[State.current_selected_surface_layer_index] = undo_package.old_surface
                        State.unsaved_changes = True
                    else:
                        log.output(logger.LOG_level("WARNING"), f"undo package {undo_package} is not handles when undo button pressed")
                    log.output(logger.LOG_level("INFO"), f"Applied undo")
            if (Mode.current == Mode.NORMAL and event.key == Key.save_current_layer_surface):
                State.unsaved_changes = False
                pygame.image.save(surface_layers[State.current_selected_surface_layer_index], input_layer_filepaths[State.current_selected_surface_layer_index])
                log.output(logger.LOG_level("INFO"), f"Saved current editing surface to {input_layer_filepaths[State.current_selected_surface_layer_index]}")
            if (Mode.current == Mode.NORMAL and event.key == Key.fill_bucket):
                mouse_position_on_editing_surface_position = mouse_pos_on_cur_image_layer()

                previous_color = surface_layers[State.current_selected_surface_layer_index].get_at(mouse_position_on_editing_surface_position)
                fill_color = buffer_colors[current_buffer_colors_index]
                fill_mask = paint_tool_bucket(surface_layers[State.current_selected_surface_layer_index], pygame.math.Vector2(mouse_position_on_editing_surface_position), fill_color)
                State.unsaved_changes = True

                if (fill_mask != None):
                    undo_object = UndoBucketFill(pygame.math.Vector2(mouse_position_on_editing_surface_position), previous_color, fill_mask)
                    add_undo_to_cur_layer(undo_object)
                else:
                    log.output(logger.LOG_level("WARNING"), f"fill_mask is None, failed to bucket fill")
            if (Mode.current == Mode.NORMAL and event.key == Key.pick_color):
                current_hovered_pixel_pos = mouse_pos_on_cur_image_layer()
                try:
                    hover_color = surface_layers[State.current_selected_surface_layer_index].get_at((current_hovered_pixel_pos[0], current_hovered_pixel_pos[1]))
                except IndexError:
                    log.output(logger.LOG_level("WARNING"), "Position given is invalid")
                    continue
                log.output(logger.LOG_level("INFO"), f"adding color {hover_color} to pallet buffer slot {current_buffer_colors_index}")
                buffer_colors[current_buffer_colors_index] = hover_color

            if (event.key == Key.confirm):
                if (Mode.current == Mode.SELECT_COLOR):
                    Mode.current = Mode.NORMAL
                    log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(Mode.current)}")
                if (Mode.current == Mode.SET_COLOR):
                    Mode.current = Mode.NORMAL
                    log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(Mode.current)}")
                    current_color_channel = None
                    final_color = buffer_colors[current_buffer_colors_index]
                    current_number_str = ""
                    for char in State.text_io_buffer:
                        if (char == "r"):
                            if (len(current_number_str) > 0):
                                if (char == "r"):
                                    if (int(current_number_str) < 256):
                                        final_color.r = int(current_number_str)
                                if (char == "g"):
                                    if (int(current_number_str) < 256):
                                        final_color.g = int(current_number_str)
                                if (char == "b"):
                                    if (int(current_number_str) < 256):
                                        final_color.b = int(current_number_str)
                                if (char == "a"):
                                    if (int(current_number_str) < 256):
                                        final_color.a = int(current_number_str)
                            current_color_channel = "r"
                            current_number_str = ""
                        elif (char == "g"):
                            if (len(current_number_str) > 0):
                                if (char == "r"):
                                    if (int(current_number_str) < 256):
                                        final_color.r = int(current_number_str)
                                if (char == "g"):
                                    if (int(current_number_str) < 256):
                                        final_color.g = int(current_number_str)
                                if (char == "b"):
                                    if (int(current_number_str) < 256):
                                        final_color.b = int(current_number_str)
                                if (char == "a"):
                                    if (int(current_number_str) < 256):
                                        final_color.a = int(current_number_str)
                            current_color_channel = "g"
                            current_number_str = ""
                        elif (char == "b"):
                            if (len(current_number_str) > 0):
                                if (char == "r"):
                                    if (int(current_number_str) < 256):
                                        final_color.r = int(current_number_str)
                                if (char == "g"):
                                    if (int(current_number_str) < 256):
                                        final_color.g = int(current_number_str)
                                if (char == "b"):
                                    if (int(current_number_str) < 256):
                                        final_color.b = int(current_number_str)
                                if (char == "a"):
                                    if (int(current_number_str) < 256):
                                        final_color.a = int(current_number_str)
                            current_color_channel = "b"
                            current_number_str = ""
                        elif (char == "a"):
                            if (len(current_number_str) > 0):
                                if (char == "r"):
                                    if (int(current_number_str) < 256):
                                        final_color.r = int(current_number_str)
                                if (char == "g"):
                                    if (int(current_number_str) < 256):
                                        final_color.g = int(current_number_str)
                                if (char == "b"):
                                    if (int(current_number_str) < 256):
                                        final_color.b = int(current_number_str)
                                if (char == "a"):
                                    if (int(current_number_str) < 256):
                                        final_color.a = int(current_number_str)
                            current_color_channel = "a"
                            current_number_str = ""
                        elif (char.isdigit()):
                            current_number_str += char
                        else:
                            log.output(logger.LOG_level("ERROR"), f"char \'{char}\' should not be in the buffer")

                    if (len(current_number_str) != 0):
                        if (current_color_channel == "r"):
                            if (int(current_number_str) < 256):
                                final_color.r = int(current_number_str)
                        if (current_color_channel == "g"):
                            if (int(current_number_str) < 256):
                                final_color.g = int(current_number_str)
                        if (current_color_channel == "b"):
                            if (int(current_number_str) < 256):
                                final_color.b = int(current_number_str)
                        if (current_color_channel == "a"):
                            if (int(current_number_str) < 256):
                                final_color.a = int(current_number_str)

                if (Mode.current == Mode.RESIZE_SURFACE):
                    Mode.current = Mode.NORMAL

                    undo_object = UndoResize(surface_layers[State.current_selected_surface_layer_index])
                    add_undo_to_cur_layer(undo_object)

                    width = surface_layers[State.current_selected_surface_layer_index].get_width()
                    height = surface_layers[State.current_selected_surface_layer_index].get_height()
                    number_str = ""
                    for char in State.text_io_buffer:

                        if (char == "w"):
                            if (len(number_str) > 0):
                                if (int(number_str) > 0):
                                    width = int(number_str)
                                    number_str = ""
                        if (char == "h"):
                            if (len(number_str) > 0):
                                if (int(number_str) > 0):
                                    height = int(number_str)
                                    number_str = ""
                        if (char.isdigit()):
                            number_str += char
                    surface_layers[State.current_selected_surface_layer_index] = pygame.transform.scale(surface_layers[State.current_selected_surface_layer_index], (width, height))
                    ui_display_surface_size.update_text(f"{surface_layers[State.current_selected_surface_layer_index].get_width()}w {surface_layers[State.current_selected_surface_layer_index].get_height()}h")
                    State.unsaved_changes = True
                    log.output(logger.LOG_level("INFO"), f"Changed editing surface size to ({surface_layers[State.current_selected_surface_layer_index].get_width()}, {surface_layers[State.current_selected_surface_layer_index].get_height()})")
                if (Mode.current == Mode.LAYERS):
                    Mode.current = Mode.NORMAL
                    if len(State.text_io_buffer) < 1:
                        log.output(logger.LOG_level("WARNING"), f"Input Text Buffer is empty when submitting input to layers processor")
                        continue
                    State.text_io_buffer = State.text_io_buffer.strip()
                    if State.text_io_buffer.isdigit():
                        layer_index = int(State.text_io_buffer)
                        if (layer_index >= len(surface_layers)):
                            clear_text_buffer()
                            write_str_to_text_buffer("Error: layer index out of bound")
                            State.clear_text_buffer_on_write = True
                            continue # Error selected surface index is not valid/out of range
                        State.current_selected_surface_layer_index = layer_index
                        Mode.current = Mode.NORMAL
                        continue
                    text_buf_args = State.text_io_buffer.split(" ")
                    while "" in text_buf_args:
                        text_buf_args.remove("")
                    operation = text_buf_args.pop(0)
                    if operation == "n":
                        if len(text_buf_args) == 0:
                            write_str_to_text_buffer("Missing argument(s): <PATH> ...")
                            continue
                        for arg in text_buf_args:
                            log.output(logger.LOG_level("INFO"), f"Adding a new layer through the layer manger with the path of '{arg}'")
                            add_layer(arg, State.default_surface.copy())
                    if operation == "l":
                        if len(text_buf_args) == 0:
                            write_str_to_text_buffer("Missing argument(s): <PATH> ...")
                            continue
                        for arg in text_buf_args:
                            log.output(logger.LOG_level("INFO"), f"Attempting to load in image '{arg}'")
                            loaded_surface, status, message = load_image(arg)
                            if status != ImageLoadStates.NO_ERROR:
                                write_str_to_text_buffer(f"Failed image load: {message}")
                                continue
                            add_layer(arg, loaded_surface)

            if (event.key == pygame.K_BACKSPACE):
                if (Mode.current == Mode.SET_COLOR):
                    clear_text_buffer()
                    Mode.current = Mode.NORMAL
                    log.output(logger.LOG_level("INFO"), f"Changed mode to normal from set color")
                if (Mode.current == Mode.RESIZE_SURFACE):
                    clear_text_buffer()
                    Mode.current = Mode.NORMAL
                    log.output(logger.LOG_level("INFO"), f"Changed mode to normal from resize surface")
                if (Mode.current == Mode.LAYERS):
                    clear_text_buffer()
                    Mode.current = Mode.NORMAL

            if (Mode.current == Mode.SET_COLOR and (event.unicode.isdigit() or (event.unicode in ["r", "g", "b", "a"]))):
                last_number_in_input = ""
                #print(f"{State.text_io_buffer}, reverse:{State.text_io_buffer[::-1]}")
                # code to stop numbers being larger than 255
                for char in State.text_io_buffer[::-1]:
                    #print(f"char={char}")
                    if not char.isdigit():
                        #print(f"break at {char}")
                        break
                    last_number_in_input += char
                if len(last_number_in_input) > 0 and event.unicode.isdigit():
                    last_number_in_input = last_number_in_input[::-1]
                    print(last_number_in_input)
                    val = int(last_number_in_input+event.unicode)
                    if val >= 255:
                        continue
                State.text_io_buffer += event.unicode
            if (Mode.current == Mode.SELECT_COLOR and event.unicode.isdigit()):
                index = int(event.unicode)
                if (index >= 0 and index <= 9):
                    # Shift the indexs by one place.
                    index = (index+9) % 10
                    log.output(logger.LOG_level("INFO"), f"Switched from color index {current_buffer_colors_index} to {index}")
                    current_buffer_colors_index = index
                    Mode.current = Mode.NORMAL
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(Mode.current)}")
            if (Mode.current == Mode.RESIZE_SURFACE and (event.unicode.isdigit() or event.unicode in ["w", "h"])):
                append_str_to_text_buffer(event.unicode)

            if (Mode.current == Mode.LAYERS and event.unicode.isprintable()):
                # TODO, support more than just layer selection, allow for letter to be begain with, for specific commands. Such as bl (blend layers) <blend-mode> <base-layer-index> <blend-layer-index>. Have these as non-destructive (do not apply them to the layers, only visually present them as such, only on writes would you apply them to the saved image (compile the final image), but not the layers themselves)
                append_str_to_text_buffer(event.unicode)

        if (event.type == pygame.KEYUP):
            if (event.key == Key.move_camera):
                State.move_camera = False

    if (Mode.current == Mode.NORMAL and State.move_camera):
        mouse_pos = list(pygame.mouse.get_pos())
        mouse_pos[0] -= screen_size[0]/2
        mouse_pos[1] -= screen_size[1]/2
        if (abs(mouse_pos[0]) < 5):
            mouse_pos[0] = 0
        if (abs(mouse_pos[1]) < 5):
            mouse_pos[1] = 0
        # increase the speed and frame-rate independant
        mouse_pos[0] *= 2 * delta_time_seconds
        mouse_pos[1] *= 2 * delta_time_seconds
        # Update camera position
        State.camera_position[0] += int(mouse_pos[0])
        State.camera_position[1] += int(mouse_pos[1])

    if (Mode.current == Mode.NORMAL and State.main_mouse_button_held):
        mouse_position_on_editing_surface_position = mouse_pos_on_cur_image_layer()
        if (mouse_position_on_editing_surface_position[0] < 0 or mouse_position_on_editing_surface_position[1] < 0):
            pass
        elif (mouse_position_on_editing_surface_position[0] >= surface_layers[State.current_selected_surface_layer_index].get_width()):
            pass
        elif (mouse_position_on_editing_surface_position[1] >= surface_layers[State.current_selected_surface_layer_index].get_height()):
            pass
        elif (buffer_colors[current_buffer_colors_index] != surface_layers[State.current_selected_surface_layer_index].get_at(mouse_position_on_editing_surface_position)):
            color_copy = pygame.Color(surface_layers[State.current_selected_surface_layer_index].get_at(mouse_position_on_editing_surface_position))
            undo_object = UndoSinglePixel(mouse_position_on_editing_surface_position, color_copy)
            add_undo_to_cur_layer(undo_object)
            log.output(logger.LOG_level("INFO"), f"mouse_position_on_surface: {mouse_position_on_editing_surface_position}")
            log.output(logger.LOG_level("INFO"), f"setting color: {buffer_colors[current_buffer_colors_index]}, at {mouse_position_on_editing_surface_position}")

            surface_layers[State.current_selected_surface_layer_index].set_at(mouse_position_on_editing_surface_position, buffer_colors[current_buffer_colors_index])
            State.unsaved_changes = True

            log.output(logger.LOG_level("INFO"), f"Set color: {surface_layers[State.current_selected_surface_layer_index].get_at(mouse_position_on_editing_surface_position)} at {mouse_position_on_editing_surface_position}")

    screen.fill(bg_color)

    editing_surface_screen_proportionality_xy = (screen_size[0]/640, screen_size[1]/480)
    # Scale from the center of the screen. Not the top left of the surface.
    transformed_editing_surface = pygame.transform.scale(surface_layers[State.current_selected_surface_layer_index], (surface_layers[State.current_selected_surface_layer_index].get_width()*editing_surface_screen_proportionality_xy[0]*State.editing_surface_zoom, surface_layers[State.current_selected_surface_layer_index].get_height()*editing_surface_screen_proportionality_xy[1]*State.editing_surface_zoom))
    transformed_editing_surface_rect = transformed_editing_surface.get_rect(center=(0, 0))
    transformed_editing_surface_pos = transformed_editing_surface_rect.topleft

    editing_surface_average_color = pygame.transform.average_color(surface_layers[State.current_selected_surface_layer_index])
    editing_surface_negated_color = pygame.Color(255 - editing_surface_average_color[0], 255 - editing_surface_average_color[1], 255 - editing_surface_average_color[2])
    if (123 < editing_surface_negated_color[0] < 134 and 123 < editing_surface_negated_color[1] < 134 and 123 < editing_surface_negated_color[2] < 134):
        editing_surface_negated_color[0] += 32
        editing_surface_negated_color[1] += 32
        editing_surface_negated_color[2] += 32
    screen.blit(transformed_editing_surface, camera_transform(transformed_editing_surface_pos))
    if State.display_grid_lines:
        for x in range(-surface_layers[State.current_selected_surface_layer_index].get_width()//2, surface_layers[State.current_selected_surface_layer_index].get_width()//2+1):
            pygame.draw.line(screen, editing_surface_negated_color, camera_transform((x*editing_surface_screen_proportionality_xy[0]*State.editing_surface_zoom, transformed_editing_surface_pos[0])), camera_transform((x*editing_surface_screen_proportionality_xy[0]*State.editing_surface_zoom, transformed_editing_surface.get_height()//2)))
        for y in range(-surface_layers[State.current_selected_surface_layer_index].get_height()//2, surface_layers[State.current_selected_surface_layer_index].get_height()//2+1):
            pygame.draw.line(screen, editing_surface_negated_color, camera_transform((transformed_editing_surface_pos[0], y*editing_surface_screen_proportionality_xy[1]*State.editing_surface_zoom)), camera_transform((transformed_editing_surface.get_width()//2, y*editing_surface_screen_proportionality_xy[1]*State.editing_surface_zoom)))
    
    display_color_rect_size = (screen_size[0]//25, screen_size[1]//25)
    display_color_rect_start_x_position = screen_size[0] - (display_color_rect_size[0]+display_color_rect_horizontal_gap)*10 - display_color_rect_horizontal_gap

    for display_color_index in range(10):
        
        pygame.draw.rect(screen, buffer_colors[display_color_index], ((display_color_rect_start_x_position +  display_color_index*(display_color_rect_size[0]+display_color_rect_horizontal_gap), display_color_rect_screen_verticle_gap), display_color_rect_size))
        if (display_color_index == current_buffer_colors_index):
            pygame.draw.rect(screen, (0, 0, 0), ((display_color_rect_start_x_position + display_color_index*(display_color_rect_size[0]+display_color_rect_horizontal_gap) - 5, display_color_rect_screen_verticle_gap -5), (display_color_rect_size[0]+5, display_color_rect_size[1]+5)), width = 5)

    current_selected_color = buffer_colors[current_buffer_colors_index]
    display_color_rect_text_surface = app_font_object.render(f"{current_selected_color[0]}r{current_selected_color[1]}g{current_selected_color[2]}b{current_selected_color[3]}a", True, (app_text_color))
    display_color_rect_text_background_surface = pygame.Surface((display_color_rect_text_surface.get_width(), display_color_rect_text_surface.get_height()))
    display_color_rect_text_background_surface.fill(app_text_background_color)
    display_color_rect_text_background_surface.set_alpha(app_text_background_alpha)
    screen.blit(display_color_rect_text_background_surface, (screen_size[0] - display_color_rect_text_background_surface.get_width() - 5, display_color_rect_screen_verticle_gap + display_color_rect_size[1] + 5))
    screen.blit(display_color_rect_text_surface, (screen_size[0] - display_color_rect_text_background_surface.get_width() - 5, display_color_rect_screen_verticle_gap + display_color_rect_size[1] + 5))

    display_mode_text_surface = app_font_object.render(f"--{get_mode_type_code_to_str(Mode.current)}--", True, (app_text_color))
    display_mode_text_background_surface = pygame.Surface((display_mode_text_surface.get_width(), display_mode_text_surface.get_height()))
    display_mode_text_background_surface.fill(app_text_background_color)
    display_mode_text_background_surface.set_alpha(app_text_background_alpha)
    screen.blit(display_mode_text_background_surface, (screen_size[0]//8, screen_size[1] - display_mode_text_surface.get_height() -5))
    screen.blit(display_mode_text_surface, (screen_size[0]//8, screen_size[1] - display_mode_text_surface.get_height() -5))

    display_io_buffer_surface = app_font_object.render(f"{State.text_io_buffer}", True, (app_text_color))

    display_input_buffer_background_surface = pygame.Surface((display_io_buffer_surface.get_width(), display_io_buffer_surface.get_height()))
    display_input_buffer_background_surface.fill(app_text_background_color)
    display_input_buffer_background_surface.set_alpha(app_text_background_alpha)
    screen.blit(display_input_buffer_background_surface, (screen_size[0] - display_io_buffer_surface.get_width() - 5, screen_size[1] - display_io_buffer_surface.get_height() -5))
    screen.blit(display_io_buffer_surface, (screen_size[0] - display_io_buffer_surface.get_width() - 5, screen_size[1] - display_io_buffer_surface.get_height() -5))

    ui_display_layer_index.update_text(f"{State.current_selected_surface_layer_index}/{len(surface_layers)}") # TODO: update when the current layer get switched.
    ui_display_layer_index.set_top_right_pos((screen_size[0]-5, display_color_rect_screen_verticle_gap +display_color_rect_size[1] +10 + display_color_rect_text_background_surface.get_height())) # TODO: update only when the window is resized.
    ui_display_layer_index.render(screen)

    if (Mode.current == Mode.RESIZE_SURFACE):
        ui_display_surface_size.render(screen)

    # display errors above input buffer

    pygame.display.update()
