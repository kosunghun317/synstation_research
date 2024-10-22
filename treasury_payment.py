import numpy as np


def get_y_0_y_1(x_0, p_0):
    assert x_0 > 0
    assert p_0 < 1 and p_0 > 0

    L = x_0 * np.sqrt(p_0)

    y_0 = L * np.sqrt(p_0)
    y_1 = L

    return (y_0, y_1)


def get_expected_treasury_payment(B, p_array):
    """
    Given payment from proposer and probability distribution of outcomes,
    this function calculates the expectation of leftover fund after settlement,
    and returns the amount that the treasury should pay.
    """
    assert B > 0
    for p in p_array:
        assert p > 0 and p < 1

    # caculate the expected leftover fund after settlement,
    # when the 1 USD is used for minting outcome tokens (i.e, X == 1)
    # this is the maximum amount that the treasury can pay
    expected_fund_share = np.sum([get_y_0_y_1(1, p)[1] * p for p in p_array])

    deployer_share = (
        1 + sum([get_y_0_y_1(1, p)[0] for p in p_array]) - expected_fund_share
    )

    X = B / deployer_share

    return X * expected_fund_share


def get_guaranteed_treasury_payment(B, p_array):
    """
    Given payment from proposer and probability distribution of outcomes,
    this function calculates the minimum leftover fund after settlement,
    and returns the amount that the treasury should pay.
    We assume sum of probabilities is 1.
    """
    assert B > 0
    for p in p_array:
        assert p > 0 and p < 1

    # caculate the guaranteed leftover fund after settlement,
    # when the 1 USD is used for minting outcome tokens (i.e, X == 1)
    # this is the maximum amount that the treasury can pay
    guaranteed_fund_share = np.min([get_y_0_y_1(1, p)[1] for p in p_array])

    deployer_share = (
        1 + sum([get_y_0_y_1(1, p)[0] for p in p_array]) - guaranteed_fund_share
    )

    X = B / deployer_share

    return X * guaranteed_fund_share


def test_uniform_dist(n=2, B=1_000):
    """
    Test the result of the treasury payment calculation
    under uniform distribution of outcomes.
    """
    p_array = [1 / n for _ in range(n)]
    q_array = [1 / n for _ in range(n)]

    print(f"n= {n}")
    print(f"exp: {get_expected_treasury_payment(B, p_array)}")
    print(f"min: {get_guaranteed_treasury_payment(B, q_array)}")


def test_non_uniform_dist(n=2, B=1_000):
    """
    Test the result of the treasury payment calculation
    under non-uniform distribution of outcomes.
    """
    np.random.seed(20180759)
    p_array = np.random.rand(n)
    p_array = p_array / np.sum(p_array)
    q_array = np.random.rand(n)
    q_array = q_array / np.sum(q_array)

    print(f"{n}-outcomes distribution: {p_array}")
    print(f"exp: {get_expected_treasury_payment(B, p_array)}")
    print(f"min: {get_guaranteed_treasury_payment(B, q_array)}")


if __name__ == "__main__":
    print("Test with uniform distribution")
    for i in range(2, 11):
        test_uniform_dist(i)

    print("-" * 20)

    print("Test with non-uniform distribution")
    for i in range(2, 11):
        test_non_uniform_dist(i)
