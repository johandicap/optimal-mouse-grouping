"""
Core functionality of the Optimal Mouse Grouping program.
"""

import os
from dataclasses import dataclass

from tabulate import tabulate

from .mouse_grouping_mip import construct_and_solve_mouse_grouping_model
from .mouse_grouping_utils import compute_group_sizes, construct_mouse_groups_data_frame
from .mouse_grouping_utils import load_and_verify_mouse_id_and_tumor_size_data_frame, move_column_inplace
from .mouse_grouping_utils import plot_mouse_groups, print_group_sizes, save_mouse_grouping_as_xlsx


########################################################################################################################


@dataclass
class MouseGroupingConfig:  # pylint: disable=R0902
    """
    Data class containing a configuration for the Optimal Mouse Grouping program.
    """
    input_file_path: str
    output_folder_path: str

    min_group_size: int = 5
    max_seconds: int = 10
    print_model_stats: bool = False
    save_model: bool = False

    # Default file names
    xlsx_file_name: str = "mouse_grouping.xlsx"
    plot_file_name: str = "mouse_grouping.png"
    model_file_name: str = "mouse_grouping.lp"

    # Input column names
    orig_id_column_name: str = "Mouse ID"
    orig_tumor_size_column_name: str = "Tumor size"

    # Output column names
    id_column_name: str = "mouse_id"
    tumor_size_column_name: str = "tumor_size"
    group_column_name: str = "group"


########################################################################################################################


def print_mouse_grouping_config(cfg: MouseGroupingConfig, show_full: bool = False) -> None:
    """
    Print a given Optimal Mouse Grouping configuration.
    :param cfg: The mouse grouping configuration.
    :param show_full: Print all of the configuration rather than just the essentials.
    """
    print("Configuration:")
    print(f"- Input file path:     {cfg.input_file_path}")
    print(f"- Output folder path:  {cfg.output_folder_path}")
    print(f"- Mimimum group size:  {cfg.min_group_size}")
    print(f"- Maximum seconds:     {cfg.max_seconds}")
    print(f"- Save model to file:  {cfg.save_model}")
    print("")

    if not show_full:
        return

    print(f"- Print model stats:   {cfg.print_model_stats}")
    print(f"- XLSX file name:      {cfg.xlsx_file_name}")
    print(f"- Plot file name:      {cfg.plot_file_name}")
    print(f"- Model file name:     {cfg.model_file_name}")
    print("")
    print(f"- Orig id column name:         {cfg.orig_id_column_name}")
    print(f"- Orig tumor size column name: {cfg.orig_tumor_size_column_name}")
    print(f"- Id column name:              {cfg.id_column_name}")
    print(f"- Tumor size column name:      {cfg.tumor_size_column_name}")
    print(f"- Group column name:           {cfg.group_column_name}")
    print("")


########################################################################################################################


def find_optimal_mouse_grouping(cfg: MouseGroupingConfig) -> None:
    """
    Run the Optimal Mouse Grouping program given a mouse grouping configuration.
    Prints a header and the configuration, loads the input data from an Excel-file, solves the mouse grouping
    optimization problem, and saves the results in different formats.
    :param cfg: The mouse grouping configration.
    """
    print("")
    print("##########################")
    print("# Optimal Mouse Grouping #")
    print("##########################")
    print("")

    # Print configuration
    print_mouse_grouping_config(cfg)

    # Load and verify input data
    df = load_and_verify_mouse_id_and_tumor_size_data_frame(
        cfg.input_file_path, cfg.orig_id_column_name, cfg.orig_tumor_size_column_name,
        cfg.id_column_name, cfg.tumor_size_column_name
    )

    # Verify output folder
    if not os.path.isdir(cfg.output_folder_path):
        raise NotADirectoryError(f"Output folder not found: \"{cfg.output_folder_path}\"")

    # Define and print group sizes
    num_mice = df.shape[0]
    group_sizes = compute_group_sizes(num_mice, min_group_size=cfg.min_group_size)
    print_group_sizes(group_sizes)

    # Extract tumor sizes
    tumor_sizes = df[cfg.tumor_size_column_name].values

    # If model should be saved, construct the model save path, otherwise set to None
    model_save_path = os.path.join(cfg.output_folder_path, cfg.model_file_name) if cfg.save_model else None

    # Construct and run optimization model
    mouse_grouping, objective_value, _ = construct_and_solve_mouse_grouping_model(
        tumor_sizes, group_sizes, cfg.max_seconds, print_model_stats=cfg.print_model_stats,
        model_save_path=model_save_path
    )

    print(f"Objective function value: {objective_value:.1f}\n")
    print("The objective value is the sum of absolute deviations from overall tumor size mean.")

    # Add computed grouping to the data frame
    df[cfg.group_column_name] = mouse_grouping
    move_column_inplace(df, cfg.group_column_name, 0)

    # Construct data frames for the output XLSX file
    df_groups = construct_mouse_groups_data_frame(df, cfg.id_column_name, cfg.tumor_size_column_name,
                                                  cfg.group_column_name)
    df_sorted = df.sort_values(by=[cfg.group_column_name, cfg.id_column_name, cfg.tumor_size_column_name])

    # Show resulting groups as a table
    print(tabulate(df_groups, showindex=False, headers="keys", tablefmt="psql"))
    print("")

    # Save constructed data frames to output XLSX file
    xlsx_file_path = os.path.join(cfg.output_folder_path, cfg.xlsx_file_name)
    save_mouse_grouping_as_xlsx(df_sorted, df_groups, xlsx_file_path)

    # Plot results as a PNG file
    plot_file_path = os.path.join(cfg.output_folder_path, cfg.plot_file_name)
    plot_mouse_groups(df, cfg.tumor_size_column_name, cfg.group_column_name, plot_file_path)
    print("\nDone!")


########################################################################################################################
