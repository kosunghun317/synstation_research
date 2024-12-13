import numpy as np
import scipy as sp
import matplotlib.pyplot as plt


class CPMM:
    def __init__(self, _L: float, _P: float, _fee_rate: float):
        self.L = _L
        self.P = _P
        self.fee_rate = _fee_rate
