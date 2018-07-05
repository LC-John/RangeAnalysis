# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 15:24:30 2018

@author: DrLC
"""

import re
import symtab

import os, sys

PATTERN_INT = re.compile(r"((\+|-)?[0-9]+)")
PATTERN_FP = re.compile(r"((\+|-)?\d+(\.\d*)?((e|E)(\+|-)?\d+))|((\+|-)?\d+\.\d+)")
PATTERN_VAR = re.compile(r"(([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9]+)|([A-Za-z][A-Za-z0-9]+\.[A-Za-z0-9]+)|_[A-Za-z0-9]*)")
PATTERN_RAW_VAR = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
PATTERN_FUNC = re.compile(r"([A-Za-z0-9]+( |\t)*\(.*\))")

class Compare(object):
    
    def __init__(self, line=""):
        
        line = line.strip()
        self.__op = None
        if " == " in line:
            self.__op = "=="
        elif " != " in line:
            self.__op = "!="
        elif " >= " in line:
            self.__op = ">="
        elif " <= " in line:
            self.__op = "<="
        elif " < " in line:
            self.__op = "<"
        elif " > " in line:
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
        if (not self.__left_prop == 'var') and self.__right_prop == 'var':
            self.__left, self.__right = [self.__right, self.__left]
            self.__left_prop, self.__right_prop = [self.__right_prop, self.__left_prop]
            if self.__op == '>':    self.__op = '<'
            elif self.__op == '<':    self.__op = '>'
            elif self.__op == '>=':    self.__op = '<='
            elif self.__op == '<=':    self.__op = '>='
        
    def __str__(self):
        
        return self.__left + " " +self.__op + " " + self.__right
        
    def debug(self):
        
        print ("      Condition: " + self.__left + " " +self.__op + " " + self.__right)
        
    def set_left(self, left):   self.__left = left
    def set_right(self, right): self.__right = right
    def get_var_number(self):
        if self.__left_prop == 'var' and self.__right_prop == 'var': return 2
        elif self.__left_prop == 'var' or self.__right_prop == 'var': return 1
        else: return 0
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
            if "*" in tmp_right: self.__op = "*"
            elif "/" in tmp_right: self.__op = "/"
            elif "+" in tmp_right: self.__op = "+"
            elif "-" in tmp_right: self.__op = "-"
            else: self.__op = None
            tmp_right = tmp_right.replace('e+', 'e|')
            tmp_right = tmp_right.replace("e-", 'e~')
            tmp_right = tmp_right.split(self.__op)
            tmp_right = [i.replace('e|', 'e+') for i in tmp_right]
            tmp_right = [i.replace('e~', 'e-') for i in tmp_right]
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
                tmp1 = PATTERN_FUNC.match(tmp).group()
                tmp2 = re.search(r"\(.*\)", tmp).group()
                tmp2 = tmp2.strip().strip("()").strip().split(",")
                self.__source = []
                self.__source.append(tmp1)
                self.__source_prop.append("func")
                for tt in tmp2:
                    self.__source.append(tt.strip())
                    if PATTERN_VAR.search(tmp) is not None:
                        self.__source_prop.append("var")
                    elif PATTERN_FP.search(tmp) is not None:
                        self.__source_prop.append("fp")
                    elif PATTERN_INT.search(tmp) is not None:
                        self.__source_prop.append("int")
                    else:
                        assert False, "Invalid token \"" + tmp + "\""
                self.__op = 'func'
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
        elif self.__source_prop[0] == "func":
            ret += self.__source[0] + "("
            if len(self.__source) >= 2:
                ret += self.__source[1]
                for i in self.__source[2:]:
                    ret += ", " + i
            ret += ")"
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
        elif self.__source_prop[0] == "func":
            print ('    Call function:')
            print ('      Funcation: ' + self.__source[0])
            if len(self.__source) > 1:
                print ('      Param:', end="")
                for i, j in zip(self.__source[1:], self.__source_prop[1:]):
                    print (i + " (" + j + ")", end=', ')
                print ()
            else:
                print ('      No param')
            print ('      Target' + self.__left)
        else:
            print ('    Arithmetic expression')
            print ('      Operation: ' + self.__op)
            print ('      Source: ' + self.__source[0] + " (" + self.__source_prop[0] + "), " \
                   + self.__source[1] + " (" + self.__source_prop[1] + ")")
            print ('      Target: ' + self.__left)
        
    def set_source(self, s, sp, idx):
        self.__source[idx] = s
        self.__source_prop[idx] = sp 
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
            
    def set_source(self, s): self.__source = s           
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
             
class Branch(object):
    
    def __init__(self, name="", bb_name="", ft=True):
        
        self.__name = PATTERN_RAW_VAR.match(name.strip()).group()
        self.__pattern = re.compile(self.__name)
        self.__name_t = self.__name + bb_name + "_t"
        self.__ft = False
        self.__name_f = self.__name + bb_name + "_f"
        if ft:
            self.__ft = True
            self.__name_f = None
        
    def __str__(self):
        
        ret = ""
        ret += "# " + self.__name_t + " = Goto true("+ self.__name +")\n"
        if not self.__ft:
            ret += "# " + self.__name_f + " = Goto false("+ self.__name +")\n"
        return ret
        
    def debug(self):
        
        print ("    Branch variables")
        print ("      Ft range: "+str(self.__ft))
        print ("      True var: "+str(self.__name_t))
        if not self.__ft:
            print ("      False var: "+self.__name_f)
        
    def set_name(self, name=""):
        self.__name = PATTERN_RAW_VAR.match(name.strip()).group()
        self.__pattern = re.compile(self.__name)
        self.__name_t = self.__name + "_t"
        if not self.__ft:
            self.__name_f = self.__name + "_f"
        
    def get_name(self):         return self.__name
    def is_ft(self):            return self.__ft
    def get_true_name(self):    return self.__name_t
    def get_false_name(self):   return self.__name_f
    def get_name_pattern(self): return self.__pattern
   
class Constrain_Phi(object):
    
    def __init__(self, var, con_var):
        
        self.__left = PATTERN_RAW_VAR.match(var.strip()).group()
        self.__right = PATTERN_RAW_VAR.match(con_var.strip()).group()
        
    def __str__(self):
        ret = ""
        ret += "# " + self.__left + " = C_PHI <" + self.__left + ", " + self.__right + ">"
        return ret
        
    def debug(self):
        
        print ("    Constrain-Phi function")
        print ("      Source: " + self.__left + ", " + self.__right)
        print ("      Target: " + self.__left)
        
    def get_left(self):     return self.__left
    def get_right(self):    return [self.__left, self.__right]

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
        self.__branch = []
        if self.__goto is not None and self.__goto.is_conditional():
            tmp_ft = (self.__goto.get_goto()['condition'].get_var_number() == 2)
            tmp_bb_name_ = self.__name.strip().strip('<>').strip().split()
            tmp_bb_name = ""
            for i in tmp_bb_name_:
                tmp_bb_name += "_" + i
            if self.__goto.get_goto()['condition'].get_left_prop() == 'var':
                self.__branch.append(Branch(self.__goto.get_goto()['condition'].get_left(), tmp_bb_name, tmp_ft))
            if self.__goto.get_goto()['condition'].get_right_prop() == 'var':
                self.__branch.append(Branch(self.__goto.get_goto()['condition'].get_right(), tmp_bb_name, tmp_ft))
        self.__def = []
        for a in self.__content:
            if type(a) is Assign:
                tmp_raw_var = PATTERN_RAW_VAR.match(a.get_left()).group()
                if tmp_raw_var not in self.__def:
                    self.__def.append(tmp_raw_var)
        self.__var = []
        for a in self.__content:
            if type(a) is Return:
                tmp_var = a.get_source()
                if tmp_var is not None:
                    tmp_raw_var = PATTERN_RAW_VAR.match(tmp_var).group()
                    if tmp_raw_var not in self.__var:
                        self.__var.append(tmp_raw_var)
            if type(a) is Assign:
                for (s, sp) in zip(a.get_right()['source'], a.get_right()['prop']):
                    if sp == 'var':
                        if "(int)" in s:
                            tmp_raw_var = PATTERN_RAW_VAR.match(s[s.find("(int)")+5:].strip()).group()
                            tmp_raw_var = "(int)"+tmp_raw_var
                        elif "(float)" in s:
                            tmp_raw_var = PATTERN_RAW_VAR.match(s[s.find("(float)")+7:].strip()).group()
                            tmp_raw_var = "(float)"+tmp_raw_var
                        else:
                            tmp_raw_var = PATTERN_RAW_VAR.match(s).group()
                        if tmp_raw_var not in self.__var:
                            self.__var.append(tmp_raw_var)
                    elif sp == "func":
                        tmp_var_list = re.search(r"\(.*\)", s).group()
                        tmp_var_list = tmp_var_list.strip()[1:-1]
                        if ',' not in tmp_var_list:
                            tmp_raw_var = PATTERN_RAW_VAR.match(tmp_var_list.strip())
                            if tmp_raw_var is not None and tmp_raw_var not in self.__var:
                                self.__var.append(tmp_raw_var.group())
                            continue
                        tmp_var_list = tmp_var_list.split(',')
                        for tmp_var in tmp_var_list:
                            tmp_raw_var = PATTERN_RAW_VAR.match(tmp_var.strip())
                            if tmp_raw_var is None:
                                continue
                            tmp_raw_var = tmp_raw_var.group()
                            if tmp_raw_var not in self.__var:
                                self.__var.append(tmp_raw_var)
        for b in self.__branch:
            tmp_raw_var = PATTERN_RAW_VAR.match(b.get_name().strip())
            if tmp_raw_var is None:
                continue
            if tmp_raw_var.group() not in self.__var:
                self.__var.append(tmp_raw_var.group())
                
    def replace_var(self, old="", new="", chain_head=True):
        
        old = PATTERN_RAW_VAR.match(old).group()
        new = PATTERN_RAW_VAR.match(new).group()
        if old not in self.__var:
            return True
        self.__var.append(new)
        find_phi = False
        i = 0
        for c, i in zip(self.__content, range(len(self.__content))):
            if type(c) is Assign and c.get_right()['op'] == 'phi':
                find_phi = True
                if PATTERN_VAR.match(c.get_left()).group() == PATTERN_VAR.match(old).group():
                    return False
                continue
            else:
                break
        if find_phi:
            self.__content.insert(i+1, Constrain_Phi(old, new))
        else:
            self.__content.insert(i, Constrain_Phi(old, new))
        return True
                
    def __str__(self):
        
        ret = self.__name + "\n"
        for stmt in self.__content:
            ret += str(stmt) + "\n"
        for b in self.__branch:
            ret += str(b)
        if self.__goto is not None:
            ret += str(self.__goto)
        return ret
            
    def set_goto(self, label=""):
        
        assert self.__goto is None, "Goto already set."
        self.__goto = Goto(["goto "+label+";"])
            
    def debug(self):
        
        print ("  Block name: " + self.__name)
        print ("    Uses: ", end="")
        for v in self.__var:
            print (v, end=" ")
        print ("\n    Defines: ", end="")
        for v in self.__def:
            print (v, end=" ")
        print ()
        for stmt in self.__content:
            stmt.debug()
        for b in self.__branch:
            b.debug()
        if self.__goto is not None:
            self.__goto.debug()
        
    def get_name(self):     return self.__name
    def get_content(self):  return self.__content
    def get_branch(self):   return self.__branch
    def get_vars_used(self):    return self.__var
    def get_vars_defed(self):   return self.__def
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
        self.__return = None
        self.__block = []
        for i in range(len(block_line_no)):
            if i == len(block_line_no)-1:
                self.__block.append(Block(lines[block_line_no[i]:]))
                self.__return = self.__block[-1]
            else:
                self.__block.append(Block(lines[block_line_no[i]: block_line_no[i+1]]))
                if i == 0:
                    self.__entry = self.__block[-1]
                if self.__block[-1].get_goto() is None:
                    self.__block[-1].set_goto(block_name[i+1])
        for b, my_bidx in zip(self.__block, range(len(self.__block))):
            if b.get_goto() is not None and b.get_goto().is_conditional():
                br_list = b.get_branch()
                for br in br_list:
                    for b_name in b.get_goto().get_goto()['true']:
                        bb, bidx = self.__find_block(b_name)
                        if bb is not None:
                            tmp_flags = [False for i in self.__block]
                            self.__replace_var_block_chain(bb, bidx, br.get_name(),
                                                           br.get_true_name(), tmp_flags)
                            break
                    if not br.is_ft():
                        for b_name in b.get_goto().get_goto()['false']:
                            bb, bidx = self.__find_block(b_name)
                            if bb is not None:
                                tmp_flags = [False for i in self.__block]
                                self.__replace_var_block_chain(bb, bidx, br.get_name(),
                                                               br.get_false_name(), tmp_flags)
                                break
                
    def __replace_var_block_chain(self, bb, bidx, old="", new="", flags=[]):
        
        if flags[bidx]:
            return
        flags[bidx] = True
        if not bb.replace_var(old, new):
            return
        if bb.get_goto() is not None:
            g = bb.get_goto()
            for b_name in bb.get_goto().get_goto()['true']:
                tmp_bb, tmp_bidx = self.__find_block(b_name)
                if tmp_bb is not None:
                    self.__replace_var_block_chain(tmp_bb, tmp_bidx, old, new, flags)
            if g.is_conditional():
                for b_name in bb.get_goto().get_goto()['false']:
                    tmp_bb, tmp_bidx = self.__find_block(b_name)
                    if tmp_bb is not None:
                        self.__replace_var_block_chain(tmp_bb, tmp_bidx, old, new, flags)
                    
    def __find_block(self, name=""):
        
        for b, bidx in zip(self.__block, range(len(self.__block))):
            if b.get_name() == name:
                return b, bidx
        return None, -1
        
    def __str__(self):
        
        ret = ""
        for b in self.__block:
            ret += str(b)
        return ret
        
    def debug(self):
        
        print ("CFG name: " + self.__name)
        print ("  Entry block: " + self.__entry.get_name())
        print ("  Return block: " + self.__return.get_name())
        for b in self.__block:
            b.debug()
        
    def get_vars_used(self):
        
        ret = {}
        for b in self.__block:
            ret[b.get_name()] = b.get_vars_used()
        return ret
    def get_vars_defed(self):
        ret = {}
        for b in self.__block:
            ret[b.get_name()] = b.get_vars_defed()
        return ret
    def get_name(self):     return self.__name
    def get_block(self):    return self.__block
    def get_entry(self):    return self.__entry
    def get_return(self):   return self.__return
           
def print_help():
    
    print ()
    print ("+-------------------+")
    print ("|                   |")
    print ("|     SSA-CFG       |")
    print ("|         by DrLC   |")
    print ("|                   |")
    print ("+-------------------+")
    print ()
    print ("Transfer .ssa file to SSA-CFG.")
    print ()
    print ("Use this command to run.")
    print ("  python3 %s [-P|--path SSA_FILE_PATH]" % sys.argv[0])
    print ()
    exit(0)
 
def get_op():
    
    args = sys.argv
    if '-h' in args or '--help' in args:
        print_help()
    if len(args) == 1:
        path = '../benchmark/t1.ssa'
    elif len(args) == 3 and args[1] in ['-P', '--path']:
        path = args[2]
    else:
        print_help()
    return path
        

if __name__ == "__main__":
    
    path = get_op()
    sym_tab = symtab.build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    cfg = {}
    for key in sym_tab.keys():
        cfg[key] = CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                       key)
    for key in cfg.keys():
        cfg[key].debug()