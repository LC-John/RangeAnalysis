# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 15:24:30 2018

@author: DrLC
"""

import re
import symtab

PATTERN_INT = re.compile(r"((\+|-)?[0-9]+)")
PATTERN_FP = re.compile(r"((\+|-)?\d+(\.\d*)?((e|E)(\+|-)?\d+))|((\+|-)?\d+\.\d+)")
PATTERN_VAR = re.compile(r"(([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9]+)|([A-Za-z][A-Za-z0-9]+\.[A-Za-z0-9]+)|_[A-Za-z0-9]*)")
PATTERN_FUNC = re.compile(r"([A-Za-z0-9]+( |\t)*\(.*\))")

class Compare(object):
    
    def __init__(self, line=""):
        
        line = line.strip()
        self.__op = None
        if "==" in line:
            self.__op = "=="
        elif "!=" in line:
            self.__op = "!="
        elif ">=" in line:
            self.__op = ">="
        elif "<=" in line:
            self.__op = "<="
        elif "<" in line:
            self.__op = "<"
        elif ">" in line:
            self.__op = ">"
        else:
            assert False, "No valid comp op in \""+line+"\""
        line = line.split(self.__op)
        self.__left = line[0].strip()
        if PATTERN_VAR.match(self.__left) is not None:
            self.__left_prop = "var"
        elif PATTERN_FP.match(self.__left) is not None:
            self.__left_prop = "fp"
        elif PATTERN_INT.match(self.__left) is not None:
            self.__left_prop = "int"
        else: assert False, "Invalid left token \""+self.__left+"\""
        self.__right = line[-1].strip()
        if PATTERN_VAR.match(self.__right) is not None:
            self.__right_prop = "var"
        elif PATTERN_FP.match(self.__right) is not None:
            self.__right_prop = "fp"
        elif PATTERN_INT.match(self.__right) is not None:
            self.__right_prop = "int"
        else: assert False, "Invalid right token \""+self.__right+"\""
        
    def __str__(self):
        
        return self.__left + " " +self.__op + " " + self.__right
        
    def debug(self):
        
        print ("      Condition: " + self.__left + " " +self.__op + " " + self.__right)
        
    def get_left(self):     return self.__left
    def get_right(self):    return self.__right
    def get_op(self):       return self.__op
    def get_left_prop(self):    return self.__left_prop
    def get_right_prop(self):    return self.__right_prop

class Assign(object):
    
    def __init__(self, line=""):
        
        line = line.strip().strip("#").strip().split("=")
        self.__left = line[0].strip()
        assert PATTERN_VAR.match(self.__left) is not None, \
            "Invalid left token \""+self.__left+"\""
        tmp_right = line[1].strip().strip(";").strip()
        self.__source = []
        self.__source_prop = []
        if "PHI" in tmp_right:
            self.__op = "phi"
            tmp_right = re.findall(r"<.*>", tmp_right)[0].strip("<>").split(",")
            for i in tmp_right:
                tmp = i.strip()
                assert PATTERN_VAR.match(tmp) is not None, \
                    "Invalid token \"" + tmp + "\""
                self.__source.append(tmp)
                self.__source_prop.append("var")
        elif (" + " in tmp_right or " - " in tmp_right
              or " * " in tmp_right or " / " in tmp_right):
            if "+" in tmp_right: self.__op = "+"
            elif "-" in tmp_right: self.__op = "-"
            elif "*" in tmp_right: self.__op = "*"
            elif "/" in tmp_right: self.__op = "/"
            else: self.__op = None
            tmp_right = tmp_right.split(self.__op)
            for i in tmp_right:
                tmp = i.strip()
                self.__source.append(tmp)
                if PATTERN_VAR.search(tmp) is not None:
                    self.__source_prop.append("var")
                elif PATTERN_FP.search(tmp) is not None:
                    self.__source_prop.append("fp")
                elif PATTERN_INT.search(tmp) is not None:
                    self.__source_prop.append("int")
                else:
                    assert False, "Invalid token \"" + tmp + "\""
        else:
            self.__op = "assign"
            tmp = tmp_right.strip().strip(";").strip()
            self.__source.append(tmp)
            if PATTERN_FUNC.match(tmp) is not None:
                self.__source_prop.append("func")
            elif PATTERN_VAR.search(tmp) is not None:
                self.__source_prop.append("var")
            elif PATTERN_FP.search(tmp) is not None:
                self.__source_prop.append("fp")
            elif PATTERN_INT.search(tmp) is not None:
                self.__source_prop.append("int")
            else:
                assert False, "Invalid token \"" + tmp + "\""
                
    def __str__(self):
        
        ret = ""
        if self.__op == 'phi':
            ret += "# "
        ret += self.__left + " = "
        if self.__op == 'phi':
            ret += "PHI <"
            for i in range(len(self.__source)):
                if i == 0: ret += self.__source[i]
                else: ret += ", " + self.__source[i]
            ret += ">"
        elif self.__op in ["+", "-", "*", "/"]:
            ret += self.__source[0] + " " + self.__op + " " + self.__source[1] + ";"
        elif self.__op == "assign":
            ret += self.__source[0] + ";"
        return ret
        
    def debug(self):
        
        if self.__op == 'phi':
            print ('    Phi function')
            print ('      Source: ', end='')
            for s, p in zip(self.__source, self.__source_prop):
                print (s + " (" + p + "), ", end="")
            print ()
            print ('      Target: ' + self.__left)
        elif self.__op == 'assign':
            print ('    Assignment')
            print ('      Source: ' + self.__source[0] + " (" + self.__source_prop[0] + ")")
            print ('      Target: ' + self.__left)
        else:
            print ('    Arithmetic expression')
            print ('      Operation: ' + self.__op)
            print ('      Source: ' + self.__source[0] + " (" + self.__source_prop[0] + "), " \
                   + self.__source[1] + " (" + self.__source_prop[1] + ")")
            print ('      Target: ' + self.__left)
        
    def get_right(self):
        return {'op': self.__op, 'source': self.__source, 'prop': self.__source_prop}
    def get_left(self): return self.__left

class Return(object):
    
    def __init__(self, line=""):
        
        assert "return" in line, "\"" + line + "\" is not a return"
        line = line.strip().strip(";").strip().split()
        assert "return" == line[0].strip(), "\"" + line + "\" is not a return"
        if len(line) == 2:
            assert PATTERN_VAR.search(line[1].strip()) is not None, "Invalid token \"" + line[1] + "\""
            self.__source = line[1].strip()
        else:
            self.__source = None
        
    def __str__(self):
        
        if self.__source is None:
            return "return;"
        else:
            return "return " + self.__source + ";"
        
    def debug(self):
        
        if self.__source is None:
            print ("    Return nothing")
        else:
            print ("    Return: " + self.__source)
            
    def get_source(self): return self.__source

class SimpleFunc(object):
    
    def __init__(self, line=""):
        
        line = line.strip().strip(";").strip()
        assert PATTERN_FUNC.search(line) is not None, "Invalid func call \"" + line + "\""
        self.__source = line
        
    def __str__(self):
        
        return self.__source + ";"
        
    def debug(self):
        
        print ("    Call function: " + self.__source)
        
    def get_source(self): return self.__source

class Goto(object):
    
    def __init__(self, lines=[]):
        
        self.__is_conditional = False
        for line in lines:
            if re.match(r"if( |\t)*\(.+\)", line.strip()) is not None:
                self.__is_conditional = True
                break
        if self.__is_conditional:
            self.__conditional(lines)
        else:
            self.__unconditional(lines)
        
    def __conditional(self, lines=[]):
        
        self.__label = []
        for line_no in range(len(lines)):
            tmp_line = lines[line_no].strip()
            if "if " in tmp_line:
                self.__condition = re.findall(r"\(.*\)", tmp_line)[0].strip('()')
                self.__condition = Compare(self.__condition)
            if "goto " in tmp_line:
                self.__label.append(re.findall(r"<[a-zA-Z0-9 _]*>", tmp_line))
                
    def __unconditional(self, lines=[]):
        
        for line in lines:
            tmp_line = line.strip()
            if "goto " in tmp_line:
                self.__label = [re.findall(r"<[a-zA-Z0-9 _]*>", tmp_line)]
                return
           
    def __str__(self):
        
        ret = ""
        if self.__is_conditional:
            ret += "if (" + str(self.__condition) + ")\n"
            ret += "goto " + self.__label[0][0]
            for i in self.__label[0][1:]:
                ret += " (" + i + ")"
            ret += ";\nelse\n"
            ret += "goto " + self.__label[1][0]
            for i in self.__label[1][1:]:
                ret += " (" + i + ")"
            ret += "\n"
        else:
            ret += "goto " + self.__label[0][0]
            for i in self.__label[0][1:]:
                ret += " (" + i + ")"
            ret += ";\n"
        return ret
                
    def debug(self):
        
        if self.__is_conditional:
            print ("    Conditional goto")
            self.__condition.debug()
            print ("      True label: ", end='')
            for i in self.__label[0]:
                print (i + ", ", end="")
            print ()
            print ("      False label: ", end='')
            for i in self.__label[1]:
                print (i + ", ", end="")
            print ()
        else:
            print ("    Unconditional goto")
            print ("      Goto label: ", end="")
            for i in self.__label[0]:
                print (i + ", ", end="")
            print ()
        
    def get_goto(self):
        
        if self.__is_conditional:
            return {"condition": self.__condition,
                    "true": self.__label[0],
                    "false": self.__label[1]}
        else:
            return {"condition": "__ALWAYS__",
                    "true": self.__label[0],
                    "false": "__IMPOSSIBLE__"}
                
    def is_conditional(self):   return self.__is_conditional
                
class Block(object):
    
    def __init__(self, lines=[]):
        
        self.__name = None
        self.__goto = None
        self.__content = None
        for line_no in range(len(lines)):
            tmp_line = lines[line_no].strip()
            if re.match(r"<[a-zA-Z0-9 _]*>", tmp_line):
                self.__name = re.findall(r"<[a-zA-Z0-9 _]*>", tmp_line)[0]
                begin_line = line_no
            elif "if " in tmp_line or "goto " in tmp_line:
                self.__goto = Goto(lines[line_no:])
                self.__content = []
                for line in lines[begin_line+1:line_no]:
                    if len(line.strip().strip("{}:").strip()) <= 0:
                        continue
                    if "return" in line:
                        self.__content.append(Return(line))
                    elif PATTERN_FUNC.match(line.strip()) is not None:
                        self.__content.append(SimpleFunc(line))
                    else:
                        self.__content.append(Assign(line))
                break
        if self.__goto is None:
            self.__content = []
            for line in lines[begin_line+1:]:
                if len(line.strip().strip("{}:").strip()) <= 0:
                    continue
                if "return" in line:
                    self.__content.append(Return(line))
                elif PATTERN_FUNC.match(line.strip()) is not None:
                    self.__content.append(SimpleFunc(line))
                else:
                    self.__content.append(Assign(line))
            
    def __str__(self):
        
        ret = self.__name + "\n"
        for stmt in self.__content:
            ret += str(stmt) + "\n"
        if self.__goto is not None:
            ret += str(self.__goto)
        return ret
            
    def set_goto(self, label=""):
        
        assert self.__goto is None, "Goto already set."
        self.__goto = Goto(["goto "+label+";"])
            
    def debug(self):
        
        print ("  Block name: " + self.__name)
        for stmt in self.__content:
            stmt.debug()
        if self.__goto is not None:
            self.__goto.debug()
        
    def get_name(self):     return self.__name
    def get_content(self):  return self.__content
    def get_goto(self):     return self.__goto
                
class CFG(object):
    
    def __init__(self, lines=[], name=""):
        
        self.__name = name
        block_line_no = []
        block_name = []
        for line_no in range(len(lines)):
            line = lines[line_no].strip().strip(":{}").strip()
            if len(line) <= 0:
                continue
            if line[0] == '<' and line[-1] == ">":
                block_line_no.append(line_no)
                block_name.append(line)
        self.__entry = None
        self.__block = []
        for i in range(len(block_line_no)):
            if i == len(block_line_no)-1:
                self.__block.append(Block(lines[block_line_no[i]:]))
            else:
                self.__block.append(Block(lines[block_line_no[i]: block_line_no[i+1]]))
                if i == 0:
                    self.__entry = self.__block[-1]
                if self.__block[-1].get_goto() is None:
                    self.__block[-1].set_goto(block_name[i+1])
        
    def __str__(self):
        
        ret = ""
        for b in self.__block:
            ret += str(b)
        return ret
        
    def debug(self):
        
        print ("CFG name: " + self.__name)
        for b in self.__block:
            b.debug()
        
    def get_name(self):     return self.__name
    def get_block(self):    return self.__block
    def get_entry(self):    return self.__entry
            
if __name__ == "__main__":
    
    path = "../benchmark/t1.ssa"
    sym_tab = symtab.build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    cfg = {}
    for key in sym_tab.keys():
        cfg[key] = CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                       key)
        
    #for key in cfg.keys():
    #    cfg[key].debug()