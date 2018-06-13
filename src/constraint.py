# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 15:36:05 2018

@author: DrLC
"""

import re
from interval import interval

from symtab import build_symtab
import cfg

PATTERN_VAR = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")

class ConstraintNode(object):
    
    __Number = 0
    
    def __init__(self):
        
        self.__prev = []
        self.__next = []
        self.__number = ConstraintNode.__Number
        ConstraintNode.__Number += 1

    def debug(self):
        
        print ("  Next: ", end='')
        for n in self.__next:
            print (str(n.get_number()), end=" ")
        print ()
        print ("  Prev: ", end='')
        for n in self.__prev:
            print (str(n.get_number()), end=" ")
        print ()
        
    def __eq__(self, obj):
        
        if type(obj) is not ConstraintNode:
            return False
        return self.__number == obj.get_number()
        
    def add_prev(self, _prev): self.__prev.append(_prev)
    def add_next(self, _next): self.__next.append(_next)
    def del_prev(self, _prev): self.__prev.remove(_prev)
    def del_next(self, _next): self.__next.remove(_next)
    def get_prev(self):     return self.__prev
    def get_next(self):     return self.__next
    def get_number(self):   return self.__number

class VarNode(ConstraintNode):
    
    def __init__(self, name="", vartype=""):
        
        assert vartype in ["int", "float"], "Invalid type \"" + vartype + "\""
        self.__name = PATTERN_VAR.match(name).group()
        if vartype == 'float':
            vartype = 'fp'
        self.__type = vartype
        super().__init__()

    def debug(self):
        
        print ("VarNode "+str(self.get_number()))
        print ("  Name: "+self.__name)
        print ("  Type: "+self.__type)
        super().debug()
        
    def __str__(self):
        
        return self.__name
        
    def get_name(self): return self.__name
    def get_type(self): return self.__type

class RangeNode(ConstraintNode):
    
    def __init__(self, l=float('-inf'), r=float('inf'), unknown=False):
        
        if unknown:
            self.__interval = interval([float('-inf'), float('inf')])
            self.__unknown = True
        else:
            assert l <= r, 'Invalid interval [' + l + ', ' + r + ']'
            self.__interval = interval(l, r)
            self.__unknown = False
        super().__init__()
        
    def set_interval(self, _inter):
        
        self.__interval = interval(_inter)
        self.__unknown = False
        
    def debug(self):
        
        print ("RangeNode "+str(self.get_number()))
        if self.__unknown:
            print ("  Range: unknown.")
        else:
            print ("  Range: ["+str(self.__interval[0][0])+","\
                                    +str(self.__interval[0][1])+"]")
        super().debug()
        
    def __str__(self):
        
        if self.__unknown: return "Unknown"
        else: return "["+str(self.__interval[0][0])+","+str(self.__interval[0][1])+"]"
        
    def is_unknown(self):   return self.__unknown
    def get_interval(self): return self.__interval
    
class FtRangeNode(ConstraintNode):
    
    def __init__(self, lft=None, lop="", lval=float('-inf'),
                 rft=None, rop="", rval=float('inf')):
        
        assert not(lft is None and rft is None), "Invalid ft-range"
        if lft is None: assert len(lop) == 0, "Invalid ft-range"
        else: assert lop in ["+", "-", "*", "/", "pass"], "Invalid ft-range"
        if rft is None: assert len(rop) == 0, "Invalid ft-range"
        else: assert rop in ["+", "-", "*", "/", "pass"], "Invalid ft-range"
        self.__lft = lft
        self.__rft = rft
        self.__lop = lop
        self.__rop = rop
        self.__lval = lval
        self.__rval = rval
        super().__init__()
        
    def debug(self):
        
        print ("FtRangeNode "+str(self.get_number()))
        if self.__lft is None: print ("  Range-L: "+str(self.__lval))
        elif self.__lop == "pass": print ("  Range-L: "+self.__lft)
        else: print ("  Range-L: "+self.__lft+" "+self.__lop+" "+str(self.__lval))
        if self.__rft is None: print ("  Range-R: "+str(self.__rval))
        elif self.__rop == "pass": print ("  Range-R: "+self.__rft)
        else: print ("  Range-R: "+self.__lft+" "+self.__rop+" "+str(self.__rval))
        super().debug()
        
    def __str__(self):
        
        ret = "["
        if self.__lft is None: ret += str(self.__lval)
        elif self.__lop == "pass": ret += "ft("+self.__lft+")"
        else: ret += "ft("+self.__lft+")"+self.__lop+str(self.__lval)
        ret += ","
        if self.__rft is None: ret += str(self.__rval)
        elif self.__rop == "pass": ret += "ft("+self.__rft+")"
        else: ret += "ft("+self.__rft+")"+self.__rop+str(self.__rval)
        return ret + "]"
        
    def get_l(self): return {'ft': self.__lft, 'op': self.__lop, 'val': self.__lval}
    def get_r(self): return {'ft': self.__rft, 'op': self.__rop, 'val': self.__rval}
        
class PhiNode(ConstraintNode):
    
    def __init__(self):
        
        super().__init__()
        
    def debug(self):
        
        print ("PhiNode "+str(self.get_number()))
        super().debug()
        
    def __str__(self):
        
        return 'phi'
        
class ArithmeticNode(ConstraintNode):
    
    def __init__(self, op=""):
        
        assert op in ['+', '-', '*', '/'], "Invalid arithmetic op \"" + op + "\""
        self.__op = op
        super().__init__()
    
    def debug(self):
        
        print ("ArithmeticNode "+str(self.get_number()))
        print ("  Operation: "+self.__op)
        super().debug()
        
    def __str__(self):
        
        return self.__op
        
    def get_op(self):   return self.__op

class CallNode(ConstraintNode):
    
    def __init__(self, funcName=""):
        
        self.__name = funcName
        super().__init__()
        
    def debug(self):
        
        print ("CallNode "+str(self.get_number()))
        print ("  Function: "+self.__name)
        super().debug()
        
    def __str__(self):
        
        return self.__name+"()"
        
    def get_name(self):   return self.__name

class CG(object):
    
    def __init__(self, _cfg, _symtab):
        
        self.__symtab = _symtab
        self.__create_varnodes(_cfg, _symtab)
        self.__link_varnodes(_cfg)
            
    def __create_varnodes(self, _cfg, _symtab):
        
        self.__constraint = []
        self.__entry = []
        var_list = _symtab['decl'].get_args() + _symtab['vars']
        for b in _cfg.get_block():
            for stmt in b.get_content():
                if type(stmt) is cfg.Assign:
                    tmp_name = stmt.get_left()
                    for var in var_list:
                        if var.get_name() in [tmp_name.split("_")[0], tmp_name]:
                            tmp_type = var.get_type()
                            break
                    self.__constraint.append(VarNode(tmp_name, tmp_type))
                    
    def __link_varnodes(self, _cfg):
        
        for b in _cfg.get_block():
            for stmt in b.get_content():
                if type(stmt) is cfg.SimpleFunc:
                    pass
                elif type(stmt) is cfg.Return:
                    if self.__find_varnode(stmt.get_source()) is not None:
                        self.__return = self.__find_varnode(stmt.get_source())
                    else:
                        self.__return = None
                elif type(stmt) is cfg.Assign:
                    if stmt.get_right()['op'] == 'phi':
                        tmp_node = PhiNode()
                        self.__constraint.append(tmp_node)
                        tmp_var = self.__find_varnode(stmt.get_left())
                        assert tmp_var is not None
                        tmp_var.add_prev(tmp_node)
                        tmp_node.add_next(tmp_var)
                    elif stmt.get_right()['op'] in ['+', '-', '*', '/']:
                        tmp_node = ArithmeticNode(stmt.get_right()['op'])
                        self.__constraint.append(tmp_node)
                        tmp_var = self.__find_varnode(stmt.get_left())
                        assert tmp_var is not None
                        tmp_var.add_prev(tmp_node)
                        tmp_node.add_next(tmp_var)
                    elif stmt.get_right()['op'] == 'assign':
                        tmp_node = self.__find_varnode(stmt.get_left())
                    tmp_stmt_right = stmt.get_right()    
                    for (s, sp) in zip(tmp_stmt_right['source'], tmp_stmt_right['prop']):
                        if sp == 'var':
                            tmp_var = self.__find_varnode(s)
                            assert tmp_var is not None
                            tmp_var.add_next(tmp_node)
                            tmp_node.add_prev(tmp_var)
                        elif sp == 'fp':
                            tmp_range = RangeNode(float(s), float(s))
                            self.__constraint.append(tmp_range)
                            tmp_range.add_next(tmp_node)
                            tmp_node.add_prev(tmp_range)
                        elif sp == 'int':
                            tmp_range = RangeNode(float(int(s)), float(int(s)))
                            self.__constraint.append(tmp_range)
                            tmp_range.add_next(tmp_node)
                            tmp_node.add_prev(tmp_range)
                        elif sp == 'func':
                            tmp_call = CallNode(s[:s.find('(')].strip())
                            self.__constraint.append(tmp_call)
                            tmp_call.add_next(tmp_node)
                            tmp_node.add_prev(tmp_call)
                            args = s[s.find('(')+1:s.find(')')].strip().split(',')
                            for a in args:
                                tmp_var = self.__find_varnode(a.strip())
                                assert tmp_var is not None
                                tmp_var.add_next(tmp_call)
                                tmp_call.add_prev(tmp_var)
                        else: assert False
                else: assert False
    
    def __goto_varnodes(self, _cfg):
    
        for b in _cfg.get_block():
            g = b.get_goto()
            if g is not None and g.is_conditional():
                if (not (g.get_left_prop() == 'var' and g.get_right_prop() == 'var')
                    and (g.get_left_prop() == 'var' or g.get_right_prop() == 'var')):
                    if g.get_left_prop() == 'var':
                        tmp_var = self.__find_varnode(g.get_left())
                        tmp_val = g.get_right()
                    elif g.get_right_prop() == 'var':
                        tmp_var = self.__find_varnode(g.get_right())
                        tmp_val = g.get_left()
                    tmp_op = g.get_op()
                    if tmp_op in ['==', '!=']:
                        if tmp_var.get_type() == 'int':
                            tmp_val = int(tmp_val)
                        tmp_t_interval = [float(tmp_val), float(tmp_val)]
                        tmp_f_interval = [float('-inf'), float('inf')]
                        if (tmp_op == '!='):
                            tmp_t_interval, tmp_f_interval = [tmp_f_interval, tmp_t_interval]
                    if (tmp_op == '<' and g.get_left_prop() == 'var') \
                        or (tmp_op == '>' and g.get_right_prop() == 'var') \
                        or (tmp_op == '>=' and g.get_left_prop() == 'var') \
                        or (tmp_op == '<=' and g.get_right_prop() == 'var'):
                        if tmp_var.get_type() == 'int':
                            tmp_t_interval = [float('-inf'), float(int(tmp_val)-1)]
                            tmp_f_interval = [float(int(tmp_val)), float('inf')]
                        else:
                            tmp_t_interval = [float('-inf'), float(tmp_val)]
                            tmp_f_interval = [float(tmp_val), float('inf')]
                        if (tmp_op == '>=' and g.get_left_prop() == 'var') \
                            or (tmp_op == '<=' and g.get_right_prop() == 'var'):
                            tmp_t_interval, tmp_f_interval = [tmp_f_interval, tmp_t_interval]
                    if (tmp_op == '>' and g.get_left_prop() == 'var') \
                        or (tmp_op == '<' and g.get_right_prop() == 'var') \
                        or (tmp_op == '<=' and g.get_left_prop() == 'var') \
                        or (tmp_op == '>=' and g.get_right_prop() == 'var'):
                        if tmp_var.get_type() == 'int':
                            tmp_t_interval = [float(int(tmp_val)+1), float('inf')]
                            tmp_f_interval = [float('-inf'), float(int(tmp_val))]
                        else:
                            tmp_t_interval = [float(tmp_val), float('inf')]
                            tmp_f_interval = [float('-inf'), float(tmp_val)]
                        if (tmp_op == '<=' and g.get_left_prop() == 'var') \
                            or (tmp_op == '>=' and g.get_right_prop() == 'var'):
                            tmp_t_interval, tmp_f_interval = [tmp_f_interval, tmp_t_interval]
                    tmp_t_range = RangeNode(tmp_t_interval[0], tmp_t_interval[1])
                    tmp_f_range = RangeNode(tmp_f_interval[0], tmp_f_interval[1])
                    tmp_t_range.add_prev(tmp_var)
                    tmp_f_range.add_prev(tmp_var)
                    tmp_var.add_next(tmp_t_range)
                    tmp_var.add_next(tmp_f_range)
                elif g.get_left_prop() == 'var' and g.get_right_prop() == 'var':
                    tmp_l_var = self.__find_varnode(g.get_left())
                    tmp_r_var = self.__find_varnode(g.get_right())
                    if (tmp_op == "=="):
                        pass
                    
    def __find_varnode(self, name=""):
        
        if "(int)" in name:
            name = name[name.find("(int)")+5:]
        if "(float)" in name:
            name = name[name.find("(float)")+7:]
        var_name = PATTERN_VAR.match(name.strip()).group()
        #print (var_name)
        for c in self.__constraint:
            if type(c) is VarNode:
                if var_name == c.get_name():
                    return c
        if "(D" in name:
            for a in self.__symtab['decl'].get_args():
                if a.get_name() in [var_name.split("_")[0].strip(), var_name.strip()]:
                    self.__constraint.append(VarNode(var_name, a.get_type()))
                    self.__entry.append(self.__constraint[-1])
                    return self.__constraint[-1]
        return None
                
    def debug(self):
        
        for c in self.__constraint:
            c.debug()
                    
    def get_constraint_nodes(self): return self.__constraint
    def get_entry_nodes(self):      return self.__entry
    def get_return_node(self):     return self.__return
        

if __name__ == "__main__":
    
    path = "../benchmark/t3.ssa"
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    _cfg_ = {}
    for key in sym_tab.keys():
        _cfg_[key] = cfg.CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                             key)
    cg = CG(_cfg_['foo'], sym_tab['foo'])
    for i in cg.get_constraint_nodes():
        print (str(i.get_number())+" "+str(i), end="\t")
    #cg.debug()