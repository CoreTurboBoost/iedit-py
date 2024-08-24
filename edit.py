#!/bin/env python3

import pygame
import sys
import time

import logger

if (__name__ != "__main__"):
    print("Need to run directly")
    sys.exit(1)

VERSION_MAJOR = 0
VERSION_MINOR = 6
VERSION_PATCH = 2

log = logger.LOG()
log.set_warnlevel(logger.LOG_level("INFO"))

pygame.init()

key_select_mode_select_color = pygame.K_s
key_select_mode_set_color = pygame.K_c
key_resize_editing_surface = pygame.K_r
key_undo_editing_surface_modification = pygame.K_u
key_save_editing_surface = pygame.K_w
key_confirm = pygame.K_RETURN
key_move_camera = pygame.K_m
key_fill_bucket = pygame.K_f
key_quit = pygame.K_q

editing_surface_zoom = 30
editing_surface_max_zoom = 100

argv = sys.argv
argc = len(argv)

if (argc == 1):
    print(f"python3 {argv[0]} --help")

if (argc > 1):
    if (argv[1] == "--help" or argv[1] == "-h"):
        print( "Description: Pixel art editor with key bindings")
        print(f"\'python3 {argv[0]} --version \' for version infomation")
        print(f"Usage: python3 {argv[0]}")
        print(f"Usage: python3 {argv[0]} [Options]")
        print(f"Options:")
        print(f"  -i [file-path]  - input image file from [file-path]")
        print(f"  -o [file-path]  - output image file to [file-path]")
        print(f"  --key-bindings  - output key bindings and exit")
        print(f"Note:")
        print(f" Can only use -i or -o alone (not both at same time)")
        sys.exit()
    if (argv[1] == "--version"):
        print(f"VERSION: {VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}")
        sys.exit()

def assume_or_exception(condition: bool) -> None:
    if (condition):
        Exception(f"condition failed")

input_file_path = None
output_file_path = None
arg_skip_count = 0
for arg_index in range(1, argc):
    if (arg_skip_count > 0):
        arg_skip_count -= 1
        continue

    arg = argv[arg_index]

    if (arg == "-i"):
        if (arg_index +1 >= argc):
            print(f"[{arg_index+1}] option \'-i\' needs argument [file-path]")
            sys.exit()
        if (input_file_path != None):
            print(f"[{arg_index+1}] option \'-i\' can only be given once, (app only supports single file)")
            sys.exit()
        input_file_path = argv[arg_index+1]
    elif (arg == "-o"):
        if (arg_index +1 >= argc):
            print(f"[{arg_index+1}] option \'-o\' needs argument [file-path]")
            sys.exit()
        if (input_file_path != None):
            print(f"[{arg_index+1}] option \'-o\' can only be given once, (app only supports single file)")
            sys.exit()
        output_file_path = argv[arg_index+1]
    elif (arg == "--key-bindings"):
        print("Key bindings (In normal mode):")
        print(" - select color (In normal mode): ", pygame.key.name(key_select_mode_select_color))
        print(" - set color (In normal mode): ", pygame.key.name(key_select_mode_set_color))
        print(" - resize editing surface (In normal mode): ", pygame.key.name(key_resize_editing_surface))
        print(" - undo editing surface modification (In normal mode): ", pygame.key.name(key_undo_editing_surface_modification))
        print(" - save editing surface (In normal mode): ", pygame.key.name(key_save_editing_surface))
        print(" - confirm (In any mode, used for prompts): ", pygame.key.name(key_confirm))
        print(" - fill bucket paint brush (In normal mode): " , pygame.key.name(key_fill_bucket))
        print(" - quit program without saving (or save warning) (In normal mode): ", pygame.key.name(key_quit))
        sys.exit()
    else:
        print(f"[{arg_index+1}] option \'{arg}\' is not recognised")

if (input_file_path != None):
    try:
        input_surface = pygame.image.load(input_file_path)
    except FileNotFoundError:
        print(f"Could not load file \'{input_file_path}\'")
        sys.exit()
    except pygame.error:
        print(f"Pygame could not load in the image, {sys.exc_info()[1]}")
        sys.exit()
    editing_surface = input_surface
    log.output(logger.LOG_level("INFO"), f"editing surface: {editing_surface}")

else:
    editing_surface = pygame.Surface((64, 64), pygame.SRCALPHA)

if (output_file_path != None):
    app_save_filepath_editing_surface = output_file_path

else:
    print("Output file path set to \'a.png\'")
    app_save_filepath_editing_surface = "a.png"
app_state_unsaved_changes = False

mode_type_normal = 0
mode_type_select_color = 1
mode_type_set_color = 2
mode_type_save_file = 3
mode_type_resize_editing_surface = 4
current_mode = mode_type_normal
def get_mode_type_code_to_str(mode_type_code):
    if (mode_type_code == mode_type_normal):
        return "normal"
    elif (mode_type_code == mode_type_select_color):
        return "select color"
    elif (mode_type_code == mode_type_set_color):
        return "set color"
    elif (mode_type_code == mode_type_save_file):
        return "save file"
    elif (mode_type_code == mode_type_resize_editing_surface):
        return "resize surface"
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

current_input_buffer = ""
max_input_buffer_len = 16

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
buffer_undo_objects = []
buffer_undo_max_size = 512

def add_to_undo_buffer(undo_object: UndoObject):
    global buffer_undo_objects
    buffer_undo_objects.append(undo_object)
    if (len(buffer_undo_objects) > buffer_undo_max_size):
        buffer_undo_objects.pop() # Might change to make more robust
def pop_from_undo_buffer() -> UndoObject: # Or return None when empty
    global buffer_undo_objects
    if len(buffer_undo_objects) == 0:
        return None
    return buffer_undo_objects.pop()

display_color_rect_horizontal_gap = 5 # pixels
display_color_rect_screen_verticle_gap = 10 # pixels

app_font_size = 20
app_font_object = pygame.font.Font(None, app_font_size)

app_text_background_alpha = 150

app_state_mouse_main_click_current_frame = False
app_state_mouse_main_click_held = False
app_mouse_last_recored_position = (0, 0)

screen_size = (640, 480)
screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
editing_surface_screen_proportionality_xy = (screen_size[0]/640, screen_size[1]/480)

bg_color = (100, 100, 100)
app_text_color = (0, 0, 0)
app_text_background_color = (255 - app_text_color[0], 255 - app_text_color[1], 255 - app_text_color[2], 100)
max_fps = 60

app_state_move_camera = False
camera_position = [0, 0]
def camera_transform(vec2f_position):
    return (vec2f_position[0] - camera_position[0] + screen_size[0]/2, vec2f_position[1] - camera_position[1] + screen_size[1]/2)

def camera_reverse_transform(vec2f_position):
    return (vec2f_position[0] + camera_position[0] - screen_size[0]/2, vec2f_position[1] + camera_position[1] - screen_size[1]/2)
error_string = ""

previous_frame_time = time.time()
clock = pygame.time.Clock()
while True:
    clock.tick(max_fps)
    fps = clock.get_fps()
    pygame.display.set_caption(f"edit - {app_save_filepath_editing_surface} - {fps : 0.1f}")
    delta_time_seconds = time.time() - previous_frame_time
    previous_frame_time = time.time()

    app_state_mouse_main_click_current_frame = False

    for event in pygame.event.get():
        if (event.type == pygame.QUIT or current_mode == mode_type_normal and event.type == pygame.KEYDOWN and event.key == key_quit):
            pygame.quit()
            sys.exit()

        if (event.type == pygame.WINDOWRESIZED):
            screen_size = (event.x, event.y)
            width, height = screen_size[0]/640, screen_size[1]/480
            average = (width+height)/2
            app_font_size = int(20 * average)
            app_font_object = pygame.font.Font(None, app_font_size)

        if (event.type == pygame.MOUSEWHEEL):
            if (0 < editing_surface_zoom + event.y < editing_surface_max_zoom):
                editing_surface_zoom += event.y

        if (event.type == pygame.MOUSEBUTTONDOWN):
            if (event.button == 1):
                log.output(logger.LOG_level("INFO"), f"Clicked main mouse button")
                app_state_mouse_main_click_current_frame = True
                app_state_mouse_main_click_held = True

        if (event.type == pygame.MOUSEBUTTONUP):
            if (event.button == 1):
                app_state_mouse_main_click_held = False

        if (event.type == pygame.KEYDOWN):

            if (current_mode != mode_type_normal and event.key == pygame.K_ESCAPE):
                log.output(logger.LOG_level("INFO"), f"Escaped to normal mode from {get_mode_type_code_to_str(current_mode)}")
                current_mode = mode_type_normal
                current_input_buffer = ""
            if (current_mode == mode_type_normal and event.key == key_select_mode_select_color):
                current_mode = mode_type_select_color
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(current_mode)}")
                current_input_buffer = ""
            if (current_mode == mode_type_normal and event.key == key_select_mode_set_color):
                current_mode = mode_type_set_color
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(current_mode)}")
                current_input_buffer = ""
            if (current_mode == mode_type_normal and event.key == key_resize_editing_surface):
                current_mode = mode_type_resize_editing_surface
                log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(current_mode)}")
                current_input_buffer = ""
            if (current_mode == mode_type_normal and event.key == key_move_camera):
                app_state_move_camera = True
            if (current_mode == mode_type_normal and event.key == key_undo_editing_surface_modification):
                undo_package = pop_from_undo_buffer()
                if (undo_package != None):
                    log.output(logger.LOG_level("INFO"), f"undoing package {undo_package}")
                    if isinstance(undo_package, UndoSinglePixel):
                        editing_surface.set_at(undo_package.pixel_position, undo_package.color)
                        app_state_unsaved_changes = True
                    elif isinstance(undo_package, UndoBucketFill):
                        paint_tool_bucket(editing_surface, undo_package.pixel_position, undo_package.old_color, undo_package.mask)
                        app_state_unsaved_changes = True
                    elif isinstance(undo_package, UndoResize):
                        editing_surface = undo_package.old_surface
                        app_state_unsaved_changes = True
                    else:
                        log.output(logger.LOG_level("WARNING"), f"undo package {undo_package} is not handles when undo button pressed")
                    log.output(logger.LOG_level("INFO"), f"Applied undo")
            if (current_mode == mode_type_normal and event.key == key_save_editing_surface):
                app_state_unsaved_changes = False
                pygame.image.save(editing_surface, app_save_filepath_editing_surface)
                log.output(logger.LOG_level("INFO"), f"Saved current editing surface to {app_save_filepath_editing_surface}")
            if (current_mode == mode_type_normal and event.key == key_fill_bucket):
                mouse_position = pygame.mouse.get_pos()
                reverse_camera_mouse_position = camera_reverse_transform(mouse_position)
                # assumes editing_surface_screen_proportionality_xy != 0
                # assumes editing_surface_zoom != 0
                mouse_position_on_editing_surface_position = (int(reverse_camera_mouse_position[0]/(editing_surface_screen_proportionality_xy[0]*editing_surface_zoom)), int(reverse_camera_mouse_position[1]/(editing_surface_screen_proportionality_xy[1]*editing_surface_zoom)))
                
                previous_color = editing_surface.get_at(mouse_position_on_editing_surface_position)
                fill_color = buffer_colors[current_buffer_colors_index]
                fill_mask = paint_tool_bucket(editing_surface, pygame.math.Vector2(mouse_position_on_editing_surface_position), fill_color)
                app_state_unsaved_changes = True

                if (fill_mask != None):
                    undo_object = UndoBucketFill(pygame.math.Vector2(mouse_position_on_editing_surface_position), previous_color, fill_mask)
                    add_to_undo_buffer(undo_object)
                else:
                    log.output(logger.LOG_level("WARNING"), f"fill_mask is None, failed to bucket fill")
            if (event.key == key_confirm):	
                if (current_mode == mode_type_select_color):
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered mode {get_mode_type_code_to_str(current_mode)}")
                    current_color_channel = None
                    final_color = buffer_colors[current_buffer_colors_index]
                    current_number_str = ""
                    for char in current_input_buffer:
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

                if (current_mode == mode_type_resize_editing_surface):
                    current_mode = mode_type_normal

                    undo_object = UndoResize(editing_surface)
                    add_to_undo_buffer(undo_object)

                    width = editing_surface.get_width()
                    height = editing_surface.get_height()
                    number_str = ""
                    for char in current_input_buffer:

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
                    editing_surface = pygame.transform.scale(editing_surface, (width, height))
                    app_state_unsaved_changes = True
                    log.output(logger.LOG_level("INFO"), f"Changed editing surface size to ({editing_surface.get_width()}, {editing_surface.get_height()})")

            if (event.key == pygame.K_0 or event.key == pygame.K_KP0):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 9
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "0")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "0"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "0"
            if (event.key == pygame.K_1 or event.key == pygame.K_KP1):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 0
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "1")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "1"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "1"
            if (event.key == pygame.K_2 or event.key == pygame.K_KP2):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 1
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "2")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "2"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "2"
            if (event.key == pygame.K_3 or event.key == pygame.K_KP3):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 2
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "3")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "3"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "3"
            if (event.key == pygame.K_4 or event.key == pygame.K_KP4):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 3
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "4")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "4"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "4"
            if (event.key == pygame.K_5 or event.key == pygame.K_KP5):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 4
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "5")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "5"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "5"
            if (event.key == pygame.K_6 or event.key == pygame.K_KP6):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 5
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "6")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "6"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "6"
            if (event.key == pygame.K_7 or event.key == pygame.K_KP7):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 6
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "7")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "7"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "7"
            if (event.key == pygame.K_8 or event.key == pygame.K_KP8):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 7
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "8")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= max_input_buffer_len):
                        current_input_buffer += "8"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "8"
            if (event.key == pygame.K_9 or event.key == pygame.K_KP9):
                if (current_mode == mode_type_select_color):
                    current_buffer_colors_index = 8
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Entered {get_mode_type_code_to_str(current_mode)}")
                if (current_mode == mode_type_set_color):
                    if (len(current_input_buffer) >= 2):
                        if (current_input_buffer[-1].isdigit() and current_input_buffer[-2].isdigit()):
                            value = int(current_input_buffer[-2] + current_input_buffer[-1] + "9")
                            if (value > 255):
                                continue
                            else:
                                log.output(logger.LOG_level("INFO"), f"Color value is valide: {value}, last two values in buffer {current_input_buffer[-2]} {current_input_buffer[-1]}")
                        else:
                            log.output(logger.LOG_level("INFO"), f"Last two value in buffer no digits: {current_input_buffer[-2]}, {current_input_buffer[-1]}")
                    if (len(current_input_buffer) +1 <= 16):
                        current_input_buffer += "9"
                        log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "9"

            if (event.key == pygame.K_r):
                if (current_mode == mode_type_set_color):
                    current_input_buffer += "r"
                    log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
            if (event.key == pygame.K_g):
                if (current_mode == mode_type_set_color):
                    current_input_buffer += "g"
                    log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
            if (event.key == pygame.K_b):
                if (current_mode == mode_type_set_color):
                    current_input_buffer += "b"
                    log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")
            if (event.key == pygame.K_a):
                if (current_mode == mode_type_set_color):
                    current_input_buffer += "a"
                    log.output(logger.LOG_level("INFO"), f"Entered {current_input_buffer}")

            if (event.key == pygame.K_w):
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "w"
            if (event.key == pygame.K_h):
                if (current_mode == mode_type_resize_editing_surface):
                    if (len(current_input_buffer)+1 <= max_input_buffer_len):
                        current_input_buffer += "h"

            if (event.key == pygame.K_BACKSPACE):
                if (current_mode == mode_type_set_color):
                    current_input_buffer = ""
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Changed mode to normal from set color")
                if (current_mode == mode_type_resize_editing_surface):
                    current_input_buffer = ""
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Changed mode to normal from resize surface")

        if (event.type == pygame.KEYUP):
            if (current_mode == mode_type_normal and event.key == pygame.K_m):
                app_state_move_camera = False

    if (current_mode == mode_type_normal and app_state_move_camera):
        mouse_pos = list(pygame.mouse.get_pos())
        mouse_pos[0] -= screen_size[0]/2
        mouse_pos[1] -= screen_size[1]/2
        if (abs(mouse_pos[0]) < 5):
            mouse_pos[0] = 0
        if (abs(mouse_pos[1]) < 5):
            mouse_pos[1] = 0
        mouse_pos[0] *= 0.06
        mouse_pos[1] *= 0.06
        camera_position[0] += int(mouse_pos[0])
        camera_position[1] += int(mouse_pos[1])

    if (app_state_mouse_main_click_held): #editing in any mode
        mouse_position = pygame.mouse.get_pos()
        reverse_camera_mouse_position = camera_reverse_transform(mouse_position)
        # assumes editing_surface_screen_proportionality_xy != 0
        # assumes editing_surface_zoom != 0
        mouse_position_on_editing_surface_position = (int(reverse_camera_mouse_position[0]/(editing_surface_screen_proportionality_xy[0]*editing_surface_zoom)), int(reverse_camera_mouse_position[1]/(editing_surface_screen_proportionality_xy[1]*editing_surface_zoom)))
        if (mouse_position_on_editing_surface_position[0] < 0 or mouse_position_on_editing_surface_position[1] < 0):
            log.output(logger.LOG_level("ERROR"), f"surface position is negative: {mouse_position_on_editing_surface_position}", write_file_path = "errors.txt")
            log.output(logger.LOG_level("INFO"), f"Data: mouse_pos:{mouse_position}, screen_size:{screen_size}, camera_pos:{camera_position}, revers_cam_pos:{reverse_camera_mouse_position}, proprotionality_xy:{editing_surface_screen_proportionality_xy}, zoom:{editing_surface_zoom}", write_file_path = "errors.txt")
        elif (mouse_position_on_editing_surface_position[0] >= editing_surface.get_width() or mouse_position_on_editing_surface_position[1] >= editing_surface.get_height()):
            log.output(logger.LOG_level("ERROR"), f"surface position is greater or equal surface size: {mouse_position_on_editing_surface_position}", write_file_path = "errors.txt")
            log.output(logger.LOG_level("INFO"), f"Data: mouse_pos:{mouse_position}, screen_size:{screen_size}, camera_pos:{camera_position}, revers_cam_pos:{reverse_camera_mouse_position}, proprotionality_xy:{editing_surface_screen_proportionality_xy}, zoom:{editing_surface_zoom}", write_file_path = "errors.txt")
        elif (buffer_colors[current_buffer_colors_index] != editing_surface.get_at(mouse_position_on_editing_surface_position)):
            color_copy = pygame.Color(editing_surface.get_at(mouse_position_on_editing_surface_position))
            undo_object = UndoSinglePixel(mouse_position_on_editing_surface_position, color_copy)
            add_to_undo_buffer(undo_object)
            log.output(logger.LOG_level("INFO"), f"mouse_position_on_surface: {mouse_position_on_editing_surface_position}")
            log.output(logger.LOG_level("INFO"), f"setting color: {buffer_colors[current_buffer_colors_index]}, at {mouse_position_on_editing_surface_position}")

            editing_surface.set_at(mouse_position_on_editing_surface_position, buffer_colors[current_buffer_colors_index])
            app_state_unsaved_changes = True

            log.output(logger.LOG_level("INFO"), f"Set color: {editing_surface.get_at(mouse_position_on_editing_surface_position)} at {mouse_position_on_editing_surface_position}")

    screen.fill(bg_color)

    editing_surface_screen_proportionality_xy = (screen_size[0]/640, screen_size[1]/480)
    transformed_editing_surface = pygame.transform.scale(editing_surface, (editing_surface.get_width()*editing_surface_screen_proportionality_xy[0]*editing_surface_zoom, editing_surface.get_height()*editing_surface_screen_proportionality_xy[1]*editing_surface_zoom))

    editing_surface_average_color = pygame.transform.average_color(editing_surface)
    editing_surface_negated_color = pygame.Color(255 - editing_surface_average_color[0], 255 - editing_surface_average_color[1], 255 - editing_surface_average_color[2])
    if (123 < editing_surface_negated_color[0] < 134 and 123 < editing_surface_negated_color[1] < 134 and 123 < editing_surface_negated_color[2] < 134):
        editing_surface_negated_color[0] += 32
        editing_surface_negated_color[1] += 32
        editing_surface_negated_color[2] += 32
    screen.blit(transformed_editing_surface, camera_transform((0, 0)))
    for x in range(editing_surface.get_width()+1):
        pygame.draw.line(screen, editing_surface_negated_color, camera_transform((x*editing_surface_screen_proportionality_xy[0]*editing_surface_zoom, 0)), camera_transform((x*editing_surface_screen_proportionality_xy[0]*editing_surface_zoom, transformed_editing_surface.get_height())))
    for y in range(editing_surface.get_height()+1):
        pygame.draw.line(screen, editing_surface_negated_color, camera_transform((0, y*editing_surface_screen_proportionality_xy[1]*editing_surface_zoom)), camera_transform((transformed_editing_surface.get_width(), y*editing_surface_screen_proportionality_xy[1]*editing_surface_zoom)))
    
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

    display_mode_text_surface = app_font_object.render(f"--{get_mode_type_code_to_str(current_mode)}--", True, (app_text_color))
    display_mode_text_background_surface = pygame.Surface((display_mode_text_surface.get_width(), display_mode_text_surface.get_height()))
    display_mode_text_background_surface.fill(app_text_background_color)
    display_mode_text_background_surface.set_alpha(app_text_background_alpha)
    screen.blit(display_mode_text_background_surface, (screen_size[0]//8, screen_size[1] - display_mode_text_surface.get_height() -5))
    screen.blit(display_mode_text_surface, (screen_size[0]//8, screen_size[1] - display_mode_text_surface.get_height() -5))

    display_input_buffer_surface = app_font_object.render(f"{current_input_buffer}", True, (app_text_color))

    display_input_buffer_background_surface = pygame.Surface((display_input_buffer_surface.get_width(), display_input_buffer_surface.get_height()))
    display_input_buffer_background_surface.fill(app_text_background_color)
    display_input_buffer_background_surface.set_alpha(app_text_background_alpha)
    screen.blit(display_input_buffer_background_surface, (screen_size[0] - display_input_buffer_surface.get_width() - 5, screen_size[1] - display_input_buffer_surface.get_height() -5))
    screen.blit(display_input_buffer_surface, (screen_size[0] - display_input_buffer_surface.get_width() - 5, screen_size[1] - display_input_buffer_surface.get_height() -5))

    if (current_mode == mode_type_resize_editing_surface):
        editing_surface_size_text_surface = app_font_object.render(f"{editing_surface.get_width()}w {editing_surface.get_height()}h", True, (app_text_color))
        editing_surface_size_text_background_surface = pygame.Surface((editing_surface_size_text_surface.get_width(), editing_surface_size_text_surface.get_height()))
        editing_surface_size_text_background_surface.fill(app_text_background_color)
        editing_surface_size_text_background_surface.set_alpha(app_text_background_alpha)
        screen.blit(editing_surface_size_text_background_surface, (5, 5))
        screen.blit(editing_surface_size_text_surface, (5, 5))

    # display errors above input buffer

    #debug

    pygame.display.update()
