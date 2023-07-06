
import pygame
import sys
import time

import logger

VERSION_MAJOR = 0
VERSION_MINOR = 2
VERSION_PATCH = 0

log = logger.LOG()
log.set_warnlevel(logger.LOG_level("INFO"))

pygame.init()

argv = sys.argv
argc = len(argv)

if (argc > 1):
    if (argv[1] == "--help" or argv[1] == "-h"):
        print("Description: Pixrl art editor with key bindings")

key_select_mode_select_color = pygame.K_s
key_select_mode_set_color = pygame.K_c
key_resize_editing_surface = pygame.K_r
key_undo_editing_surface_modification = pygame.K_u
key_save_editing_surface = pygame.K_w
key_confirm = pygame.K_RETURN

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

current_input_buffer = ""
max_input_buffer_len = 16

buffer_colors = []
current_buffer_colors_index = 0

for _ in range(10):
    buffer_colors.append(pygame.Color(255, 255, 255, 255))

editing_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
editing_surface_size = (32, 32)
editing_surface_zoom = 30
editing_surface_max_zoom = 100

buffer_undo_editing_surface_edit = []
buffer_undo_max_size = 512

display_color_rect_horizontal_gap = 5 # pixels
display_color_rect_screen_verticle_gap = 10 # pixels

app_font_size = 20
app_font_object = pygame.font.Font(None, app_font_size)

app_text_background_alpha = 150

app_save_filepath_editing_surface = "a.png" # a.png for testing (acctual should be None)
app_state_unsaved_changes = False

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
        if (event.type == pygame.QUIT or current_mode == mode_type_normal and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
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
            if (current_mode == mode_type_normal and event.key == pygame.K_m):
                app_state_move_camera = True
            if (current_mode == mode_type_normal and event.key == key_undo_editing_surface_modification):
                if (len(buffer_undo_editing_surface_edit) > 0):
                    undo_package = buffer_undo_editing_surface_edit.pop(0)
                    log.output(logger.LOG_level("INFO"), f"undoing package ({undo_package[0]}, {undo_package[1]})")
                    editing_surface.set_at(undo_package[0], undo_package[1])
                    log.output(logger.LOG_level("INFO"), f"Applied undo")
            if (current_mode == mode_type_normal and event.key == key_save_editing_surface):
                pygame.image.save(editing_surface, app_save_filepath_editing_surface)
                log.output(logger.LOG_level("INFO"), f"Saved current editing surface to {app_save_filepath_editing_surface}")
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
                    log.output(logger.LOG_level("INFO"), f"resize mode not implemented yet")
                    current_mode = mode_type_resize_editing_surface
                    pass

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

            if (event.key == pygame.K_BACKSPACE):
                if (current_mode == mode_type_set_color):
                    current_input_buffer = ""
                    current_mode = mode_type_normal
                    log.output(logger.LOG_level("INFO"), f"Changed mode to normal from set color")

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
            sys.exit()
        elif (mouse_position_on_editing_surface_position[0] >= editing_surface.get_width() or mouse_position_on_editing_surface_position[1] >= editing_surface.get_height()):
            log.output(logger.LOG_level("ERROR"), f"surface position is greater or equal surface size: {mouse_position_on_editing_surface_position}", write_file_path = "errors.txt")
            log.output(logger.LOG_level("INFO"), f"Data: mouse_pos:{mouse_position}, screen_size:{screen_size}, camera_pos:{camera_position}, revers_cam_pos:{reverse_camera_mouse_position}, proprotionality_xy:{editing_surface_screen_proportionality_xy}, zoom:{editing_surface_zoom}", write_file_path = "errors.txt")
            sys.exit()
        elif (buffer_colors[current_buffer_colors_index] != editing_surface.get_at(mouse_position_on_editing_surface_position)):
            color_copy = pygame.Color(editing_surface.get_at(mouse_position_on_editing_surface_position))
            buffer_undo_editing_surface_edit.insert(0, (mouse_position_on_editing_surface_position, color_copy))
            if (len(buffer_undo_editing_surface_edit) > buffer_undo_max_size):
                buffer_undo_editing_surface_edit.pop(-1)
            log.output(logger.LOG_level("INFO"), f"mouse_position_on_surface: {mouse_position_on_editing_surface_position}")
            log.output(logger.LOG_level("INFO"), f"setting color: {buffer_colors[current_buffer_colors_index]}, at {mouse_position_on_editing_surface_position}")

            editing_surface.set_at(mouse_position_on_editing_surface_position, buffer_colors[current_buffer_colors_index])

            log.output(logger.LOG_level("INFO"), f"Set color: {editing_surface.get_at(mouse_position_on_editing_surface_position)} at {mouse_position_on_editing_surface_position}")

    screen.fill(bg_color)

    editing_surface_screen_proportionality_xy = (screen_size[0]/640, screen_size[1]/480)
    transformed_editing_surface = pygame.transform.scale(editing_surface, (editing_surface.get_width()*editing_surface_screen_proportionality_xy[0]*editing_surface_zoom, editing_surface.get_height()*editing_surface_screen_proportionality_xy[1]*editing_surface_zoom))

    editing_surface_average_color = pygame.transform.average_color(editing_surface)
    editing_surface_negated_color = pygame.Color(255 - editing_surface_average_color[0], 255 - editing_surface_average_color[1], 255 - editing_surface_average_color[2])
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

    # display errors above input buffer

    #debug

    pygame.display.update()
