"""
author: Etienne Wallet

This module handlesthe plots to create and save
"""
import sys
import textwrap
from typing import Dict, List
from importlib_resources import files

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
import matplotlib.image as mpimg

import seaborn as sns

from mxops.data.analyze_data import TransactionsData
from mxops.analyze import agglomerate


def get_all_plots() -> List[str]:
    """
    Return all the plots names of this module

    :return: plot names
    :rtype: List[str]
    """
    results = []
    for func_name in dir(sys.modules[__name__]):
        if func_name.startswith("get_") and func_name.endswith("_fig"):
            results.append(func_name[4:-4])
    return results


def limit_string_length(string: str, max_length: int = 30) -> str:
    """
    Restrict a string length to a fixed threshold and replace excess
    characters with '...' in the middle

    :param string: string to restrict
    :type string: str
    :param max_length: max length, defaults to 30
    :type max_length: int, optional
    :return: _description_
    :rtype: str
    """
    if len(string) <= max_length:
        return string

    # If the label is longer than the maximum length, truncate it
    # and insert '...' in the middle
    half_max = max_length // 2  # Floor division to get an integer result
    return string[: half_max - 2] + "..." + string[-half_max + 1 :]


def get_colors(categories: List, assigned_colors: Dict | None = None) -> List:
    """
    Generated the list of colors to use for a plot

    :param categories: categories that will be plotted
    :type categories: List
    :param assigned_colors: if some colors has been already assigned to some categories
        (specified with index), defaults to None
    :type assigned_colors: Dict | None, optional
    :return: colors to plot
    :rtype: List
    """
    color_to_generated = len(categories)
    if assigned_colors is None:
        assigned_colors = {}
    else:
        color_to_generated = max(color_to_generated, max(assigned_colors.values()) + 1)
    generated_colors = sns.color_palette("bright", color_to_generated)
    colors = generated_colors[: len(categories)]
    for cat, color_index in assigned_colors.items():
        i_cat = categories.index(cat)
        color = generated_colors[color_index]
        # look if the color has already been assigned
        try:
            i_color = colors.index(color)
        except ValueError:
            i_color = None
        if i_color is None:
            colors[i_cat] = color
        else:  # swap the colors
            colors[i_cat], colors[i_color] = color, colors[i_cat]
    return colors


def set_ax_settings(ax: Axes, title: str):
    """
    Set the parameters for the ax

    :param ax: ax to set
    :type ax: Axes
    :param title: title to set
    :type title: str
    """
    wrapped_title = textwrap.fill(
        title,
        width=80,
    )
    ax.set_title(
        wrapped_title,
        fontsize=18,
        fontweight="bold",
        color="white",
    )
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_facecolor("#1E1E1E")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("gray")
    ax.spines["left"].set_color("gray")
    ax.tick_params(colors="gray")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    plt.tight_layout()

    # add logo
    logo_path = files("mxops.resources").joinpath("mxops_logo.png")
    logo = mpimg.imread(logo_path)
    # Define the extent for positioning. This is just an example; adjust as needed.
    # Format: [x_start, x_end, y_start, y_end]
    extent = [*ax.get_xlim(), *ax.get_ylim()]
    ax.imshow(logo, aspect="auto", extent=extent, alpha=0.25, zorder=0)


def get_transactions_status_per_day_fig(txs_data: TransactionsData) -> plt.Figure:
    """
    Format the transactions data and create the plot of the transactions status per day

    :param txs_data: transactions data
    :type txs_data: TransactionsData
    :return: plot created
    :rtype: plt.Figure
    """
    txs_df = agglomerate.get_transactions_df(txs_data)
    status_df = agglomerate.get_status_per_day_df(txs_df)

    plt.style.use("dark_background")
    colors = get_colors(list(status_df.columns), {"success": 2, "fail": 3, "total": 0})

    # ensure success is green, fail is
    fig, ax = plt.subplots(figsize=(12, 7))
    line_styles = ["-"] * (len(status_df.columns) - 1) + ["--"]
    title = "Transactions Status per Day"

    for idx, column in enumerate(status_df.columns):
        ax.plot(
            status_df.index,
            status_df[column],
            marker="o",
            label=column,
            color=colors[idx],
            linewidth=2.5,
            linestyle=line_styles[idx],
            alpha=0.8,
        )
    set_ax_settings(ax, title)
    return fig


def get_functions_per_day_fig(txs_data: TransactionsData) -> plt.Figure:
    """
    Format the transactions data and create the plot of the transactions
    function per day

    :param txs_data: transactions data
    :type txs_data: TransactionsData
    :return: plot created
    :rtype: plt.Figure
    """
    txs_df = agglomerate.get_transactions_df(txs_data)
    functions_df = agglomerate.get_function_per_day_df(txs_df)

    plt.style.use("dark_background")
    colors = get_colors(list(functions_df.columns))

    fig, ax = plt.subplots(figsize=(12, 7))
    line_styles = ["-"] * (len(functions_df.columns) - 1) + ["--"]
    title = "Transactions Functions per Day"

    for idx, column in enumerate(functions_df.columns):
        ax.plot(
            functions_df.index,
            functions_df[column],
            marker="o",
            label=limit_string_length(column),
            color=colors[idx],
            linewidth=2.5,
            linestyle=line_styles[idx],
            alpha=0.8,
        )
    set_ax_settings(ax, title)
    return fig


def get_unique_users_per_day_fig(txs_data: TransactionsData) -> plt.Figure:
    """
    Format the transactions data and create the plot of the unique users per day

    :param txs_data: transactions data
    :type txs_data: TransactionsData
    :return: plot created
    :rtype: plt.Figure
    """
    txs_df = agglomerate.get_transactions_df(txs_data)
    unique_users_df = agglomerate.get_unique_users_per_day_df(txs_df)

    plt.style.use("dark_background")

    color = get_colors([""])[0]
    fig, ax = plt.subplots(figsize=(12, 7))
    title = "Unique Users per Day"
    ax.plot(
        unique_users_df["date"],
        unique_users_df["sender"],
        marker="o",
        label="count",
        color=color,
        linewidth=2.5,
        linestyle="-",
        alpha=0.8,
    )
    set_ax_settings(ax, title)
    return fig
