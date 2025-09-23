"""Plotting utilities for ply assignment."""
import matplotlib.pyplot as plt
from typing import Optional


def plot_grid(
    grid,
    scalar: Optional[str] = None,
    x_axis: str = "x",
    y_axis: str = "y",
) -> None:
    """Plot the grid thickness distribution using matplotlib scatter."""
    if scalar and scalar in grid.cell_data:
        x = grid.cell_data[x_axis]
        y = grid.cell_data[y_axis]
        c = grid.cell_data[scalar]
        plt.scatter(x, y, c=c, cmap='viridis')
        plt.colorbar(label=scalar)
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.title(f"Thickness distribution: {scalar}")
        plt.axis('equal')
        plt.show()
    else:
        print("Scalar not found or not provided.")
