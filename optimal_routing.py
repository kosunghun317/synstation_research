import numpy as np


class AMM:
    def __init__(self, X, p, fee_bps):
        """
        Invariant Curve: (X + L) * Y = L**2
        """
        self.X = X
        self.L = X * np.sqrt(p) / (1 - np.sqrt(p))
        self.Y = self.L * np.sqrt(p)
        self.fee_bps = fee_bps
        self.fee_X = 0
        self.fee_Y = 0

    def buy_X(self, dx):
        dx = np.clip(
            dx, 0, self.X * (10**4 - self.fee_bps) / 10**4
        )  # you cannot buy more than the pool has

        new_X = self.X - dx
        new_Y = self.L**2 / (new_X + self.L)
        fee_accu = (new_Y - self.Y) * self.fee_bps / 10**4
        dy = new_Y - self.Y + fee_accu

        self.fee_Y += fee_accu
        self.X = new_X
        self.Y = new_Y

        return dy

    def sell_X(self, dx):
        fee_accu = dx * self.fee_bps / 10**4
        new_X = self.X + dx - fee_accu
        new_Y = self.L**2 / (new_X + self.L)
        dy = new_Y - self.Y

        self.fee_X += fee_accu
        self.X = new_X
        self.Y = new_Y

        return dy

    def get_prob(self):
        return self.Y / (self.X + self.L)

    def get_quote(self, dx, is_buy):
        if is_buy:
            dx = np.clip(dx, 0, self.X * (10**4 - self.fee_bps) / 10**4)

            new_X = self.X - dx
            new_Y = self.L**2 / (new_X + self.L)
            fee_accu = (new_Y - self.Y) * self.fee_bps / 10**4
            dy = new_Y - self.Y + fee_accu
        else:
            fee_accu = dx * self.fee_bps / 10**4
            new_X = self.X + dx - fee_accu
            new_Y = self.L**2 / (new_X + self.L)
            dy = self.Y - new_Y

        return dy


def buy_quote(amms, i, dx, dx_i):
    n = len(amms)

    # GM -> O_i
    quote_i = amms[i].get_quote(dx_i, True)

    # GM -> O_j for j in range(n)
    # O_j -> GM for j != i
    quote_j = np.sum([amms[j].get_quote(dx - dx_i, False) for j in range(n) if j != i])

    dy = quote_i + dx - dx_i - quote_j

    return dy


def buy_multiple(amms, i, dx, dx_i):
    n = len(amms)

    # GM -> O_i
    dy_i = amms[i].buy_X(dx_i)

    # GM -> O_j for j in range(n)
    # O_j -> GM for j != i
    dy_j = np.sum([amms[j].sell_X(dx - dx_i) for j in range(n) if j != i])

    dy = dy_i + dx - dx_i - dy_j

    return dy

def sell_quote(amms, i, dx, dx_i):
    pass

def sell_multiple(amms, i, dx, dx_i):
    pass

if __name__ == "__main__":
    n = np.random.randint(2,10)

    amms = [AMM(10000 + 1000 * i, 1 / n, 30) for i in range(n)]

    i = np.random.randint(0, n-1)
    total_dx = np.random.randint(1, 20000)
    left = 0
    right = amms[i].X * (10**4 - amms[i].fee_bps) / 10**4
    precision = 1e-2

    while abs(left - right) > precision:
        mid1 = left + (right - left) / 3
        mid2 = right - (right - left) / 3

        f1 = buy_quote(amms, i, total_dx, mid1)
        f2 = buy_quote(amms, i, total_dx, mid2)

        if f1 > f2:
            left = mid1
        else:
            right = mid2

    optimal_dx_i = (left + right) / 2
    optimal_result = buy_quote(amms, i, total_dx, optimal_dx_i)

    # print the optimal dx_i, states before and after the trade
    print(f"Optimal Split: \nPath 1: {optimal_dx_i} \nPath 2: {total_dx - optimal_dx_i}")
    print(f"Before: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")

    buy_multiple(amms, i, total_dx, optimal_dx_i)

    print("-" * 50)
    print(f"After: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")
