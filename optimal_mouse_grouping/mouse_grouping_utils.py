"""
Utilities and helper functions for the Optimal Mouse Grouping program.
"""

import os
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


########################################################################################################################


def load_and_verify_mouse_id_and_tumor_size_data_frame(
        excel_file_path: str, orig_id_column_name: str, orig_tumor_size_column_name: str,
        id_column_name: str, tumor_size_column_name: str
) -> pd.DataFrame:
    """
    Load input data from an Excel file. Input data is a list of mice with a Mouse ID and a Tumor Size [mm^3] per mouse.
    :param excel_file_path: Path to the input Excel file (should end with .xlsx).
    :param orig_id_column_name: Name of the ID column in the input Excel file.
    :param orig_tumor_size_column_name:  Name of the Tumor Size column in the input Excel file.
    :param id_column_name: Name of the ID column that will be used throughout the analysis.
    :param tumor_size_column_name: Name of the Tumor Size column that will be used throughout the analysis.
    :return: A data frame of the input Excel file contents, specifically the mouse IDs and the tumor sizes.
    """
    # Verify Excel file existence
    if not os.path.isfile(excel_file_path):
        excel_full_file_path = Path(excel_file_path).resolve()
        raise FileNotFoundError(f"Excel file not found: \"{excel_file_path}\". Full path: \"{excel_full_file_path}\"")

    # Load data frame via pandas
    df: pd.DataFrame = pd.read_excel(excel_file_path)

    # Verify column names
    if orig_id_column_name not in df.columns.to_list():
        raise ValueError(f"Column \"{orig_id_column_name}\" not found in input Excel file. Please fix.")
    if orig_tumor_size_column_name not in df.columns.to_list():
        raise ValueError(f"Column \"{orig_tumor_size_column_name}\" not found in input Excel file. Please fix.")
    if orig_id_column_name == orig_tumor_size_column_name:
        raise ValueError(f"ID and Tumor Size column names cannot be the same: \"{orig_id_column_name}\". Please fix.")

    # Check that all IDs are unique
    if len(df[orig_tumor_size_column_name].unique()) != len(df[orig_tumor_size_column_name]):
        raise ValueError("Not all Mouse IDs in the input Excel file are unique! Please fix.")

    # Check that there are no missing values
    if df[orig_id_column_name].isna().sum() != 0:
        raise ValueError(f"Column \"{orig_id_column_name}\" contains missing values. Please fix.")
    if df[orig_tumor_size_column_name].isna().sum() != 0:
        raise ValueError(f"Column \"{orig_tumor_size_column_name}\" contains missing values. Please fix.")

    # Check that all tumor sizes are non-negative
    if not (df[orig_tumor_size_column_name] >= 0).all():
        raise ValueError("All tumor sizes must be non-negative. Please fix.")

    # Rename columns
    df = df.rename(columns={
        orig_id_column_name: id_column_name,
        orig_tumor_size_column_name: tumor_size_column_name
    })
    return df


########################################################################################################################


def compute_group_sizes(num_mice: int, min_group_size: int) -> np.ndarray:
    """
    Given the number of mice, compute all the group sizes so that there is a minimum of `min_group_size` in each group.
    One or more groups might contain one or more mice more than the minimum number.

    Example 1: 44 mice and a minimum group size of 5 result in four groups of 6 and four groups of 5.
    Example 2: 14 mice and a minimum group size of 5 result in two groups of 7.

    :param num_mice: The total number of mice to divide into groups.
    :param min_group_size: The minimum size of the groups that the mice should be divided into.
    :return: Array of group sizes, one group size (integer) per group.
    """
    num_groups, num_remainders = np.divmod(num_mice, min_group_size)
    group_sizes: np.ndarray = np.repeat(min_group_size, repeats=num_groups)
    # Divide initial remainders onto the groups
    num_remainders_per_group = int(np.floor(num_remainders / num_groups))
    # Add these to the groups
    group_sizes += num_remainders_per_group
    # Compute final remainders
    num_final_remainders = num_remainders - num_groups * num_remainders_per_group
    assert num_final_remainders == num_mice - group_sizes.sum()
    assert num_final_remainders < num_groups
    # Add the final remainders to some of the groups
    group_sizes[:num_final_remainders] += 1
    # Verify and return the computed group sizes
    assert group_sizes.sum() == num_mice
    assert np.all(group_sizes >= min_group_size)
    return group_sizes


def compute_group_means(df: pd.DataFrame, value_colname: str, group_colname: str) -> pd.Series:
    """
    Compute the mean of one column, grouped by another column.
    Used here to compute the mean tumor size across generated mouse groups.
    :param df: Input data frame of IDs and Tumor Sizes (read from the input Excel file).
    :param value_colname: Name of the column that contains the values to group.
    :param group_colname: Name of the column that contains the grouping variable.
    :return: The computed group means, e.g. the tumor size means per mouse group.
    """
    group_means: pd.Series = df.groupby(group_colname)[value_colname].mean()
    return group_means


########################################################################################################################


def print_group_sizes(group_sizes: np.ndarray) -> None:
    """
    Print the group sizes with one group per line plus a total at the end.
    :param group_sizes: Array of group sizes, one group size (integer) per group.
    """
    num_in_total: int = int(np.sum(group_sizes))
    print("Group sizes:")
    for group_id, num_in_group in enumerate(group_sizes, start=1):
        print(f"- Group {group_id}: {num_in_group} mice")
    print(f"- ({num_in_total} mice in total)\n")


def construct_mouse_groups_data_frame(
        df: pd.DataFrame, id_column_name: str, tumor_size_column_name: str, group_column_name: str
) -> pd.DataFrame:
    """
    Construct a data frame that summarized the mouse groups, including the mean tumor size for each group etc.
    :param df: Input data frame of IDs and Tumor Sizes (read from the input Excel file).
    :param id_column_name: Name of the ID column.
    :param tumor_size_column_name: Name of the Tumor Size column.
    :param group_column_name: Name of the Group column.
    :return: A data frame summarizing the mouse groups.
    """
    group_means: pd.Series = compute_group_means(df, tumor_size_column_name, group_column_name)
    overall_tumor_size_mean: np.float64 = df[tumor_size_column_name].mean()
    groups_diffs: np.ndarray = group_means.values - overall_tumor_size_mean
    mouse_ids_in_group: pd.Series = df.groupby(group_column_name)[id_column_name].unique()
    # https://stackoverflow.com/a/45307119
    num_mice_in_group: List[int] = [len(lst) for lst in mouse_ids_in_group]
    mouse_ids_in_group_str: List[str] = [", ".join(map(str, lst)) for lst in mouse_ids_in_group]
    group: List[int] = list(df.groupby(group_column_name).indices.keys())
    df_dict = {
        "group": group,
        "num_mice_in_group": num_mice_in_group,
        "mouse_ids_in_group": mouse_ids_in_group_str,
        "tumor_size_mean": group_means,
        "overall_mean_diff": groups_diffs,
    }
    df_groups = pd.DataFrame(df_dict)
    return df_groups


########################################################################################################################


def save_mouse_grouping_as_xlsx(df_sorted: pd.DataFrame, df_groups: pd.DataFrame, xlsx_file_path: str) -> None:
    """
    Create an Excel document of the mouse grouping results.
    It contains two sheets:
    - Sheet 1: "mouse_grouping" - A list of mice with information about each (Group, Mouse ID, Tumor Size).
    - Sheet 2: "group_statistics" - A list of mouse groups with information, see construct_mouse_groups_data_frame().
    :param df_sorted: A data frame containing the list of mice with information about each.
    :param df_groups: A data frame containing the list of mouse groups with information.
    :param xlsx_file_path: File path to write the XLSX file to.
    """
    data_frames_by_sheet_name = {
        "mouse_grouping": df_sorted,
        "group_statistics": df_groups,
    }
    column_formats_by_sheet_name = get_column_formats_by_sheet_name()

    # Create Excel file and format cells
    with pd.ExcelWriter(xlsx_file_path, engine="xlsxwriter") as writer:  # type: ignore  # pylint: disable=E0110
        for sheet_name, df in data_frames_by_sheet_name.items():
            # Write data frame as sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            # Define header formatting
            _modify_header_row_format(df, writer, sheet_name)
            # Define column formats
            _modify_column_number_formats(df, writer, sheet_name, column_formats_by_sheet_name[sheet_name])
            # Autoadjust column widths
            _adjust_column_width(df, writer, sheet_name)

    print(f"Mouse grouping results saved to \"{xlsx_file_path}\".")


########################################################################################################################


def get_column_formats_by_sheet_name() -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Get the Excel cell formats for each column in each of the sheets in the output XLSX file.
    :return: Nested dictionary of Excel cell formats.
    """
    # Cell formats
    format_str: Dict[str, str] = {}
    format_int: Dict[str, str] = {"num_format": "#0"}
    format_float2: Dict[str, str] = {"num_format": "#,##0.00"}
    format_float4: Dict[str, str] = {"num_format": "#,####0.0000"}

    # Column formats by sheet name
    column_formats_by_sheet_name = {
        "mouse_grouping": {
            "group": format_int,
            "mouse_id": format_int,
            "tumor_size": format_float2,
        },
        "group_statistics": {
            "group": format_int,
            "num_mice_in_group": format_int,
            "mouse_ids_in_group": format_str,
            "tumor_size_mean": format_float2,
            "overall_mean_diff": format_float4,
        },
    }
    return column_formats_by_sheet_name


########################################################################################################################


def _modify_header_row_format(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str) -> None:
    """
    Format the header row (light blue background color, 1 px border).
    :param df: Data frame that the sheet was created from.
    :param writer: The active ExcelWriter object that was just used to create the sheet from the data frame.
    :param sheet_name: Name of the sheet that will be modified.
    """
    # Colored header row
    header_fmt = writer.book.add_format({"bg_color": "#DDEEFF", "border": 1})
    header_fmt.set_align("center")
    header_fmt.set_align("vcenter")
    header_fmt.set_bold()
    for col_name in df:
        col_idx = df.columns.get_loc(col_name)
        writer.sheets[sheet_name].write_string(0, col_idx, col_name, cell_format=header_fmt)


def _adjust_column_width(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str, extra_width: int = 2) -> None:
    """
    Automatically adjust the width of the columns in an Excel sheet.
    Inspired by https://stackoverflow.com/a/61617835
    :param df: Data frame that the sheet was created from.
    :param writer: The active ExcelWriter object that was just used to create the sheet from the data frame.
    :param sheet_name: Name of the sheet that will be modified.
    """
    for col_name in df:
        if pd.api.types.is_float_dtype(df[col_name]):
            longest_value = df[col_name].map('${:,.2f}'.format).astype(str).map(len).max()
        else:
            longest_value = df[col_name].astype(str).map(len).max()
        column_length = max(longest_value, len(col_name)) + extra_width
        col_idx = df.columns.get_loc(col_name)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, width=column_length)


def _modify_column_number_formats(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str,
                                  column_formats_by_colum_name: Dict[str, Dict[str, str]]) -> None:
    """
    Modify the number formats of selected columns in an Excel sheet.
    :param df: Data frame that the sheet was created from.
    :param writer: The active ExcelWriter object that was just used to create the sheet from the data frame.
    :param sheet_name: Name of the sheet that will be modified.
    :param column_formats_by_colum_name: Dictionary of column formats (dicts like {"num_format": "#0"}) by column names.
    """
    # Formats need to be added to the workbook before use
    workbook = writer.book
    for col_name, col_format in column_formats_by_colum_name.items():
        # Add formats to workbook before use
        fmt = workbook.add_format(col_format)
        # Set text alignment, see https://xlsxwriter.readthedocs.io/format.html#set_align
        fmt.set_align("center")
        fmt.set_align("vcenter")
        # Set column format
        col_idx = df.columns.get_loc(col_name)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, cell_format=fmt)


########################################################################################################################


def move_column_inplace(df: pd.DataFrame, col_name: str, pos: int) -> None:
    """
    Move a data frame column in-place, i.e. modifying the given data frame.
    :param df: A data frame.
    :param col_name: The name of the column to move.
    :param pos: The desired position of the column, e.g. 0 to move it to the front.
    """
    # https://stackoverflow.com/a/58686641
    column: pd.Series = df.pop(col_name)  # type: ignore
    df.insert(pos, column.name, column)


########################################################################################################################


def plot_mouse_groups(
        df: pd.DataFrame, tumor_size_column_name: str, group_column_name: str, plot_file_path: str
) -> None:
    """
    Plot the resulting mouse groups as a violin plot with a swarm plot on top. The plot will be saved as a PNG-file.
    :param df: A data frame of mice with information about each (Group, Mouse ID, Tumor Size).
    :param tumor_size_column_name: Name of the Tumor Size column.
    :param group_column_name: Name of the Group column.
    :param plot_file_path: File path to write the PNG to.
    """
    # Use default seaborn theme for plots
    sns.set_theme()

    # Define height and aspect ratio of plots
    h, a = 7, 1.6

    title = "Optimal Mouse Grouping\n(optimized for equal tumor size average across groups)"

    group_means = compute_group_means(df, tumor_size_column_name, group_column_name)
    group_means_df = pd.DataFrame(group_means)
    group_means_df.reset_index(level=0, inplace=True)

    g = sns.catplot(x=group_column_name, y=tumor_size_column_name, kind="violin", inner=None, bw=0.3, data=df,
                    height=h, aspect=a)
    sns.swarmplot(x=group_column_name, y=tumor_size_column_name, color="k", size=7, data=df, ax=g.ax)
    g.ax.set_title(title, weight="bold")
    g.ax.set_xlabel(group_column_name.capitalize(), weight="bold")
    g.ax.set_ylabel("Tumor Size [mm\u00b3]", weight="bold")

    # Add group means as markers
    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
    g.ax.plot(group_means_df[tumor_size_column_name], "o", ms=12, mew=2, mec="w", mfc="r")

    # Set tight layout with a little extra padding
    # https://stackoverflow.com/a/14307273/1447415
    g.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)

    # Save as PNG
    if not plot_file_path.lower().endswith(".png"):
        raise ValueError("Plot file path must end with \".png\".")

    g.savefig(plot_file_path)
    print(f"Mouse grouping plot saved to \"{plot_file_path}\".")

    # Close figure
    plt.close(g.fig)


########################################################################################################################
