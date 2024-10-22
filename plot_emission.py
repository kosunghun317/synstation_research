import numpy as np
import matplotlib.pyplot as plt


# Function to calculate Y(t)
def supply_over_time(M, H, time_range):
    t = np.linspace(0, time_range, 1000)  # Create a time array from 0 to time_range
    Y_t = M * (1 - 2 ** (-t / H))  # Apply the formula
    return t, Y_t


# Function to plot the result
def plot_supply(M, H, time_range):
    t, Y_t = supply_over_time(M, H, time_range)

    plt.figure(figsize=(8, 6))
    plt.plot(t, Y_t, label=f"M = {M}, H = {H}")
    plt.axhline(y=M, color="r", linestyle="--", label="Maximum Emission (M)")
    plt.title("Emission over Time")
    plt.xlabel("Time (t)")
    plt.ylabel("Emission (Y(t))")
    plt.grid(True)
    plt.legend()
    plt.show()


# Example input
# 1B Total Supply, Halving every 365 days, 4 years
M = 1_000_000_000 * 0.5
H = 365
time_range = 4 * H

plot_supply(M, H, time_range)
