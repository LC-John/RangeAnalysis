# -*- coding: utf-8 -*-
"""
Created on Sun May 20 21:01:53 2018

@author: DrLC
"""

class VarDecl(object):
    
    def __init__(self, line=""):
        
        line = line.strip().strip(';,').strip().split()
        self.__type = line[0]
        assert self.__type in ["int", "float"], "Invalid type \""+self.__type+"\""
        self.__name = line[-1]

    def __str__(self):
        
        return str(self.__type) + " " + str(self.__name)
        
    def __eq__(self, obj):
        
        if type(obj) is not type(self):
            return False
        return (obj.get_name() == self.__name
                and obj.get_type() == self.__type)

    def get_name(self): return self.__name
    def get_type(self): return self.__type
            
class FuncDecl(object):
    
    def __init__(self, line=""):
        
        line = line.strip()
        self.__name = line[:line.find("(")].strip()
        arg_line = line[line.find("(")+1: line.find(")")].strip()
        if len(arg_line) > 0:
            arg_line = arg_line.split(",")
            self.__args = []
            for a in arg_line:
                self.__args.append(VarDecl(a.strip().strip(',').strip()))
        else: self.__args = []
            
    def __str__(self):
        
        ret = self.__name + " ("
        for i in range(len(self.__args)):
            if i == 0:
                ret += str(self.__args[i])
            else: ret += ", " + str(self.__args[i])
        return ret + ")"
            
    def __eq__(self, obj):
        
        if type(obj) is not type(self):
            return False
        if not obj.get_name() == self.__name:
            return False
        obj_args = obj.get_args()
        if not len(obj_args) == len(self.__args):
            return False
        for i in range(len(obj_args)):
            if not obj_args[i].get_type() == self.__args[i].get_type():
                return False
        return True
        
    def get_name(self): return self.__name
    def get_args(self): return self.__args


def build_symtab(ssa=""):
    
    with open(ssa, 'r') as f:
        lines = f.readlines()
        
    new_func = False
    in_func = False
    var_decl = False
    
    SYM_TABLE = {}
    
    for line, line_no in zip(lines, range(len(lines))):
        # print (line, end="")
        if line[:2] == ';;':
            new_func = True
        elif new_func and len(line.strip()) > 0:
            new_func = False
            var_decl = True
            in_func = True
            tmp_f = FuncDecl(line)
            tmp_f_begin = line_no
            tmp_vars = []
        elif var_decl:
            if len(line.strip()) == 0:
                pass
            elif line.find("<") >= 0 and line.find(">") >= 0:
                var_decl = False
                tmp_f_bb_line = line_no
                SYM_TABLE[tmp_f.get_name()] = {"decl": tmp_f, "vars": tmp_vars}
            elif line.strip() == '{': pass
            else: tmp_vars.append(VarDecl(line))
        elif in_func:
            if line.strip() == '}':
                in_func = False
                SYM_TABLE[tmp_f.get_name()]['lines'] = [tmp_f_begin, tmp_f_bb_line, line_no]
                
    for key in SYM_TABLE.keys():
        item = SYM_TABLE[key]
        var_list = item['decl'].get_args() + item['vars']
        for i in range(len(var_list)-1):
            for j in range(i+1, len(var_list)):
                assert not var_list[i].get_name() == var_list[j].get_name(), \
                    "Redefine of \""+str(var_list[i])+"\" and \""+str(var_list[j])+"\""

    return SYM_TABLE
    


if __name__ == "__main__":
    
    sym_tab = build_symtab("../benchmark/t7.ssa")
    for key in sym_tab.keys():
        item = sym_tab[key]
        print ("Function:")
        print ("  "+str(item["decl"]))
        print ("  Begin: line "+str(item['lines'][0]))
        print ("  Blocks: line "+str(item['lines'][1]))
        print ("  End: line "+str(item['lines'][2]))
        if len(item["vars"]) == 0:
            print ("  Vars:\tNone")
        else:
            print ("  Vars:")
        for v in item["vars"]:
            print (end="    ")
            print (str(v))
        print ()