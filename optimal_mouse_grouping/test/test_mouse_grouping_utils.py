"""

Tests for the mouse grouping utilities.

"""

import os
import tempfile

import numpy as np
import pandas as pd

from optimal_mouse_grouping.mouse_grouping_utils import compute_group_sizes, save_mouse_grouping_as_xlsx


########################################################################################################################


def test_compute_group_sizes_ex1() -> None:
    """
    Example 1: 44 mice and a minimum group size of 5 result in four groups of 6 and four groups of 5.
    """
    #
    # Given
    #
    num_mice = 44
    min_group_size = 5
    expected_group_sizes = np.array([6, 6, 6, 6, 5, 5, 5, 5], dtype=np.int64)

    #
    # When
    #
    group_sizes = compute_group_sizes(num_mice, min_group_size)

    #
    # Then
    #
    np.testing.assert_array_equal(group_sizes, expected_group_sizes)


########################################################################################################################


def test_compute_group_sizes_ex2() -> None:
    """
    Example 2: 14 mice and a minimum group size of 5 result in two groups of 7.
    """
    #
    # Given
    #
    num_mice = 14
    min_group_size = 5
    expected_group_sizes = np.array([7, 7], dtype=np.int64)

    #
    # When
    #
    group_sizes = compute_group_sizes(num_mice, min_group_size)

    #
    # Then
    #
    np.testing.assert_array_equal(group_sizes, expected_group_sizes)


########################################################################################################################


def test_compute_group_sizes_ex3() -> None:
    """
    Example 3: 199 mice and a minimum group size of 50 result in three groups of size [67, 66, 66].
    """
    #
    # Given
    #
    num_mice = 199
    min_group_size = 50
    expected_group_sizes = np.array([67, 66, 66], dtype=np.int64)

    #
    # When
    #
    group_sizes = compute_group_sizes(num_mice, min_group_size)

    #
    # Then
    #
    np.testing.assert_array_equal(group_sizes, expected_group_sizes)


########################################################################################################################


def test_save_mouse_grouping_as_xlsx() -> None:
    """
    Test the writing mouse grouping results to an Excel file, including formatting of cells.
    """
    #
    # Given
    #
    df_sorted = pd.DataFrame(data={
        "group": [1, 1, 2, 2],
        "mouse_id": [9, 11, 39, 41],
        "tumor_size": [20.000615, 36.217478, 20.087039, 130.426312],
    })
    df_groups = pd.DataFrame(data={
        "group": [1, 2, 3],
        "num_mice_in_group": [6, 6, 6],
        "mouse_ids_in_group": ["9, 11, 22, 39, 41, 49", "7, 13, 32, 35, 46, 48", "6, 15, 19, 34, 50, 51"],
        "tumor_size_mean": [40.52, 42.80, 42.89],
        "overall_mean_diff": [-1.7255, 0.5577, 0.6445],
    })

    # Generate temporary file path
    temp_xlsx_file_path = tempfile.NamedTemporaryFile(suffix=".xlsx").name

    #
    # When
    #
    save_mouse_grouping_as_xlsx(df_sorted, df_groups, temp_xlsx_file_path)

    #
    # Then
    #
    assert os.path.isfile(temp_xlsx_file_path)
    os.remove(temp_xlsx_file_path)


########################################################################################################################
