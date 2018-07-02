# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 15:36:05 2018

@author: DrLC
"""

import re
from interval import interval
import random

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
        
        print ("    Next: ", end='')
        for n in self.__next:
            print (str(n.get_number()), end=" ")
        print ("\tPrev: ", end='')
        for n in self.__prev:
            print (str(n.get_number()), end=" ")
        print ()
        
    def __eq__(self, obj):
        
        if type(obj) is not ConstraintNode:
            return False
        return self.__number == obj.get_number()
        
    def add_prev(self, _prev): self.__prev.append(_prev)
    def add_next(self, _next): self.__next.append(_next)
    def del_prev(self, _prev):
        if _prev in self.__prev:
            self.__prev.remove(_prev)
    def del_next(self, _next):
        if _next in self.__next:
            self.__next.remove(_next)
    def clr_prev(self): self.__prev.clear()
    def clr_next(self): self.__next.clear()
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
        
        print ("  VarNode "+str(self.get_number()))
        print ("    Name: "+self.__name, end="")
        print ("\tType: "+self.__type)
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
            self.__interval = interval((l, r))
            self.__unknown = False
        super().__init__()
        
    def set_interval(self, _inter_l, _inter_r):
        
        self.__interval = interval((_inter_l, _inter_r))
        self.__unknown = False
        
    def debug(self):
        
        print ("  RangeNode "+str(self.get_number()))
        if self.__unknown:
            print ("    Range: unknown.")
        else:
            print ("    Range: ["+str(self.__interval[0][0])+", " \
                              +str(self.__interval[0][1])+"]")
        super().debug()
        
    def __str__(self):
        
        if self.__unknown: return "Unknown"
        else: return "["+str(self.__interval[0][0])+", "+str(self.__interval[0][1])+"]"
        
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
        
        print ("  FtRangeNode "+str(self.get_number()))
        if self.__lft is None: print ("    Range-L: "+str(self.__lval))
        elif self.__lop == "pass": print ("    Range-L: "+self.__lft)
        else: print ("    Range-L: "+self.__lft+" "+self.__lop+" "+str(self.__lval))
        if self.__rft is None: print ("    Range-R: "+str(self.__rval))
        elif self.__rop == "pass": print ("    Range-R: "+self.__rft)
        else: print ("    Range-R: "+self.__rft+" "+self.__rop+" "+str(self.__rval))
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
        
        print ("  PhiNode "+str(self.get_number()))
        super().debug()
        
    def __str__(self):
        
        return 'phi'
    
class C_PhiNode(ConstraintNode):
    
    def __init__(self):
        
        super().__init__()
        
    def debug(self):
        
        print ("  C_PhiNode "+str(self.get_number()))
        super().debug()
        
    def __str__(self):
        
        return 'c_phi'
        
class ArithmeticNode(ConstraintNode):
    
    def __init__(self, op=""):
        
        assert op in ['+', '-', '*', '/'], "Invalid arithmetic op \"" + op + "\""
        self.__op = op
        super().__init__()
    
    def debug(self):
        
        print ("  ArithmeticNode "+str(self.get_number()))
        print ("    Operation: "+self.__op)
        super().debug()
        
    def __str__(self):
        
        return self.__op
        
    def get_op(self):   return self.__op

class CallNode(ConstraintNode):
    
    def __init__(self, funcName=""):
        
        if '(' in funcName:
            self.__name = funcName[:funcName.find('(')].strip()
        else:
            self.__name = funcName.strip()
        super().__init__()
        
    def debug(self):
        
        print ("  CallNode "+str(self.get_number()))
        print ("    Function: "+self.__name)
        super().debug()
        
    def __str__(self):
        
        return self.__name+"()"
        
    def get_name(self):   return self.__name

class CG(object):
    
    def __init__(self, _cfg, _symtab, name):
        
        self.__name = name
        self.__symtab = _symtab
        self.__create_varnodes(_cfg)
        self.__link_varnodes(_cfg)
        self.__goto_varnodes(_cfg)
        self.__simplify_c_phi(_cfg)
        self.__simplify()
            
    def __create_varnodes(self, _cfg):
        
        self.__constraint = []
        self.__entry = []
        self.__origin2rename = {}
        var_list = self.__symtab['decl'].get_args() + self.__symtab['vars']
        for b in _cfg.get_block():
            self.__origin2rename[b.get_name()] = {}
            for stmt in b.get_content():
                if type(stmt) is cfg.Assign:
                    tmp_name__ = stmt.get_left()
                    tmp_name_ = tmp_name__.split("_")
                    tmp_name = [tmp_name_[0], "_"+tmp_name_[0]]
                    for ttt in tmp_name_:
                        tmp_name.append(tmp_name[-2]+"_"+ttt)
                        tmp_name.append(tmp_name[-2]+"_"+ttt)
                    for var in var_list:
                        if var.get_name() in tmp_name:
                            tmp_type = var.get_type()
                            break
                    self.__constraint.append(VarNode(tmp_name__, tmp_type))
            brs = b.get_branch()
            for br in brs:
                tmp_name__ = br.get_true_name()
                tmp_name_ = tmp_name__.split("_")
                tmp_name = [tmp_name_[0]]
                for var in var_list:
                    for ttt in tmp_name_:
                        tmp_name.append(tmp_name[-1]+"_"+ttt)
                    if var.get_name() in tmp_name:
                        tmp_type = var.get_type()
                        break
                self.__constraint.append(VarNode(tmp_name__, tmp_type))
                if not br.is_ft():
                    tmp_name__ = br.get_false_name()
                    tmp_name_ = tmp_name__.split("_")
                    tmp_name = [tmp_name_[0]]
                    for var in var_list:
                        for ttt in tmp_name_:
                            tmp_name.append(tmp_name[-1]+"_"+ttt)
                        if var.get_name() in tmp_name:
                            tmp_type = var.get_type()
                            break
                    self.__constraint.append(VarNode(tmp_name__, tmp_type))
                    
    def __link_varnodes(self, _cfg):
        
        for b in _cfg.get_block():
            for stmt in b.get_content():
                if type(stmt) is cfg.SimpleFunc:
                    pass
                elif type(stmt) is cfg.Return:
                    if stmt.get_source() is None:
                        self.__return = None
                    else:
                        self.__return = self.__find_varnode(stmt.get_source())
                elif type(stmt) is cfg.Constrain_Phi:
                    tmp_node = C_PhiNode()
                    self.__constraint.append(tmp_node)
                    tmp_var = self.__find_varnode(stmt.get_left())
                    assert tmp_var is not None
                    tmp_var.add_prev(tmp_node)
                    tmp_node.add_next(tmp_var)
                    for tmp_var_ in stmt.get_right():
                        tmp_var = self.__find_varnode(tmp_var_)
                        assert tmp_var is not None
                        tmp_var.add_next(tmp_node)
                        tmp_node.add_prev(tmp_var)
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
                    elif stmt.get_right()['op'] in ['assign', 'func']:
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
                            tmp_call = CallNode(s.strip())
                            self.__constraint.append(tmp_call)
                            tmp_call.add_next(tmp_node)
                            tmp_node.add_prev(tmp_call)
                            tmp_node = tmp_call
                        else: assert False
    
    def __goto_varnodes(self, _cfg):
    
        LT, GT, EQ, LE, GE, NEQ = [1, 4, 2, 3, 6, 5]
        for b in _cfg.get_block():
            brs = b.get_branch()
            goto = b.get_goto()
            if goto is None or not goto.is_conditional():
                continue
            tmp_con = goto.get_goto()['condition']
            tmp_op = tmp_con.get_op()
            tmp_l = tmp_con.get_left()
            tmp_l_prop = tmp_con.get_left_prop()
            tmp_r = tmp_con.get_right()
            tmp_r_prop = tmp_con.get_right_prop()
            assert tmp_l_prop == 'var'
            if tmp_op == "<":
                tmp_l_lg, tmp_r_lg = [LT, GT]
            elif tmp_op == '<=':
                tmp_l_lg, tmp_r_lg = [LE, GE]
            elif tmp_op == '>':
                tmp_l_lg, tmp_r_lg = [GT, LT]
            elif tmp_op == '>=':
                tmp_l_lg, tmp_r_lg = [GE, LE]
            elif tmp_op == '==':
                tmp_l_lg, tmp_r_lg = [EQ, EQ]
            elif tmp_op == '!=':
                tmp_l_lg, tmp_r_lg = [NEQ, NEQ]
            if tmp_r_prop == 'int':
                tmp_r = int(tmp_r)
            elif tmp_r_prop == 'fp':
                tmp_r = float(tmp_r)
            for br in brs:
                if br.get_name() == PATTERN_VAR.match(tmp_l).group():
                    br_lg = tmp_l_lg
                    br_other_prop = tmp_r_prop
                    if br_other_prop == 'var':
                        br_other = PATTERN_VAR.match(tmp_r.strip()).group()
                    else:
                        br_other = tmp_r
                else:
                    br_lg = tmp_r_lg
                    br_other_prop = tmp_l_prop
                    if br_other_prop == 'var':
                        br_other = PATTERN_VAR.match(tmp_l.strip()).group()
                    else:
                        br_other = tmp_l
                if br.is_ft():
                    assert br_other_prop == 'var'
                    tmp_var = self.__find_varnode(br_other)
                    br_other_type = tmp_var.get_type()
                    if br_lg == LT:
                        if br_other_type == 'int':
                            tmp_node = FtRangeNode(None, '', float('-inf'), br_other, '-', 1)
                        elif br_other_type == 'float':
                            tmp_node = FtRangeNode(None, '', float('-inf'), br_other, 'pass', 0)
                    elif br_lg == LE:
                        tmp_node = FtRangeNode(None, '', float('-inf'), br_other, 'pass', 0)
                    elif br_lg == GT:
                        if br_other_type == 'int':
                            tmp_node = FtRangeNode(br_other, '+', 1, None, '', float('+inf'))
                        elif br_other_type == 'float':
                            tmp_node = FtRangeNode(br_other, 'pass', 0, None, '', float('+inf'))
                    elif br_lg == GE:
                        tmp_node = FtRangeNode(br_other, 'pass', 0, None, '', float('+inf'))
                    elif br_lg == EQ:
                        tmp_node = FtRangeNode(br_other, 'pass', 0, br_other, 'pass', 0)
                    self.__constraint.append(tmp_node)
                    tmp_node.add_prev(tmp_var)
                    tmp_var.add_next(tmp_node)
                    tmp_var = self.__find_varnode(br.get_name())
                    tmp_node.add_prev(tmp_var)
                    tmp_var.add_next(tmp_node)
                    tmp_var = self.__find_varnode(br.get_true_name())
                    tmp_node.add_next(tmp_var)
                    tmp_var.add_prev(tmp_node)
                else:
                    assert br_other_prop in ['int', 'fp']
                    br_other_type = br_other_prop
                    if br_lg == LT:
                        if br_other_type == 'int':
                            tmp_true_node = RangeNode(float('-inf'), br_other-1)
                            tmp_false_node = RangeNode(br_other, float('inf'))
                        elif br_other_type == 'fp':
                            tmp_true_node = RangeNode(float('-inf'), br_other)
                            tmp_false_node = RangeNode(br_other, float('inf'))
                    elif br_lg == LE:
                        if br_other_type == 'int':
                            tmp_true_node = RangeNode(float('-inf'), br_other)
                            tmp_false_node = RangeNode(br_other+1, float('inf'))
                        elif br_other_type == 'fp':
                            tmp_true_node = RangeNode(float('-inf'), br_other)
                            tmp_false_node = RangeNode(br_other, float('inf'))
                    elif br_lg == GT:
                        if br_other_type == 'int':
                            tmp_false_node = RangeNode(float('-inf'), br_other)
                            tmp_true_node = RangeNode(br_other+1, float('inf'))
                        elif br_other_type == 'fp':
                            tmp_false_node = RangeNode(float('-inf'), br_other)
                            tmp_true_node = RangeNode(br_other, float('inf'))
                    elif br_lg == GE:
                        if br_other_type == 'int':
                            tmp_false_node = RangeNode(float('-inf'), br_other-1)
                            tmp_true_node = RangeNode(br_other, float('inf'))
                        elif br_other_type == 'fp':
                            tmp_false_node = RangeNode(float('-inf'), br_other)
                            tmp_true_node = RangeNode(br_other, float('inf'))
                    elif br_lg == EQ:
                        tmp_true_node = RangeNode(br_other, br_other)
                        tmp_false_node = RangeNode()
                    elif br_lg == NEQ:
                        tmp_false_node = RangeNode(br_other, br_other)
                        tmp_true_node = RangeNode()
                    self.__constraint.append(tmp_true_node)
                    self.__constraint.append(tmp_false_node)
                    tmp_var = self.__find_varnode(br.get_name())
                    tmp_true_node.add_prev(tmp_var)
                    tmp_false_node.add_prev(tmp_var)
                    tmp_var.add_next(tmp_true_node)
                    tmp_var.add_next(tmp_false_node)
                    tmp_var = self.__find_varnode(br.get_true_name())
                    tmp_var.add_prev(tmp_true_node)
                    tmp_true_node.add_next(tmp_var)
                    tmp_var = self.__find_varnode(br.get_false_name())
                    tmp_var.add_prev(tmp_false_node)
                    tmp_false_node.add_next(tmp_var)
                    
    def __find_varnode(self, name=""):
        
        if "(int)" in name:
            name = name[name.find("(int)")+5:]
        if "(float)" in name:
            name = name[name.find("(float)")+7:]
        var_name = PATTERN_VAR.search(name.strip()).group()
        #print (var_name)
        for c in self.__constraint:
            if type(c) is VarNode:
                if var_name == c.get_name():
                    return c
        if '(D' in name:
            name = name[:name.find('(D')]
        name_ = name.split("_")
        name__ = [name_[0], "_"+name_[0]]
        for n in name_:
            name__.append(name__[-2]+"_"+n)
            name__.append(name__[-2]+"_"+n)
        for a in self.__symtab['decl'].get_args():
            if a.get_name() in name__:
                self.__constraint.append(VarNode(var_name, a.get_type()))
                self.__entry.append(self.__constraint[-1])
                return self.__constraint[-1]
        return None
                
    def __simplify_c_phi(self, _cfg):
        
        c_phi = {}
        for con, con_idx in zip(self.__constraint, range(len(self.__constraint))):
            for nxt in con.get_prev():
                if type(nxt) is not C_PhiNode:
                    continue
                nxt_idx = self.__constraint.index(nxt)
                if con_idx not in c_phi.keys():
                    c_phi[con_idx] = {nxt_idx: []}
                else:
                    c_phi[con_idx][nxt_idx] = []
                for b in _cfg.get_block():
                    for c in b.get_content():
                        if type(c) is not cfg.Constrain_Phi:
                            continue
                        if (PATTERN_VAR.match(c.get_left()).group() == con.get_name() \
                            and (PATTERN_VAR.match(c.get_right()[1]).group() == nxt.get_prev()[0].get_name() \
                            or PATTERN_VAR.match(c.get_right()[1]).group() == nxt.get_prev()[1].get_name())):
                                c_phi[con_idx][nxt_idx].append(b)
        for old_num in c_phi.keys():
            old = self.__constraint[old_num]
            for cphi_num in c_phi[old_num].keys():
                cphi = self.__constraint[cphi_num]
                for block in c_phi[old_num][cphi_num]:
                    flag = [False for b in _cfg.get_block()]
                    self.__split_c_phi_by_chain(_cfg, block, cphi, old, None, True, flag)
        tb_del = []
        for cphi in self.__constraint:
            if type(cphi) is C_PhiNode:
                tb_del.append(cphi)
                assert len(cphi.get_prev()) == 1
                nxt = cphi.get_next()[0]
                for prv in cphi.get_prev():
                    nxt.del_prev(cphi)
                    prv.del_next(cphi)
                    nxt.add_prev(prv)
                    prv.add_next(nxt)
        for c in tb_del:
            self.__constraint.remove(c)            
                    
    def __split_c_phi_by_chain(self, _cfg, block, cphi, old, new=None, begin=False, flag=[]):
        
        if begin:
            new = VarNode(old.get_name()+"_"+str(random.randint(0,100000)), old.get_type())
            self.__constraint.append(new)
            old.del_prev(cphi)
            old.del_next(cphi)
            cphi.del_prev(old)
            cphi.del_next(old)
            cphi.add_next(new)
            new.add_prev(cphi)
        if flag[_cfg.get_block().index(block)]:
            return
        flag[_cfg.get_block().index(block)] = True
        content_cphi_source = []
        for c in block.get_content():
            if type(c) is cfg.Constrain_Phi and PATTERN_VAR.match(c.get_left()).group() == old.get_name():
                content_cphi_source.append(c.get_right()[1])
        check_cphi = cphi.get_prev()[0].get_name()
        if check_cphi == old.get_name():
            check_cphi = cphi.get_prev()[1].get_name()
        check_cphi_cnt = 0
        for i in content_cphi_source:
            if i.startswith(check_cphi):
                check_cphi_cnt += 1
        if check_cphi_cnt >= 2:
            print ("merge")
            return
        
        for c in block.get_content():
            if type(c) is cfg.SimpleFunc:
                continue
            elif type(c) is cfg.Return:
                if PATTERN_VAR.match(c.get_source()).group() == old.get_name():
                    self.__return = new
                return
            elif type(c) is cfg.Assign:
                tmp_op = c.get_right()['op']
                tmp_source_ = c.get_right()['source']
                tmp_source = []
                for i in tmp_source_:
                    if PATTERN_VAR.search(i):
                        tmp_source.append(PATTERN_VAR.search(i).group())
                    else:
                        tmp_source.append(i)
                tmp_prop = c.get_right()['prop']
                if_match = False
                for s, sp in zip(tmp_source, tmp_prop):
                    if sp == 'var' and s == old.get_name():
                        if_match = True
                if if_match:
                    if tmp_op == 'assign':
                        tmp_var = self.__find_varnode(tmp_source[0])
                        tmp_var.del_prev(old)
                        old.del_next(old)
                        tmp_var.add_prev(new)
                        new.add_next(tmp_var)
                    else:
                        for nxt in old.get_next():
                            if (type(nxt) is VarNode
                               or (PATTERN_VAR.match(c.get_left()).group().startswith(nxt.get_next()[0].get_name())
                               or nxt.get_next()[0].get_name().startswith(PATTERN_VAR.match(c.get_left()).group()))):
                                nxt.del_prev(old)
                                old.del_next(nxt)
                                nxt.add_prev(new)
                                new.add_next(nxt)
                                break
        '''
        for br in block.get_branch():
            if old.get_name() == PATTERN_VAR.match(br.get_name()).group():
                tmp_var = self.__find_varnode(br.get_true_name())
                tmp_var = tmp_var.get_prev()[0]
                tmp_var.del_prev(old)
                old.del_next(tmp_var)
                tmp_var.add_prev(new)
                new.add_next(tmp_var)
                if not br.is_ft():
                    tmp_var = self.__find_varnode(br.get_false_name())
                    tmp_var = tmp_var.get_prev()[0]
                    tmp_var.del_prev(old)
                    old.del_next(tmp_var)
                    tmp_var.add_prev(new)
                    new.add_next(tmp_var)
        '''
        goto = block.get_goto().get_goto()
        for b in _cfg.get_block():
            if b.get_name() == goto['true']:
                self.__split_c_phi_by_chain(_cfg, b, cphi, old, new, False, flag)
            if b.get_name() == goto['false']:
                self.__split_c_phi_by_chain(_cfg, b, cphi, old, new, False, flag)
                
    def __simplify(self):
        
        while self.__backward_simplify_iter():
            pass
        while self.__forward_simplify_iter():
            pass
        
    def __backward_simplify_iter(self):
        
        ret = []
        for c in self.__constraint:
            if c.get_prev() == []:
                continue
            tb_del_ = []
            for prv in c.get_prev():
                if prv not in self.__constraint:
                    tb_del_.append(prv)
            for i in tb_del_:
                c.del_prev(i)
            if c.get_prev() == []:
                ret.append(c)
        for i in ret:
            self.__constraint.remove(i)
            if i in self.__entry:
                self.__entry.remove(i)
        if len(ret) == 0:
            return False
        else:
            return True
          
    def __forward_simplify_iter(self):
        
        ret = []
        if self.__return is None:
            ret = self.__constraint
        else:
            for c in self.__constraint:
                if (type(c) is VarNode and len(c.get_next()) == 0
                    and (not self.__return.get_number() == c.get_number())):
                    ret.append(c)
                    for prv in c.get_prev():
                        prv.del_next(c)
        for i in ret:
            self.__constraint.remove(i)
            if i in self.__entry:
                self.__entry.remove(i)
        if len(ret) == 0:
            return False
        else:
            return True
        
    def debug(self):
        
        print ()
        print ('Constraint graph ' + self.__name)
        if len(self.__entry) == 0:
            print ('No entry')
        else:
            print ('Entry: ', end="")
            for i in self.__entry:
                print (str(i.get_number()), end=" ")
            print ()
        if self.__return is None:
            print ("No return")
        else:
            print ("Return: "+str(self.__return.get_number()))
        if len(self.__constraint) == 0:
            print ("No constraint")
        else:
            print ("Constraint:")
            for c in self.__constraint:
                c.debug()
                    
    def get_name(self):             return self.__name
    def get_constraint_nodes(self): return self.__constraint
    def get_entry_nodes(self):      return self.__entry
    def get_return_node(self):      return self.__return
        
if __name__ == "__main__":
    
    path = "../benchmark/t3.ssa"
    sym_tab = build_symtab(path)
    with open(path, 'r') as f:
        lines = f.readlines()
    _cfg_ = {}
    for key in sym_tab.keys():
        _cfg_[key] = cfg.CFG(lines[sym_tab[key]["lines"][1]:sym_tab[key]["lines"][2]],
                             key)
    cg = {}
    for key in _cfg_.keys():
        cg[key] = CG(_cfg_[key], sym_tab[key], key)

    for key in cg.keys():
        cg[key].debug()