from tkinter import Toplevel, Button
from simulator.environment import Environment
from tkinter import *
from tkinter import ttk
from enum import Enum
from math import fabs, floor
from collections import deque

#Subclass of the tkinters Canvas object. Contains methods
#for setting a graph model and drawing a graph, and changing
#the vertices' colors.
class PixelDisplay(Canvas):
    cWi = 500
    cHi = 500

    def __init__(self, parent):
        self.queue = deque([])
        self.model = None
        self.width = self.cWi
        self.height = self.cHi
        self.padding = int(self.width/64)
        self.parent = parent
        self.offset = 1
        self.event_rate = 400
        super().__init__(parent, bg='white', width=self.width, height=self.height, highlightthickness=0)

    def set_rate(self, n):
        self.event_rate = n

    def set_model(self, model):
        self.model = model

    def get_model(self):
        return self.model


    def draw(self):
        '''
        Draw will call itself and redraw (colorize nodes) as long
        as the display is in running mode or there are timeslices left
        in the queue. The queue of timeslices allow the algorithm to run at
        full speed while the display is delaying the rendering, so it is easy to
        watch it's progress

        Draw will pop a timeslice from the draw queue, and
        use it's data to draw the partial solution on screen.
        Each cell will be assigned a color, and a arrow/point to indicate
        direction the cell gives its output.
        '''
        if len(self.queue)>0:
            timeslice = self.queue.popleft()
            if timeslice:
                self.draw_model(timeslice)


        if not self.stopped or len(self.queue) > 0:
            self.after(self.event_rate, self.draw)

    def colorize_item(self, item, color):
        self.itemconfig(item, fill=color)


    def draw_label(self, x_pos, y_pos, w, h, text,t="label", c="black"):
        x = self.translate_x(x_pos)
        y = self.translate_y(y_pos)
        w = self.translate_y(x_pos + w)
        h = self.translate_y(y_pos + h)
        penalty = len(text)
        font_size = 35 -penalty*2
        font = ("Helvetica", font_size, "bold")
        self.create_text((x+w)/2, (y+h)/2, text=text, tags=t, fill=c, font=font)

    #Method for drawing a graph from a ProblemModel.
    #Draws the model and add tags so individual nodes can later
    #be changed.
    def draw_model(self, timeslice):
        pass

    def start(self):
        self.stopped = False
        self.draw()

    def stop(self):
        self.stopped = True

    #The actual x position of the graph element on screen
    def translate_x(self, x):
        self.padding = 0
        x_norm = fabs(self.min_x) + x
        available_width = min(self.width, self.height)
        x_screen = (self.padding/2) + x_norm*(float((available_width-self.padding)/self.w))
        return x_screen

    #The actual y position of the graph element on screen
    def translate_y(self, y):
        self.padding = 0
        available_height= min(self.width, self.height)
        y_norm = fabs(self.min_y) + y
        y_screen = (self.padding/2) + y_norm*(float((available_height-self.padding)/self.h))
        return y_screen

    def reset(self):
        self.delete(ALL)

    def set_padding(self, padding):
        self.padding = padding

    #draws a cell.
    def draw_pixel(self, x,y, w, h, c, tag=""):
        self.create_rectangle(self.translate_x(x),
            self.translate_y(y),
            self.translate_x(x+w),
            self.translate_y(y+h),
            fill=c,
            tags=tag)

    def draw_rounded(self, x_pos, y_pos, width, height, color, rad=5, tags="", padding=0, line="black"):
        x = self.translate_x(x_pos)+padding
        y = self.translate_y(y_pos)+padding
        w = self.translate_x(x_pos+width)-padding
        h = self.translate_y(y_pos+height)-padding
        self.create_oval(x, y, x +rad, y + rad, fill=color, tag=tags, width=1, outline=line)
        self.create_oval(w -rad, y, w, y + rad, fill=color, tag=tags, width=1, outline=line)
        self.create_oval(x, h-rad, x +rad, h, fill=color, tag=tags, width=1, outline=line)
        self.create_oval(w-rad, h-rad, w , h, fill=color, tag=tags, width=1, outline=line)
        self.create_rectangle(x + (rad/2.0), y, w-(rad/2.0), h, fill=color, tag=tags, width=0)
        self.create_rectangle(x , y + (rad/2.0), w, h-(rad/2.0), fill=color, tag=tags, width=0)

    def set_dimension(self, max_x, max_y, min_x, min_y):
        self.w = fabs(min_x) + max_x
        self.h = fabs(min_y) + max_y
        self.max_x = max_x
        self.max_y = max_y
        self.min_y = min_y
        self.min_x = min_x

    #If window is resized all elements in canvas are scaled up/down
    #along with the window. A new width and height and padding is set.
    #Done so display stays consistent if new model is set.
    def on_resize(self,event):
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        self.padding = int(self.width/64)
        self.config(width=self.width, height=self.height)
        self.scale("all",0,0,wscale,wscale)

    def event(self, data):
        self.queue.append(data)

class FlatlandsDisplay(PixelDisplay):

    def __init__(self, parent, dim):
        super().__init__(parent)
        self.dim = dim
        self.bg = "#bbada0"
        self.empty_cell = "#ccc0b3"
        self.set_dimension(self.dim, self.dim, 0, 0 )
        self.draw_board()

    def draw_board(self):
        self.reset()
        self.draw_pixel(0, 0, self.dim, self.dim, self.bg, tag="bg")
        for i in range(self.dim):
            for j in range(self.dim):
                self.draw_rounded(i,j, 1, 1,  self.empty_cell, padding=2, line=self.bg, tags="bg")


    def draw_model(self, timeslice):
        if timeslice:
            x,y,dir,b = timeslice
            self.delete("Piece")
            for i in range(self.dim):
                for j in range(self.dim):
                    tile = b[i][j]
                    if tile > 0:
                        self.draw_piece("Piece", j, i, tile)
            self.draw_piece("Piece", x,y, 3)


    def draw_piece(self, piece_id, x, y, piece_type):
        self.draw_rounded(x,y, 1, 1,  self._get_color(piece_type), padding=8, line=self.bg, tags=piece_id)
        #self.draw_label( x,y, 1,1, str(piece_id), t=piece_id)

    def _get_color(self, type):
        if type == 1:
            return "green"
        elif type == 2:
            return "red"
        elif type ==3:
            return "blue"
        return "black"


class ResultDialog(object):
    '''

    '''
    def __init__(self, parent, individual, config):
        self.config = config
        self.individual = individual
        #TODO: Generate a new scenario. But what to do for static?
        dim = self.config["fitness"]["flatlands"]["parameters"]["grid_dimension"]
        self.scenario = Environment(dim)

        top = self.top = Toplevel(parent)
        top.title("Flatlands - results")
        self.canvas = FlatlandsDisplay(top, dim)
        self.canvas.set_model(self.scenario)
        self.canvas.pack(pady=5)
        v = StringVar()
        def callback(*args):
            self.canvas.set_rate(int(v.get()))

        w = Scale(top, from_=200, to=1000, command=callback,orient=HORIZONTAL, variable=v)
        w.pack()
        w.set(400)
        b = Button(top, text="OK", command=self.ok)
        b.pack(pady=5)
        self.record_agent()

    def record_agent(self):
        p = self.individual.phenotype_container.get_ANN()
        self.scenario.score_agent(p, 60)
        recording = self.scenario.get_recording()
        print(recording)
        for t in recording:
            self.canvas.event(t)
        self.canvas.start()

    def ok(self):

        self.top.destroy()