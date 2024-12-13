import numpy as np


class AMM:
    def __init__(self, X, p, fee_bps):
        """
        (X + L) * Y = L**2
        fee is always charged in token Y
        """
        self.L = X * np.sqrt(p) / (1 - np.sqrt(p))
        self.X = X
        self.Y = X * p / (1 - np.sqrt(p))
        self.fee_bps = fee_bps
        self.fee_accumulated = 0

    def buy(self, dy):
        """
        Noise trader sells dy amount of token Y
        to buy X from AMM
        """
        new_Y = np.clip(self.Y + dy, 1, self.L)
        new_X = self.L**2 / new_Y - self.L

        self.fee_accumulated += abs(new_Y - self.Y) * self.fee_bps / 10000
        self.X = new_X
        self.Y = new_Y

    def sell(self, dy):
        """
        Noise trader sells token X
        to receive dy amount of token Y
        """
        new_Y = np.clip(self.Y - dy, 1, self.L)
        new_X = self.L**2 / new_Y - self.L

        self.fee_accumulated += abs(new_Y - self.Y) * self.fee_bps / 10000
        self.X = new_X
        self.Y = new_Y

    def arbitrage(self, P_ext):
        """
        Arbitrageur buys or sells token Y
        to make profit from the difference between
        the external price P_ext and the AMM price
        """
        P = self.Y / (self.X + self.L)

        if P_ext > P * (1 + self.fee_bps / 10000):
            # buy X
            new_P = P_ext / (1 + self.fee_bps / 10000)
            new_Y = np.clip(self.L * np.sqrt(new_P), 1, self.L)
            new_X = self.L**2 / new_Y - self.L

            self.fee_accumulated += abs(new_Y - self.Y) * self.fee_bps / 10000
            self.X = new_X
            self.Y = new_Y
        elif P_ext * (1 + self.fee_bps / 10000) < P:
            # sell X
            new_P = P_ext * (1 + self.fee_bps / 10000)
            new_Y = np.clip(self.L * np.sqrt(new_P), 1, self.L)
            new_X = self.L**2 / new_Y - self.L

            self.fee_accumulated += abs(new_Y - self.Y) * self.fee_bps / 10000
            self.X = new_X
            self.Y = new_Y
        else:
            pass

    def get_value(self, P_ext):
        return self.Y + self.X * P_ext


class BinaryMarket:
    """
    Prediction market with range 0 to 1 and binary outcome
    Always initialized with 0.5 / 0.5 probabilities
    """

    def __init__(self, bid, fee_bps):
        X = bid / 2
        self.YesMarket = AMM(X, 0.5, fee_bps)
        self.NoMarket = AMM(X, 0.5, fee_bps)

    def get_value(self, P_ext):
        return self.YesMarket.get_value(P_ext) + self.NoMarket.get_value(1 - P_ext)

    def noise_trade(self, dy):
        """
        randomly select a market to trade
        randomly select direction
        execute trade
        """
        rand = np.random.rand()
        if rand < 0.25:
            self.YesMarket.buy(dy)
        elif rand < 0.5:
            self.YesMarket.sell(dy)
        elif rand < 0.75:
            self.NoMarket.buy(dy)
        else:
            self.NoMarket.sell(dy)

    def arbitrage(self, P_ext):
        self.YesMarket.arbitrage(P_ext)
        self.NoMarket.arbitrage(1 - P_ext)

    def total_fee(self):
        return self.YesMarket.fee_accumulated + self.NoMarket.fee_accumulated
