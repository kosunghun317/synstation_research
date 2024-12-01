import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

# We want to find the fee rate gamma that in expectation makes LPing profitable
# Market Proposer pays B, and Treasury will add B / (2 * (sqrt(2) - 1)) to open a market
# There will be 2 outcomes, O_1 and O_2, with initial probabilities 0.5 each
# The market will be settled with the final values p and 1 - p


def generate_price_paths(
    T: int = 30,  # 30 days, for monthly contracts
    n: int = 1000,  # number of paths to generate
    sigma: float = 0.01,  # 1% daily volatility
    P_0: float = 1000,  # initial price
):
    """
    Generate n price paths from Geometric Brownian Motion.
    mu is set according to sigma to make path martingale.
    """
    P = np.zeros((n, T))

    for i in range(n):
        z = np.cumsum(np.random.normal(0, sigma, T))
        P[i] = P_0 * np.exp(z - (sigma**2) * np.arange(T) / 2)

    return P


def get_L(B):
    return B / (2 * (np.sqrt(2) - 1))


def get_S(
    P: float = 1000,  # price at maturity
    P_0: float = 1000,  # initial price
    delta: int = 1,  # delta
    up: bool = True,  # whether given outcome token is up or down
):
    """
    Calculate the redemption value of S, the derivative, based on given parameters.
    """
    if up:
        return max(0, min(1, 0.5 * (1 + delta * (P - P_0) / P_0)))
    else:
        return max(0, min(1, 0.5 * (1 - delta * (P - P_0) / P_0)))


def get_LP_value(
    B: float = 1000,  # payment from proposer
    S: float = 0.5,  # redemption value of S
):
    """
    Calculate the value of LP's position given the redemption value of S.
    Value = L * (2 * sqrt(S) - S + 2 * sqrt(1 - S) - (1 - S))
    """
    L = get_L(B)
    return L * (2 * np.sqrt(S) + 2 * np.sqrt(1 - S) - 1)


def get_LP_loss(B, S):
    return get_LP_value(B, 0.5) - get_LP_value(B, S)


def get_LP_losses(
    P,  # price paths
    B: float = 1000,  # payment from proposer
    delta: int = 1,  # delta
):
    """
    P is n by T array where n is the number of paths and T is the number of time steps
    for each time step, calculate the LP's loss, then take the summation
    return the array of losses
    """
    n, T = P.shape
    losses = np.zeros(n)
    for i in range(n):
        losses[i] = get_LP_loss(
            B, get_S(P[i, T - 1], P_0=P[i, 0], delta=delta, up=True)
        )

    return losses


def get_swap_fee_earnings(
    P,  # price paths
    B: float = 1000,  # payment from proposer
    delta: int = 1,  # delta
    gamma: float = 0.01,  # fee rate
):
    """
    P is n by T array where n is the number of paths and T is the number of time steps
    for each time step, calculate the swap fee earnings, then take the summation
    volume = L * (sqrt(S_t) - sqrt(S_{t-1})) + L * (sqrt(1 - S_t) - sqrt(1 - S_{t-1}))
    fee_earned = gamma * volume
    return the array of fee_earned
    """
    n, T = P.shape
    fee_earned = np.zeros(n)
    for i in range(n):
        for t in range(1, T):
            S_current = get_S(P[i, t], P_0=P[i, 0], delta=delta, up=True)
            S_prev = get_S(P[i, t - 1], P_0=P[i, 0], delta=delta, up=True)
            volume = get_L(B) * (
                abs(np.sqrt(S_current) - np.sqrt(S_prev))
                + abs(np.sqrt(1 - S_current) - np.sqrt(1 - S_prev))
            )
            fee_earned[i] += gamma * volume

    return fee_earned


def main():
    # parameters
    B = 10000
    delta = 1
    gamma = 0.005
    k = 1 # share of proposer among all swap fee earnings
    T = 30 * 24
    n = 1000
    sigma = 0.02 / np.sqrt(24)
    P_0 = 1000

    # generate price paths
    P = generate_price_paths(T, n, sigma, P_0)

    # calculate LP losses
    LP_losses = get_LP_losses(P, B, delta)

    # calculate swap fee earnings
    fee_earned = k * get_swap_fee_earnings(P, B, delta, gamma)

    # calculate total profit
    total_profit = fee_earned - LP_losses

    # plot the histogram of total profit
    plt.hist(total_profit, bins=50)
    expected_total_profit = np.mean(total_profit)
    plt.axvline(
        expected_total_profit, color="r", linestyle="dashed", linewidth=2
    )  # add the expected total profit line
    plt.legend(["Expected Total Profit"])
    plt.xlabel("Total Profit")
    plt.ylabel("Frequency")
    plt.title("Histogram of Total Profit")
    plt.show()

    # calculate the expected total profit
    expected_total_profit = np.mean(total_profit)
    print(f"Expected Total Profit: {expected_total_profit}")


if __name__ == "__main__":
    main()
