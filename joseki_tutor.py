#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tkinter import Tk, Canvas, Button, Label, Text, Frame, BOTH
from enum import Enum
from sgf_parser import SGFParser
import sys, os
import random
import time

board_size = 19
line_color = "#000"
background_color = "#fA6"
line_spacing = 20
hoshi_size = 6
start_x = 2*line_spacing
start_y = 2*line_spacing
stone_color = Enum('stone_color', 'black white')
black_stone_color = "#000"
white_stone_color = "#fff"
stone_size = line_spacing - 2
possibility_color = "#f93"
tenuky_coords = (4, 15)
move_tags = {'B', 'W'}
white_move_delay = 0.5

pickle_filename = 'joseki.pkl'
# sgf_file = 'test.sgf'
sgf_filename = '2014.02.25_KJD.zip'

class Stone:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

class GUI(Frame):
  
    def __init__(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        super().__init__()

        self.goban_canvas = Canvas(self.master, width = start_x + board_size * line_spacing,
                                    height = start_y + board_size * line_spacing)
        self.goban_canvas.bind("<Button-1>", self.goban_click)
        self.goban_canvas.grid(row=0, column=0, columnspan=2, rowspan=1)

        self.comment_zone = Text(self.master)
        self.comment_zone.grid(row=0, column=2, columnspan=3, rowspan=1)
        self.comment_zone.configure(state='disabled')

        self.mistake_zone = Label(self.master)
        self.mistake_zone.grid(row=1, column=0)

        self.info_zone = Label(self.master, fg="red")
        self.info_zone.grid(row=1,column=1)

        not_mistake_button = Button(self.master, text="Not a mistake", command=self.not_mistake)
        not_mistake_button.grid(row=1, column=2)
        
        restart_button = Button(self.master, text="Restart", command=self.init)
        restart_button.grid(row=1, column=3)

        quit_button = Button(self.master, text="Quit", command=self.close)
        quit_button.grid(row=1, column=4)

        self.sgf_parser = None
        if os.path.exists(pickle_filename):
            self.sgf_parser = SGFParser.load(pickle_filename)
        else:
            self.sgf_parser = SGFParser(sgf_filename)
        assert self.sgf_parser is not None
        self.sgf_tree = self.sgf_parser.root_node

        self.init() 

        self.root.mainloop()

    def init(self):
        self.comment_zone.delete('1.0', 'end')
        self.info_zone['text'] = ''
        self.update_mistake_zone()
        
        # self.update()
        self.current_sgf_node = None
        self.stones = []
        self.possibilities = {}
        self.advance_to_first_move(self.sgf_tree)
         
        self.master.title("Joseki Tutor") 
        
        self.stone_coordinates = set()
        self.draw_goban(board_size)
        self.compute_possible_next_moves()
        self.draw_possibilities()

        self.end_of_variation = False

    def update_mistake_zone(self):
        self.mistake_zone['text'] = 'Total mistakes : ' + str(self.sgf_parser.total_mistake_count)

    def close(self):
        self.sgf_parser.save(pickle_filename)
        self.root.destroy()

    def advance_to_first_move(self, node, stop_on = {'B', 'W'}):
        for p in node.properties:
            if p.tag in stop_on:
                # self.stones.append(self.property_to_stone(p))
                self.current_sgf_node = node.parent
                return
        for c in node.children:
            self.advance_to_first_move(c, stop_on)


    def property_to_stone(self, p):
        x = 0
        y = 0
        if p.val == '':
            x,y = tenuky_coords
        else:
            x = self.get_coord(p.val[0]) + 1
            y = self.get_coord(p.val[1]) + 1
        color = stone_color.black if p.tag in ['AB', 'B'] else stone_color.white
        return Stone(x, y, color)

    def get_coord(self, sgf_char_coord):
        ascii = ord(sgf_char_coord.lower())
        if ascii < 97 or ascii > 116:
            raise Exception("Invalid coordinate specified in sgf : " + sgf_char_coord)
        return ascii - 97

    def draw_goban(self, board_size):
        # self.stone_coordinates = set()
        # draw board wood
        self.goban_canvas.create_rectangle(start_x - line_spacing, start_y - line_spacing, 
                                            (board_size+2) * line_spacing, (board_size+2) * line_spacing, 
                                            outline=background_color, fill=background_color)
        
        # draw lines
        for i in range(board_size):
            self.goban_canvas.create_line(start_x, start_y + i * line_spacing, 
                                        start_x + (board_size-1) * line_spacing, start_y + i * line_spacing, 
                                        fill=line_color)
            self.goban_canvas.create_line(start_x + i * line_spacing, start_y, 
                                            start_x + i * line_spacing, start_y + (board_size-1) * line_spacing, 
                                            fill=line_color)

        # draw hoshi    
        for i in range(board_size+1):
            for j in range(board_size+1):
                if (i-4)%6 == 0 and (j-4)%6 == 0:
                    self.goban_canvas.create_oval(start_x + (i-1)*line_spacing - hoshi_size/2, 
                                                start_y + (j-1)*line_spacing - hoshi_size/2,
                                                start_x + (i-1)*line_spacing + hoshi_size/2, 
                                                start_y + (j-1)*line_spacing + hoshi_size/2,
                                                outline=line_color, fill=line_color)

        # draw stones
        stone = None
        for stone in self.stones:
            self.draw_stone(stone)
        self.current_color = stone_color.black if (stone is None or stone.color is stone_color.white) else stone_color.white

    def compute_possible_next_moves(self):
        self.possibilities = {}
        for c in self.current_sgf_node.children:
            for p in c.properties:
                if p.tag in move_tags:
                    stone = self.property_to_stone(p)
                    self.possibilities[stone.x, stone.y] = c

    def draw_possibilities(self):
        i = 1
        for stone_x, stone_y in self.possibilities.keys():
            x, y = self.get_canvas_coord(stone_x, stone_y)
            self.goban_canvas.create_rectangle(x - stone_size/3, y - stone_size/3, x + stone_size/3, y + stone_size/3,
                                                outline=possibility_color, fill=possibility_color)
            self.goban_canvas.create_text(x, y, text=str(i))
            i += 1

    def redraw_goban(self):
        self.stone_coordinates = set()
        self.draw_goban(board_size)
        self.update()

    def get_canvas_coord(self, stone_x, stone_y):
        return start_x + (stone_x - 1) * line_spacing, start_y + (stone_y - 1) * line_spacing

    def draw_stone(self, stone):
        if (stone.x, stone.y) in self.stone_coordinates:
            return
        x, y = self.get_canvas_coord(stone.x, stone.y)
        if stone.color is stone_color.black:
            self.goban_canvas.create_oval(x - stone_size/2, y - stone_size/2, x + stone_size/2, y + stone_size/2, 
                                        outline=black_stone_color, fill=black_stone_color)
        elif stone.color is stone_color.white:
            self.goban_canvas.create_oval(x - stone_size/2, y - stone_size/2, x + stone_size/2, y + stone_size/2, 
                                        outline=white_stone_color, fill=white_stone_color)
        else:
            raise ValueError("Invalid stone color")

        self.stone_coordinates.add((stone.x, stone.y))
        self.change_color()
    
    def change_color(self):
        self.current_color = stone_color.black if self.current_color is stone_color.white else stone_color.white

    def display_comments(self):
        for p in self.current_sgf_node.properties:
            if p.tag == 'C':
                self.comment_zone.configure(state='normal')
                self.comment_zone.delete('1.0', 'end')
                self.comment_zone.insert('insert', p.val)
                self.comment_zone.configure(state='disabled')

    def goban_click(self, event):
        if self.end_of_variation:
            return
        x = round((event.x - start_x) * 1.0 / line_spacing) + 1
        y = round((event.y - start_y) * 1.0 / line_spacing) + 1
        if x > board_size or y > board_size:
            return
        if (x, y) in self.stone_coordinates:
            return
        if (x,y) not in self.possibilities:
            print(x,y)
            print (self.possibilities)
            self.current_sgf_node.mistake_count += 1
            self.sgf_parser.total_mistake_count += 1
            self.update_mistake_zone()
            self.draw_possibilities()
            return
        new_stone_human = Stone(x, y, self.current_color)
        self.stones.append(new_stone_human)
        self.current_sgf_node = self.possibilities[(x,y)]
        self.current_sgf_node.visit_count += 1
        
        self.compute_possible_next_moves()
        self.redraw_goban()

        if len(self.current_sgf_node.children) == 0:
            self.info_zone['text'] = 'END OF VARIATION'
            self.end_of_variation = True
            return

        time.sleep(white_move_delay)

        next_move = self.get_next_white_move()
        assert next_move is not None
        new_stone_computer = Stone(next_move[0], next_move[1], self.current_color)
        self.stones.append(new_stone_computer)

        self.current_sgf_node = self.possibilities[next_move]
        self.current_sgf_node.visit_count += 1
        
        self.compute_possible_next_moves()
        self.redraw_goban()
        self.display_comments()

        if len(self.current_sgf_node.children) == 0:
            self.info_zone['text'] = 'END OF VARIATION'
            self.end_of_variation = True
            return

    def get_next_white_move(self):
        max_ratio = 0
        never_visited = []
        for pos, node in self.possibilities.items():
            if node.visit_count == 0:
                never_visited.append(pos)
                continue
            # we add the 1/N term to give a chance of visit to every node
            max_ratio += (1.0 / len(self.possibilities.keys()) + node.mistake_count) / node.visit_count

        # we select in priority nodes that have never been visited
        if len(never_visited) > 0:
            return random.choice(never_visited)

        print('visits, ratio: ', max_visits, max_ratio)

        # # some of the nodes have been visited but no mistake has been made
        # if max_ratio == 0.0:
        #     pick = random.uniform(0, max_visits)
        #     current = 0
        #     for pos, node in self.possibilities.items():
        #         current += node.visit_count
        #         if current >= pick:
        #             return pos
        #     assert(True)
            
        # some of the nodes have been visited
        pick = random.uniform(0, max_ratio)
        current = 0
        for pos, node in self.possibilities.items():
            current += (1.0 / len(self.possibilities.keys()) + node.mistake_count) / node.visit_count

            print ('current, pick :', current, pick)
            if current >= pick:
                return pos

    def not_mistake(self):
        self.current_sgf_node.mistake_count -= 1
        self.sgf_parser.total_mistake_count -= 1
        self.update_mistake_zone()

    def undo(self):
        pass
        # self.stones.pop()
        # self.redraw_goban()

        # print( self.current_color)
        # self.change_color()
    

def main():
    gui = GUI()

if __name__ == '__main__':
    main()