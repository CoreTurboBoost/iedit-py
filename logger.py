import sys, os
import inspect

levels = ["ERROR", "WARNING", "INFO"] 

def get_last_callback (relative_frame = 2):
    total_stack = inspect.stack()
    frameinfo = total_stack[relative_frame][0]
    
    file_path = frameinfo.f_code.co_filename
    filename = os.path.basename(frameinfo.f_code.co_filename)
    line_number = frameinfo.f_lineno
    code = total_stack[relative_frame][4][0]
    return (filename, file_path, line_number, code)

def LOG_level ( name : str ):
    if name in levels:
        return levels.index(name)
    file_line = get_last_callback()
    print(" [ logger ] [ ERROR ] ( FILE =", file_line[0], ", LINE =", file_line[2], ", { CODE =", "\"" + file_line[3][:-1] + "\" } ", ") name provided is not a label for a LOG_level (", name, ")")
    sys.exit()

def add_LOG_level ( name : str, level : int ):
    if level > -1 and level <= len(levels):
        levels.insert(level, name)
        
    else:
        file_line = get_last_callback()
        print(" [ logger ] [ ERROR ] ( FILE =", file_line[0], "LINE=", file_line[2], ", { CODE =", "\"" + file_line[3][:-1] + "\" } ", ") level provided is outside bounds ( 0 to", len(levels), ") given (", level, ") ")
        sys.exit()


def LOG_LEVEL_TO_STR( level : int ):
    if level < len(levels) and level > -1:
        return levels[level]
    file_line = get_last_callback()
    print(" [ logger ] [ ERROR ] ( FILE =", file_line[0], "LINE =", file_line[2], ", { CODE =", "\"" + file_line[3][:-1] + "\" } ", ") level provided is outside bounds ( 0 to", len(levels) - 1, ") given (", level, ") ")
    sys.exit()


def debug_info ( msg : str , relative_frame = 1):
    total_stack = inspect.stack()
    frameinfo = total_stack[relative_frame][0]
    
    filename = os.path.basename(frameinfo.f_code.co_filename)
    line_number = frameinfo.f_lineno
    print(" [ DEBUG ] [ INFO ] ( FILE =", filename, ") ( LINE =", line_number, ") MSG =", msg)

class LOG (object):
    def __init__ (self, file = None):
        self.warnlevel = LOG_level("INFO")
        self.stop_on_level = -1
        self.output_code = False
        self.ignored_files = []
        self.same_print_count = 1
        self.print_buffer = []
        self.stack_print_buffer = []
        self.stack_logs = False

    def ignore_file ( self, filename ):
        if not os.path.exists(filename):
            call_back = get_last_callback()
            print(" [ logger ] [ WARNING ] FILE = " + str(call_back[0]) + " LINE = " + str(call_back[2]) + " CODE = \"" + str(call_back[3][:-1]) + "\"  FILE ", "\"" + filename + "\"", "was not found ")
        self.ignored_files.append(filename)
        
        
    def set_warnlevel( self, level : int ):
        self.warnlevel = level

    def stack( self, level : int, *data ):
        if len(data) == 1:
            data = data[0]
        elif len(data) > 1 :
            tmp = ""
            for string in data:
                tmp += string
                if string[-1] != " ":
                    tmp += " "
            data = tmp

        if level <= self.warnlevel:
            file_line = get_last_callback()
            if self.output_code:
                code_str = "  CODE = \"" + str(file_line[3][:-1]) + "\"" 
            else:
                code_str = ""
            if not ( file_line[0] in self.ignored_files ):
                out = "[ " + str(LOG_LEVEL_TO_STR( level ) + " ] FILE = " + str(file_line[0]) + "  LINE = " + str(file_line[2]) + str(code_str) + "  MSG = " + str(data))
                self.stack_print_buffer.append(out)

                if level <= self.stop_on_level:
                    sys.exit()

    def print_stack ( self ):
        count = []
        print_str = []
        for prt in self.stack_print_buffer:
            if not( prt in print_str ):
                print_str.append(prt)
                count.append (1)
            elif prt in print_str:
                count[print_str.index(prt)] += 1
        self.stack_print_buffer.clear()

        for i, log in enumerate(print_str):
            print(log, " ( x" + str(count[i]) + " ) ")

    def clear_buffer (self):
        if len(self.print_buffer) > 1:
            count = [1]
            print_str = [self.print_buffer[0]]
            for i in range(1, len(self.print_buffer)):
                if not(self.print_buffer[i] == print_str[-1]):
                    print_str.append(self.print_buffer[i])
                    count.append (1)
                elif self.print_buffer[i] == print_str[-1]:
                    count[-1] += 1
                else:
                    print(self.print_buffer[i])

            for i in range(len(print_str)):
                print(print_str[i], " ( x" + str(count[i]) + " ) ")
        else:
            print(self.print_buffer[0])

        self.print_buffer.clear()
    
    def output ( self,  level : int, *data, write_file_path = None ):
        tmp = ""
        for string in data:
            tmp += str(string)
        data = tmp
            
        if level <= self.warnlevel:
            file_line = get_last_callback()
            if self.output_code:
                code_str = "  CODE = \"" + str(file_line[3][:-1]) + "\"" 
            else:
                code_str = ""
            if not( file_line[0] in self.ignored_files ):
                out = "[ " + str(LOG_LEVEL_TO_STR( level ) + " ] FILE = " + str(file_line[0]) + "  LINE = " + str(file_line[2]) + str(code_str) + "  MSG = " + str(data))
                self.print_buffer.append(out)
                if self.stack_logs:

                    if len(self.print_buffer) > 1:
                        count = 1
                        if self.print_buffer[-1] != self.print_buffer[-2]:
                            for i in range(1, len(self.print_buffer)):
                                if self.print_buffer[i-1] == self.print_buffer[i]:
                                    count += 1
                                else:
                                    break
                            print(self.print_buffer[0], " ( x" + str(count) + " ) ")
                            if (write_file_path != None):
                                fileh = open(write_file_path, "a")
                                fileh.write(str(self.print_buffer[0]), "(", "x"+str(count), ")")
                                fileh.write("\n")
                                fileh.close()
                            if not(self.print_buffer[-1] in self.print_buffer[len(self.print_buffer)-1:]):
                                print(self.print_buffer[-1])
                                if (write_file_path != None):
                                    fileh = open(write_file_path, "a")
                                    fileh.write(str(self.print_buffer[-1]))
                                    fileh.write("\n")
                                    fileh.close()
                            self.print_buffer.clear()
                        
                else:
                    print(out)
                    self.print_buffer.pop()
                    if (write_file_path != None):
                        file_mode = "a"
                        fileh = open(write_file_path, file_mode)
                        fileh.write(out)
                        fileh.write("\n")
                        fileh.close()
                if level <= self.stop_on_level:
                    sys.exit()
    
log = LOG()

print(" [ LOGGER LOADED ] ")
