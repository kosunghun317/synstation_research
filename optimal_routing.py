import numpy as np
import tabulate


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
        fee_accu = (new_Y - self.Y) * 10**4 / (10**4 - self.fee_bps)
        dy = new_Y - self.Y + fee_accu

        self.fee_Y += fee_accu
        self.X = new_X
        self.Y = new_Y

        return dy

    def sell_X(self, dx):
        fee_accu = dx * self.fee_bps / 10**4
        new_X = self.X + dx - fee_accu
        new_Y = self.L**2 / (new_X + self.L)
        dy = self.Y - new_Y

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

        return dy  # dy should be always positive


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
    n = len(amms)

    # O_i -> GM
    quote_i = amms[i].get_quote(dx_i, False)

    # GM -> O_j for j != i
    # O_j -> GM for j in range(n)
    quote_j = np.sum([amms[j].get_quote(dx - dx_i, True) for j in range(n) if j != i])

    dy = quote_i + dx - dx_i - quote_j

    return dy


def sell_multiple(amms, i, dx, dx_i):
    n = len(amms)

    # O_i -> GM
    dy_i = amms[i].sell_X(dx_i)

    # GM -> O_j for j != i
    # O_j -> GM for j in range(n)
    dy_j = np.sum([amms[j].buy_X(dx - dx_i) for j in range(n) if j != i])

    dy = dy_i + dx - dx_i - dy_j

    return dy


def find_optimal_split(amms, i, dx, is_buy):
    """
    Find the optimal split of weights for a given trade via ternary search
    """
    precision = 1e-6

    if is_buy:
        left = min(precision, amms[i].X * precision)
        right = min(dx, amms[i].X * (10**4 - amms[i].fee_bps) / 10**4)
    else:
        left = max(
            precision,
            dx
            - min([amms[j].X for j in range(len(amms)) if j != i])
            * (10**4 - amms[i].fee_bps)
            / 10**4,
        )
        right = dx

    if is_buy:
        while right / left > 1 + precision:
            mid1 = left + (right - left) / 3
            mid2 = right - (right - left) / 3

            f1 = buy_quote(amms, i, dx, mid1)
            f2 = buy_quote(amms, i, dx, mid2)

            if f1 > f2:
                left = mid1
            else:
                right = mid2
    else:
        while right / left > 1 + precision:
            mid1 = left + (right - left) / 3
            mid2 = right - (right - left) / 3

            f1 = sell_quote(amms, i, dx, mid1)
            f2 = sell_quote(amms, i, dx, mid2)

            if f1 < f2:
                left = mid1
            else:
                right = mid2

    return (left + right) / 2


def generate_input(n=0, fee_bps=0):
    """
    Generate random input for testing: AMMs and trade size
    """
    if fee_bps == 0:
        fee_bps = np.random.choice([1, 5, 10, 30, 100])
    if n == 0:
        n = np.random.randint(2, 10)
    L_array = [10_000 + np.random.randint(0, 100_000) for _ in range(n)]
    p_array = [np.random.randint(1, 100) for _ in range(n)]
    p_sum = sum(p_array)
    for i in range(n):
        p_array[i] /= p_sum

    amms = [AMM(L_array[i], p_array[i], fee_bps) for i in range(n)]

    i = np.random.randint(0, n - 1)
    total_dx = np.random.randint(1, 100_000) * n

    return amms, i, total_dx


def test_buy():
    amms, i, total_dx = generate_input()

    optimal_dx_i = find_optimal_split(amms, i, total_dx, True)

    # print the optimal dx_i, states before and after the trade
    print(
        f"Optimal Split: \nPath 1: {optimal_dx_i} \nPath 2: {total_dx - optimal_dx_i}"
    )
    print("-" * 50)
    print(f"Before: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")

    buy_multiple(amms, i, total_dx, optimal_dx_i)

    print("-" * 50)
    print(f"After: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")


def test_sell():
    amms, i, total_dx = generate_input()

    optimal_dx_i = find_optimal_split(amms, i, total_dx, False)

    # print the optimal dx_i, states before and after the trade
    print(
        f"Optimal Split: \nPath 1: {optimal_dx_i} \nPath 2: {total_dx - optimal_dx_i}"
    )
    print("-" * 50)
    print(f"Before: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")

    sell_multiple(amms, i, total_dx, optimal_dx_i)

    print("-" * 50)
    print(f"After: {sum([amm.get_prob() for amm in amms])}")
    for amm in amms:
        print(f"X: {amm.X}, Y: {amm.Y}, P: {amm.get_prob()}")


if __name__ == "__main__":
    print("Test Optimal Buy")
    test_buy()
    print("-" * 50)
    print("Test Optimal Sell")
    test_sell()
