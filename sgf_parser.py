#!/usr/bin/python3
# -*- coding: utf-8 -*-
from zipfile import ZipFile
import os, sys
import pickle

sys.setrecursionlimit(10000)

class SGFParser:
  
    def __init__(self, sgf_filename):
        sgf_data = ''
        ext = os.path.splitext(sgf_filename)[1]
        if ext == '.sgf':
            with open(sgf_filename) as f:
                sgf_data = f.read()
        elif ext == '.zip':
            with ZipFile(sgf_filename) as input_zip:
                sgf_files = [f for f in input_zip.namelist() if os.path.splitext(f)[1] == '.sgf']
                if (len(sgf_files)) > 1:
                    raise Exception('More than one SGF file in zip file')
                elif len(sgf_files) == 0:
                    raise Exception('No SGF file in zip file')

                sgf_data = input_zip.read(sgf_files[0]).decode("utf-8") 
        else:
            raise Exception(ext + ' files not handled')
        
        iterator = SGFIterator()
        self.root_node = SGFNode(None, sgf_data, 0, 0, iterator)

        self.total_mistake_count = 0

    def save(self, pickle_filename):
        with open(pickle_filename, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(pickle_filename):
        with open(pickle_filename, 'rb') as f:
            return pickle.load(f)

# this class encapsulates a single integer to be able to pass it as ref in python
class SGFIterator:
    def __init__(self):
        self.index = 0
    def increment(self):
        self.index += 1

class SGFNode:
    def __init__(self, parent, sgf_code, branch_depth, this_depth, iterator):
        self.parent = parent
        self.children = []
        self.properties = []

        self.visit_count = 0
        self.mistake_count = 0

        while iterator.index < len(sgf_code):
            c = sgf_code[iterator.index]
            # new node
            if c == ';':
                iterator.increment()
                self.children.append(SGFNode(self, sgf_code, branch_depth, this_depth + 1, iterator))
                if this_depth > branch_depth:
                    break
            elif c == '(':
                branch_depth = this_depth
            elif c == ')':
                break
            elif c.isalpha():
                self.properties.append(SGFProperty(sgf_code, iterator))
            elif c == '[':
                self.properties.append(SGFProperty(sgf_code, iterator , self.properties[-1].tag))

            iterator.increment()
        
    def print(self, tab = ''):
        properties_str = [str(p) for p in self.properties]
        print (tab, properties_str)
        for c in self.children:
            c.print(tab + '\t')

class SGFProperty:

    def __init__(self, sgf_code, iterator, tag_name = ''):
        self.tag = tag_name
        self.val = ''

        read_tag = True
        while iterator.index < len(sgf_code):
            c = sgf_code[iterator.index]
            if c == '[':
                read_tag = False
            elif c == ']':
                break
            else:
                if read_tag:
                    if c.isalpha():
                        self.tag += c
                else:
                    self.val += c
            iterator.increment()

    def __str__(self):
        return self.tag + '=' + self.val

if __name__ == '__main__':
    sgf_parser = SGFParser('test.sgf')
    sgf_parser.root_node.print()