import copy as cp

class CalculationRecorder:
    def __init__(self, ):
        self.value_lst = []
        self.op_lst = []
        self.inv_op = {'+':'-', '-':'+', '*':'/', '/':'*', '//':'*'}

    def __add__(self, x):
        self.value_lst += [x]
        self.op_lst += ['+']
        return cp.deepcopy(self)
        
    def __sub__(self, x):
        self.value_lst += [x]
        self.op_lst += ['-']
        return cp.deepcopy(self)

    def __mul__(self, x):
        self.value_lst += [x]
        self.op_lst += ['*']
        return cp.deepcopy(self)

    def __truediv__(self, x):
        self.value_lst += [x]
        self.op_lst += ['/']
        return cp.deepcopy(self)

    def __floordiv__(self, x):
        self.value_lst += [x]
        self.op_lst += ['//']
        return cp.deepcopy(self)

    def forward(self, x):
        for v, op in zip(self.value_lst, self.op_lst):
            x = eval('x {} {}'.format(op, v))
        return x

    def backward(self, x):
        for v, op in zip(self.value_lst[::-1], self.op_lst[::-1]):
            x = eval('x {} {}'.format(self.inv_op[op], v))
        return x
