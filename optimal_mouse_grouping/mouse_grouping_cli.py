#!/usr/bin/env python3
"""
Command-line interface for the Optimal Mouse Grouping program.
The program groups lab mice so that the average tumor sizes across the groups are as close as possible.
"""

import argparse

from .mouse_grouping_core import MouseGroupingConfig, find_optimal_mouse_grouping


########################################################################################################################


def main() -> None:
    """
    Entrypoint of the Optimal Mouse Grouping command-line interface (CLI).
    Loads a configuration from the CLI and runs the Optimal Mouse Grouping program using it.
    """
    # Obtain configuration via CLI
    cfg = obtain_mouse_grouping_configuration_from_cli()
    # Find the optimal mouse grouping using mathematical optimization
    find_optimal_mouse_grouping(cfg)


########################################################################################################################


def obtain_mouse_grouping_configuration_from_cli() -> MouseGroupingConfig:
    """
    Load a configuration for the Optimal Mouse Grouping program from the command-line interface.
    :return: A mouse grouping configuration.
    """
    parser = argparse.ArgumentParser(
        description="OPTIMAL MOUSE GROUPING",
        epilog="MIT licensed. Copyright \N{COPYRIGHT SIGN} 2021 Johan Musaeus Bruun."
    )
    
    i_help = "Input Excel file path. Example: \"./data/example_input.xlsx\""
    parser.add_argument("-i", "--input-file", required=True, help=i_help)

    o_help = "Output folder path where all output files will be saved. Example: \"./output\""
    parser.add_argument("-o", "--output-folder", required=True, help=o_help)

    g_help = "Minimum group size, i.e. how many mice must at least be in each group. Defaults to 5."
    parser.add_argument("-g", "--min-group-size", type=int, default=5, help=g_help)

    s_help = "Number of seconds that the optimization should maximally run for. Defaults to 10."
    parser.add_argument("-s", "--max-seconds", type=int, default=10, help=s_help)

    m_help = "Save the mathematical optimization model as a .lp-file. Disabled by default."
    parser.add_argument("-m", "--save-model", action="store_true", help=m_help)

    # Parse arguments
    args = parser.parse_args()

    # Convert to a mouse grouping configuration
    cfg = MouseGroupingConfig(
        input_file_path=args.input_file,
        output_folder_path=args.output_folder
    )
    cfg.min_group_size = args.min_group_size
    cfg.max_seconds = args.max_seconds
    cfg.save_model = args.save_model
    return cfg


########################################################################################################################


if __name__ == "__main__":
    main()
