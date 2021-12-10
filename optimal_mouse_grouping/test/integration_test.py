#!/usr/bin/env python3
"""

Run the Optimal Mouse Grouping program via Python instead of via the CLI.

"""

import tempfile
from pathlib import Path

import pandas as pd

from optimal_mouse_grouping.mouse_grouping_core import MouseGroupingConfig, find_optimal_mouse_grouping
from optimal_mouse_grouping.mouse_grouping_utils import get_column_formats_by_sheet_name


########################################################################################################################


def test_find_optimal_mouse_grouping(input_file_path: str = "input/example_input.xlsx") -> None:
    """
    Run the optimal mouse grouping program via Python and verify that the expected outputs are created.
    :param input_file_path: Path to the example input file. Depends on where the test is executed from.
    """
    #
    # Given
    #
    # Create temporary output folder that will be deleted after the test
    with tempfile.TemporaryDirectory(prefix="optimal_mouse_grouping") as temp_folder_path:
        print(f"Using temporary folder: \"{temp_folder_path}\"")
        
        # Create a configuration to run
        cfg = MouseGroupingConfig(
            input_file_path=input_file_path,
            output_folder_path=temp_folder_path
        )
    
        # Settings
        cfg.min_group_size = 5
        cfg.max_seconds = 3
        cfg.print_model_stats = True
        cfg.save_model = True
    
        # Input column names
        cfg.orig_id_column_name = "Mouse ID"
        cfg.orig_tumor_size_column_name = "Tumor size"
    
        # Output column names
        cfg.id_column_name = "mouse_id"
        cfg.tumor_size_column_name = "tumor_size"
        cfg.group_column_name = "group"
    
        # Default file names
        cfg.xlsx_file_name = "mouse_grouping.xlsx"
        cfg.plot_file_name = "mouse_grouping.png"
        cfg.model_file_name = "mouse_grouping.lp"
        
        #
        # When
        #
        find_optimal_mouse_grouping(cfg)
    
        #
        # Then
        #
        xlsx_file_path = Path(temp_folder_path) / cfg.xlsx_file_name
        plot_file_path = Path(temp_folder_path) / cfg.plot_file_name
        model_file_path = Path(temp_folder_path) / cfg.model_file_name
        
        # Verify output file existence
        assert xlsx_file_path.is_file(), "Expected XLSX output file not found."
        assert plot_file_path.is_file(), "Expected output plot not found."
        assert model_file_path.is_file(), "Expected model output file not found."
        
        # Verify the LP model file contents
        _verify_lp_model_file_contents(model_file_path)

        # Verify the output XLSX file contents
        _verify_output_xlsx_file_contents(xlsx_file_path)
        
        print("Integration test done.")


########################################################################################################################


def _verify_lp_model_file_contents(model_file_path: Path) -> None:
    """
    Verify the contents of the generated LP model file that contains the mathematical optimization model.
    :param model_file_path: Path to the LP model file.
    """
    with open(model_file_path, "r") as fp:
        first_line = fp.readline()
        remaining_text = fp.read()
    assert "Problem name: " in first_line, "LP model file contents is expected to start with a problem name."
    assert remaining_text.strip(" \n").endswith("End"), "LP model file contents is expected to end with 'End'."


def _verify_output_xlsx_file_contents(xlsx_file_path: Path) -> None:
    """
    Verify the contents of the generated output XLSX file that contains the computed mouse grouping and some statistics.
    :param xlsx_file_path: Path to the output XLSX file.
    """
    # Obtain expected sheet and column names
    column_formats_by_sheet_name = get_column_formats_by_sheet_name()
    
    # Verify that the expected sheets and column names are present in the generated XLSX output file
    for sheet_name, column_formats_dict in column_formats_by_sheet_name.items():
        # Read current sheet into a data frame
        df: pd.DataFrame = pd.read_excel(xlsx_file_path, sheet_name=sheet_name)
        expected_column_names = df.columns.to_list()
        for column_name in column_formats_dict.keys():
            if column_name not in expected_column_names:
                err_msg = f"Column \"{column_name}\" not found in sheet \"{sheet_name}\" of generated output XLSX file."
                raise ValueError(err_msg)


########################################################################################################################


# test_find_optimal_mouse_grouping(input_file_path="../input/example_input.xlsx")
