from synstation import amm
import numpy as np
import tabulate


def spectral_market_simulation(
    bid,  # initial bid for proposing new market
    fee_bps,  # fee in basis points
    daily_transaction,  # number of transaction per day. Polymarket: around 200k
    min_size,  # minimum size of trade
    max_size,  # maximum size of trade
    initial_price,  # initial price of underlying asset
    volatility,  # daily volatility
    block_time,  # seconds
    period,  # days
):
    """
    price follows GBM
    arbitrageur comes every block and try to make profit
    noise trader arrival is Poisson process,
    with size of trade is Uniform(0,100)
    """
    # initialize market
    market = amm.BinaryMarket(bid=bid, fee_bps=fee_bps)
    initial_value = market.get_value(0.5)

    # generate price of underlying asset
    W = np.random.normal(
        0, volatility * np.sqrt(block_time / 86400), int(period * 86400 / block_time)
    ).cumsum()
    P = initial_price * np.exp(W)

    # fundamental value of UP token
    P_min = initial_price * np.exp(-volatility * np.sqrt(period) * 2)
    P_max = initial_price * 2 - P_min
    P_ext = np.clip((P - P_min) / (P_max - P_min), 0, 1)

    # generate poisson arrival of noise trader
    arrival_rate = daily_transaction / 86400 * block_time
    num_trades = np.random.poisson(arrival_rate * len(P))
    arrival_times = np.sort(np.random.randint(0, len(P), num_trades))

    # generate size of trade
    trade_size = np.random.uniform(min_size, max_size, num_trades)

    # simulate market
    total_trades = 0
    for i in range(len(P)):
        # arbitrageur
        market.arbitrage(P_ext[i])

        # noise trader
        if i in arrival_times:
            market.noise_trade(trade_size[total_trades])
            total_trades += 1

    final_value = market.get_value(P_ext[-1])

    return (final_value - initial_value, market.total_fee())


if __name__ == "__main__":
    # testing fee rates: 1, 5, 10, 20, 30, 50, 100 (bps)
    fee_rates = [1, 5, 10, 20, 30, 50, 100]
    results = []

    for fee_rate in fee_rates:
        result = []

        for _ in range(20):
            pnl, fee_earned = spectral_market_simulation(
                bid=10_000,  # initial bid for proposing new market
                fee_bps=fee_rate,
                daily_transaction=200,  # 0.1% of Polymarket
                min_size=1,
                max_size=100,
                initial_price=4000,
                volatility=0.01,  # 1% daily volatility
                block_time=2,  # 2 seconds per block
                period=30,  # 30 days
            )
            result.append([pnl, fee_earned])

        result = np.array(result)
        results.append(
            [
                fee_rate,
                np.mean(result[:, 0]),
                np.std(result[:, 0]),
                np.mean(result[:, 1]),
                np.std(result[:, 1]),
            ]
        )

    print(
        tabulate.tabulate(
            results,
            headers=[
                "Fee Rate (bps)",
                "Mean (PnL)",
                "Std (PnL)",
                "Mean (Fee Earned)",
                "Std (Fee Earned)",
            ],
            tablefmt="pretty",
        )
    )
