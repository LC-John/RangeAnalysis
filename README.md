# Range Analysis

This is the final project of the compilation course, EECS, PKU. The task is to determine the range of the return value of a specific function, given the range of all the arguments. The programs are in .ssa form, and are generated by the GCC compiler. Sub-function invoking is allowed.

The method of "widen-ft-narrow" proposed by [Aho A V & Ullman J D](https://github.com/LC-John/RangeAnalysis/reference/Aho_A_V_Ullman_J_D.pdf) is applied. There still remains some bugs in this project.

## Requirement

re >= 2.2.1
**pyinterval >= 1.2.1**
crlibm

## Usage

Use the following command to run the range analysis. It requires mannual input to set the range of the arguments.

```
python3 range_analysis [-P|--path SSA_FILE_PATH] [-M|--main MAIN_FUNCTION_NAME]
```

Other Python files are all runnable, and each of them has a certain application. Use '-H' or '--help' option to find out.

## SSA Parsing

The first step is to parse the SSA files. The SSA files, regarded as raw input in this project, are generated by the GCC compiler, and since they are temporary intermediate files, the BNF is almost unavailable. 

We summarize the benchmark SSA files, and give the empirical BNF as follow. The terminal symbols are in the form of regular expression. Strings between quotation marks are just raw strings.

```
S           ->  (func_header func_decl func_body)*
func_header ->  ";; Function" name "(" name "=" num ")"" 
func_decl   ->  name "(" ((type name) ("," type name)*)? ")"
func_body   ->  "{" (type name ";")* block* "}"
block       ->  "<" [A-Za-z 0-9]* ">" phi* (assign | func_call)* (goto | c_goto)?
phi         ->  "#" name "= PHI <" name ("," name)+ ">"
assign      ->  name "=" name ";" | name "=" arith_op ";" | name "=" func_call ";"
goto        ->  "goto <" [A-Za-z 0-9]* ">;"
c_goto      ->  "if (" comp_op ")" goto "else" goto
func_call   ->  name "(" ((name | num) ("," name | "," num)*)? ")"
arith_op    ->  (name | num) ("+" | "-" | "*" | "/") (name | num)
com_op      ->  (name | num) ("<" | ">" | "<=" | ">=" | "==" | "!=") (name | num)
num         ->  int | float
int         ->  (\+|-)?[0-9]*
float       ->  (\+|-)?[0-9]+(\.[0-9]*)?((e|E)(\+|-)?[0-9]+))|((\+|-)?[0-9]+\.[0-9]+
name        ->  [_A-Za-z][_.A-Za-z0-9]*(\([0-9]*\))?
type        ->  "int" | "float"
```

We translate the SSA files to CFG defined and implemented by us. The detail of the CFG defination and implementation and the translation process are in [SSA2CFG source code](https://github.com/LC-John/RangeAnalysis/src/cfg.py).

You may run cfg.py to generate a CFG text file, or run cfg_plot.py to generate a rough CFG figure.

## Constraint Graph

The CFG is transferred to constraint graph (CG), because the method we apply requies it.

A special type of statement, C_PHI (or constraint phi) is introduced. During translation from SSA-CFG to CG, the range constraint on conditional branch is set by C_PHI. Take the following program segment for example. C_PHI's help to set range constraints on branches and loops. They are added by traverse the path on CFG. If there are two C_PHI's with opposite names(e.g. i_1_bb_2_t and i_1_bb_2_f), they all die and the traverse ends immediately.

```
========== Before C_PHI ==========
<bb 1>
if (i_1 < 0)
	goto <bb 2>
else 
	goto <bb 3>
<bb 2>
	// ...
<bb 3>
	// ...
========== After C_PHI  ==========
<bb 1>
if (i_1 < 0)
	// i_1_bb_1_t = [-inf, 0)
	goto <bb 2>
else 
	// i_1_bb_1_f = [0, inf]
	goto <bb 3>
<bb 2>
	i_1 = C_PHI <i_1, i_1_bb_1_t>
	// ...
<bb 3>
	i_1 = C_PHI <i_1, i_1_bb_1_f>
	// ...
```

There are 5 major steps during the translation.
1. Generate constraint nodes for all the variables appeared in the CFG.
2. Use the statements in the blocks to partially link the constraint nodes. Add arithmetic nodes and PHI nodes if they are required.
3. Use the branches (conditional and unconditional) between blocks to link the nodes. Add C_PHI nodes if they are required.
4. Reverse C_PHI node (e.g. i_1 = C_PHI <i_1, i_1_bb_2_t> to i_1_bb_2_t = C_PHI <i_1, i_1_bb_2_t>), and split the paths. After this step, there should be no remaining C_PHI nodes.
5. Compress the graph. All useless nodes and paths (e.g. not related to the return variable) are purged.

The detail of the CG defination and implementation and the translation process are in [CFG2CG source code](https://github.com/LC-John/RangeAnalysis/src/constraint.py). You may run constraint.py to generate a CG text file, or run constraint_plot.py to generate a rough CG figure.

The CG's are generated for each function, and there are function invoking nodes in the CG's. We generated the full-CG, which has no function invoking nodes. An invoking node has several precursor nodes as arguments, and one successor node as return value. By linking the precursor nodes of the invoking node and the argument nodes of the CG of the invoked function, and the successor node of the invoking node and the return node of the invoked function, the invoking node is purged and the invoked function CG is linked into the invoking CG.

The detail of the full-CG linking process is in [CFG2CG source code](https://github.com/LC-John/RangeAnalysis/src/full-constraint.py). You may run full_constraint.py to generate a full-CG text file, or run full_constraint_plot.py to generate a rough full-CG figure.

## Range Analysis

Following the paper, we implement the "widen-ft-narrow" method. We believe that the future propagation process can be merged into the widen process. SCC algorithm is not applied, instead, we choose the easier but much more time-consuming iterative method.

The detail of the widen-ft-narrow process is in [CFG2CG source code](https://github.com/LC-John/RangeAnalysis/src/range_analysis.py). You may run range_analysis.py to run the range analysis.

## References

[1] Aho A V, Ullman J D. Principles of Compiler Design (Addison-Wesley series in computer science and information processing)[M]. Addison-Wesley Longman Publishing Co., Inc., 1977.

[2] Harrison W H. Compiler analysis of the value ranges for variables[J]. IEEE Transactions on software engineering, 1977 (3): 243-250.

[3] Rodrigues R E, Campos V H S, Pereira F M Q. A fast and low-overhead technique to secure programs against integer overflows[C]//Code Generation and Optimization (CGO), 2013 IEEE/ACM International Symposium on. IEEE, 2013: 1-11.