import re
import pickle

from sortedcontainers import SortedSet
from sympy import Poly, simplify, expand, S, default_sort_key, Intersection, Interval, Expr, Symbol
from sympy.solvers.inequalities import solve_poly_inequality, solve_poly_inequalities

from ParetoLib.Geometry.Point import *

import ParetoLib.Oracle.Oracle
# from ParetoLib.Oracle import vprint
from . import vprint, eprint


# from data_generator import *

class Condition:
    # Condition = f op g
    # type(f) = sympy.Expr
    # type(g) = sympy.Expr
    # type(op) = string in {'>', '>=', '<', '<=', '==', '!='}
    #
    # Example
    # inequality = (sympy.Poly(f - g), op)

    def __init__(self, f='x', op='==', g='0'):
        # type: (_, str, str, str) -> None
        self.comparison = ['==', '>', '<', '>=', '<=', '<>']
        assert (op in self.comparison), "Operator " + op + " must be any of: {'>', '>=', '<', '<=', '==', '!='}"
        assert (not f.isdigit() or not g.isdigit()), \
            "At least '" + f + "' or '" + g + "' must be a polynomial expression (i.e., not a single number)"
        self.op = op
        self.f = simplify(f)
        self.g = simplify(g)

        if not self.all_coeff_are_positive():
            eprint("WARNING! Expression '%s' contains negative coefficients: %s"
                   % (str(self.get_expression()), str(self.get_expression_with_negative_coeff())))

    def initFromString(self, poly_function):
        # op_exp = (=|>|<|>=|<|<=|<>)\s\d+
        # f_regex = r'(\s*\w\s*)+'
        # g_regex = r'(\s*\w\s*)+'
        vprint('Polynomial string ', poly_function)

        op_comp = "|".join(self.comparison)
        op_regex = r'(%s)' % op_comp
        f_regex = r'[^%s]+' % op_comp
        g_regex = r'[^%s]+' % op_comp
        regex = r'(?P<f>(%s))(?P<op>(%s))(?P<g>(%s))' % (f_regex, op_regex, g_regex)
        regex_comp = re.compile(regex)
        result = regex_comp.match(poly_function)
        vprint('Parsing result ', str(result))
        # if regex_comp is not None:
        if result is not None:
            self.op = result.group('op')
            self.f = simplify(result.group('f'))
            self.g = simplify(result.group('g'))
            vprint('(op, f, g): (%s, %s, %s) ' % (self.op, self.f, self.g))

            if not self.all_coeff_are_positive():
                eprint("WARNING! Expression '%s' contains negative coefficients: %s"
                       % (str(self.get_expression()), str(self.get_expression_with_negative_coeff())))

    # Printers
    def __repr__(self):
        # type: (Condition) -> str
        return self.toStr()

    def __str__(self):
        # type: (Condition) -> str
        return self.toStr()

    def toStr(self):
        # type: (Condition) -> str
        return str(self.f) + self.op + str(self.g)

    # Equality functions
    def __eq__(self, other):
        # type: (Condition, Condition) -> bool
        return (self.f == other.f) and \
               (self.op == other.op) and \
               (self.g == other.g)

    def __ne__(self, other):
        # type: (Condition, Condition) -> bool
        return not self.__eq__(other)

    # Identity function (via hashing)
    def __hash__(self):
        # type: (Condition) -> int
        return hash((self.f, self.op, self.g))

    # Membership functions
    def __contains__(self, p):
        # type: (Condition, tuple) -> bool
        return self.member(p) is True

    def all_coeff_are_positive(self):
        # type: (Condition) -> bool
        coeffs = self.get_coeff_of_expression()
        all_positives = True
        for i in coeffs:
            all_positives = all_positives and (coeffs[i] >= 0)
        return all_positives

    def get_coeff_of_expression(self):
        # type: (Condition) -> dict
        expr = self.get_expression()
        expanded_expr = expand(expr)
        simpl_expr = simplify(expanded_expr)
        coeffs = simpl_expr.as_coefficients_dict()
        return coeffs

    def get_positive_coeff_of_expression(self):
        # type: (Condition) -> dict
        expr = self.get_expression()
        expanded_expr = expand(expr)
        simpl_expr = simplify(expanded_expr)
        coeffs = simpl_expr.as_coefficients_dict()
        positive_coeff = {i: coeffs[i] for i in coeffs if coeffs[i] >= 0}
        return positive_coeff

    def get_negative_coeff_of_expression(self):
        # type: (Condition) -> dict
        expr = self.get_expression()
        expanded_expr = expand(expr)
        simpl_expr = simplify(expanded_expr)
        coeffs = simpl_expr.as_coefficients_dict()
        negative_coeff = {i: coeffs[i] for i in coeffs if coeffs[i] < 0}
        return negative_coeff

    def get_expression_with_negative_coeff(self):
        # type: (Condition) -> Expr
        negative_coeff = self.get_negative_coeff_of_expression()
        l = ['%s * %s' % (negative_coeff[i], i) for i in negative_coeff]
        return simplify(''.join(l))

    def get_expression_with_positive_coeff(self):
        # type: (Condition) -> Expr
        positive_coeff = self.get_positive_coeff_of_expression()
        l = ['%s * %s' % (positive_coeff[i], i) for i in positive_coeff]
        return simplify('+'.join(l))

    def get_expression(self):
        # type: (Condition) -> Expr
        return simplify(self.f - self.g)

    def get_variables(self):
        # type: (Condition) -> list
        expr = self.get_expression()
        return sorted(expr.free_symbols, key=default_sort_key)

    def eval_tuple(self, xpoint):
        # type: (Condition, tuple) -> Expr
        keys_fv = self.get_variables()
        di = {key: xpoint[i] for i, key in enumerate(keys_fv)}

        vprint('Condition ', str(self), ' evaluates ', str(xpoint), ' to ', str(self.eval_dict(di)))
        vprint('di ', str(di))
        return self.eval_dict(di)

    def eval_dict(self, d=None):
        # type: (Condition, dict) -> Expr
        keys_fv = self.get_variables()
        if d is None:
            # di = dict.fromkeys(expr.free_symbols)
            di = {key: 0 for key in keys_fv}
        else:
            di = d
            keys = set(d.keys())
            assert keys.issuperset(keys_fv), "Keys in dictionary " \
                                             + str(d) \
                                             + " do not match with the variables in the condition"
        expr = self.get_expression()
        res = expr.subs(di)
        ex = str(res) + self.op + '0'
        vprint('Expression ', str(simplify(ex)))
        return simplify(ex)

    def eval_var_val(self, variable=None, val='0'):
        # type: (Condition, Symbol, int) -> Expr
        if variable is None:
            fvset = self.get_variables()
            fv = fvset.pop()
        else:
            fv = variable
        expr = self.get_expression()
        res = expr.subs(fv, val)
        ex = str(res) + self.op + '0'
        vprint('Expression ', str(simplify(ex)))
        return simplify(ex)

    # Membership functions
    def member(self, xpoint):
        # type: (Condition, tuple) -> Expr
        keys = self.get_variables()
        di = {key: xpoint[i] for i, key in enumerate(keys)}
        return self.eval_dict(di)

    def membership(self):
        # type: (Condition, tuple) -> function
        return lambda xpoint: self.member(xpoint)

    # Read/Write file functions
    def fromFile(self, fname='', human_readable=False):
        # type: (Condition, str, bool) -> None
        assert (fname != ''), "Filename should not be null"

        mode = 'rb'
        finput = open(fname, mode)
        if human_readable:
            self.fromFileHumRead(finput)
        else:
            self.fromFileNonHumRead(finput)
        finput.close()

    def fromFileNonHumRead(self, finput=None):
        # type: (Condition, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        self.f = pickle.load(finput)
        self.op = pickle.load(finput)
        self.g = pickle.load(finput)

    def fromFileHumRead(self, finput=None):
        # type: (Condition, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        poly_function = finput.readline()
        self.initFromString(poly_function)

    def toFile(self, fname='', append=False, human_readable=False):
        # type: (Condition, str, bool, bool) -> None
        assert (fname != ''), "Filename should not be null"

        if append:
            mode = 'ab'
        else:
            mode = 'wb'

        foutput = open(fname, mode)
        if human_readable:
            self.toFileHumRead(foutput)
        else:
            self.toFileNonHumRead(foutput)
        foutput.close()

    def toFileNonHumRead(self, foutput=None):
        # type: (Condition, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        pickle.dump(self.f, foutput, pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.op, foutput, pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.g, foutput, pickle.HIGHEST_PROTOCOL)

    def toFileHumRead(self, foutput=None):
        # type: (Condition, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        # str(self.f) + self.op + str(self.g)
        foutput.write(str(self) + '\n')


# class OracleFunction(ParetoLib.Oracle.Oracle):
class OracleFunction:
    # An OracleFunction is a set of Conditions
    def __init__(self):
        # type: (OracleFunction, int) -> None
        #self.variables = set()
        self.variables = SortedSet(key=default_sort_key)
        self.oracle = set()

    # Printers
    def __repr__(self):
        # type: (OracleFunction) -> str
        return self.toStr()

    def __str__(self):
        # type: (OracleFunction) -> str
        return self.toStr()

    def toStr(self):
        # type: (OracleFunction) -> str
        return str(self.oracle)

    # Equality functions
    def __eq__(self, other):
        # type: (OracleFunction, OracleFunction) -> bool
        return self.oracle == other.oracle

    def __ne__(self, other):
        # type: (OracleFunction, OracleFunction) -> bool
        return not self.__eq__(other)

    # Identity function (via hashing)
    def __hash__(self):
        # type: (OracleFunction) -> int
        return hash(tuple(self.oracle))

    # Addition of a new condition
    def add(self, cond):
        # type: (OracleFunction, Condition) -> None
        self.variables = self.variables.union(cond.get_variables())
        self.oracle.add(cond)

    def get_variables(self):
        # type: (OracleFunction) -> list
        #variable_list = sorted(self.variables, key=default_sort_key)
        variable_list = list(self.variables)
        return variable_list

    def dim(self):
        # type: (OracleFunction) -> int
        return len(self.get_variables())

    def eval_tuple(self, xpoint):
        # type: (OracleFunction, tuple) -> bool
        #_eval_list = [cond.eval_tuple(xpoint) for cond in self.oracle]
        _eval_list = [cond.eval_tuple(xpoint) == True for cond in self.oracle]
        # All conditions are true (i.e., 'and' policy)
        _eval = all(_eval_list)
        # Any condition is true (i.e., 'or' policy)
        #_eval = any(_eval_list)
        vprint('OracleFunction evaluates ', str(xpoint), ' to ', str(_eval))
        return _eval

    def eval_dict(self, d=None):
        # type: (OracleFunction, dict) -> bool
        #_eval_list = [cond.eval_dict(d) for cond in self.oracle]
        _eval_list = [cond.eval_dict(d) == True for cond in self.oracle]
        # All conditions are true (i.e., 'and' policy)
        _eval = all(_eval_list)
        # Any condition is true (i.e., 'or' policy)
        #_eval = any(_eval_list)
        vprint('OracleFunction evaluates ', str(_eval_list), ' in ', self.toStr(), ' to ', str(_eval))
        return _eval

    def eval_var_val(self, var=None, val='0'):
        # type: (OracleFunction, Symbol, int) -> bool
        _eval_list = [cond.eval_var_val(var, val) == True for cond in self.oracle]
        # All conditions are true (i.e., 'and' policy)
        _eval = all(_eval_list)
        # Any condition is true (i.e., 'or' policy)
        # _eval = any(_eval_list)
        vprint('OracleFunction evaluates ', str(_eval_list), ' in ', self.toStr(), ' to ', str(_eval))
        return _eval

    # Membership functions
    def __contains__(self, p):
        # type: (OracleFunction, tuple) -> bool
        return self.member(p) is True

    def member(self, xpoint):
        # type: (OracleFunction, tuple) -> bool
        # return self.eval_tuple(xpoint)
        vprint(xpoint)
        #keys = self.get_variables()
        keys = self.variables
        di = {key: xpoint[i] for i, key in enumerate(keys)}
        # di = dict.fromkeys(keys)
        return self.eval_dict(di)

    def membership(self):
        # type: (OracleFunction) -> function
        return lambda xpoint: self.member(xpoint)

    # Read/Write file functions
    def fromFile(self, fname='', human_readable=False):
        # type: (OracleFunction, str, bool) -> None
        assert (fname != ''), "Filename should not be null"

        mode = 'rb'
        finput = open(fname, mode)
        if human_readable:
            self.fromFileHumRead(finput)
        else:
            self.fromFileNonHumRead(finput)
        finput.close()

    def fromFileNonHumRead(self, finput=None):
        # type: (OracleFunction, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        self.oracle = pickle.load(finput)
        self.variables = pickle.load(finput)

    def fromFileHumRead(self, finput=None):
        # type: (OracleFunction, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        # Each line has a Condition
        for line in finput:
            cond = Condition()
            cond.initFromString(line)
            self.add(cond)

    def toFile(self, fname='', append=False, human_readable=False):
        # type: (OracleFunction, str, bool, bool) -> None
        assert (fname != ''), "Filename should not be null"

        if append:
            mode = 'ab'
        else:
            mode = 'wb'

        foutput = open(fname, mode)
        if human_readable:
            self.toFileHumRead(foutput)
        else:
            self.toFileNonHumRead(foutput)
        foutput.close()

    def toFileNonHumRead(self, foutput=None):
        # type: (OracleFunction, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        pickle.dump(self.oracle, foutput, pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.variables, foutput, pickle.HIGHEST_PROTOCOL)

    def toFileHumRead(self, foutput=None):
        # type: (OracleFunction, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        # Each line has a Condition
        for cond in self.oracle:
            cond.toFileHumRead(foutput)


EPS = 1e-1


def staircase_oracle(xs, ys):
    # type: (tuple, tuple) -> function
    return lambda p: any(p[0] >= x and p[1] >= y for x, y in zip(xs, ys))


# Point (p0,p1) is closer than a 'epsilon' to point (x,y), which is member point
def membership_oracle(xs, ys, epsilon=EPS):
    # type: (tuple, tuple, float) -> function
    return lambda p: any((abs(p[0] - x) <= epsilon) and (abs(p[1] - y) <= epsilon) for x, y in zip(xs, ys))