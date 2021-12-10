"""
Functions related to the MIP (Mixed-Integer Linear Program) formulation of the Optimal Mouse Grouping problem.
"""

import os
from typing import List, Optional, Tuple

import mip
import numpy as np


########################################################################################################################


def construct_and_solve_mouse_grouping_model(  # pylint: disable=R0914
        tumor_sizes: np.ndarray,
        group_sizes: np.ndarray,
        max_seconds: int = 60,
        print_model_stats: bool = False,
        model_save_path: Optional[str] = None
) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Construct the mouse grouping optimization model and solve it.

    Note: pylint rule ignored: "R0914: Too many local variables (18/15) (too-many-locals)"

    :param tumor_sizes: Array of tumor sizes, one tumor size (float) per mouse.
    :param group_sizes: Array of group sizes, one group size (integer) per group.
    :param max_seconds: The max number of seconds that the optimization is allowed to run for.
    :param print_model_stats: If basic statistics about the constructed model should be printed.
    :param model_save_path: File path to save the model to.
    :return: The optimized mouse grouping, the objective value, and the group deviations.
    """
    # Verify input
    if max_seconds < 1.0:
        raise AttributeError("The optimization must run for at least one second.")
    if print_model_stats not in [True, False]:
        raise AttributeError("The argument \"print_model_stats\" must be either True or False.")

    # Construct model
    model, x, y_pos, y_neg, all_mice, all_groups = construct_mouse_grouping_model(tumor_sizes, group_sizes)

    # Print model statistics
    if print_model_stats:
        print("Model stats:")
        print(f"- {model.num_cols} columns (variables)")
        print(f"- {model.num_int} integer variables")
        print(f"- {model.num_rows} rows (constraints)")
        print(f"- {model.num_nz} non-zeros in the constraint matrix")
        print("")

    # Save the model to a file (if a valid model_save_path is given)
    if model_save_path is not None and model_save_path != "":
        save_optimization_model_to_file(model, model_save_path)

    # Search for a good solution
    print(f"Running optimization for {max_seconds:.1f} seconds, please wait...\n")
    status = model.optimize(max_seconds=max_seconds)
    print("Optimization done.")

    # Print optimization status
    print(f"Status: {status}")
    # if status == mip.OptimizationStatus.OPTIMAL: ...
    # OPTIMAL(0), ERROR(-1), INFEASIBLE(1), UNBOUNDED(2), FEASIBLE(3), INT_INFEASIBLE(4), NO_SOLUTION_FOUND(5)
    # See https://python-mip.readthedocs.io/en/latest/classes.html

    # Convert solution to numpy array
    x_arr = np.array([[x[i][j].x for j in all_groups] for i in all_mice])

    # Verify solution
    if not np.all(np.isclose(x_arr.sum(axis=1), np.repeat(1, len(all_mice)))):
        raise ValueError("The assignment matrix was invalid (axis=1). Please investigate.")
    if not np.all(np.isclose(x_arr.sum(axis=0), group_sizes)):
        raise ValueError("The assignment matrix was invalid (axis=0). Please investigate.")

    # Extract grouping from solution
    mouse_grouping = np.where(x_arr)[1]
    # Make sure the first group is group 1 rather than group 0
    mouse_grouping += 1

    # Compute group deviations (from the overall mean tumor size)
    y_pos_arr = np.array([y_pos[j].x for j in all_groups])
    y_neg_arr = np.array([y_neg[j].x for j in all_groups])
    group_deviations = y_pos_arr - y_neg_arr

    # Extract objective value, i.e. the sum of absolute deviations from overall mean
    objective_value = float(model.objective_value)

    # Verify objective value against group deviations
    if not np.isclose(objective_value, sum(abs(group_deviations))):
        raise ValueError("Objective value and sum of absolute group deviations differ. Please investigate.")

    return mouse_grouping, objective_value, group_deviations


########################################################################################################################


def construct_mouse_grouping_model(
        tumor_sizes: np.ndarray, group_sizes: np.ndarray
) -> Tuple[mip.model.Model, List[List[mip.entities.Var]], List[mip.entities.Var], List[mip.entities.Var], range, range]:
    """
    Construct the mouse grouping optimization model.
    :param tumor_sizes: Array of tumor sizes, one tumor size (float) per mouse.
    :param group_sizes: Array of group sizes, one group size (integer) per group.
    :return: The constructed model and its decision variables and ranges.
    """
    #
    # Verify input
    #
    if not len(tumor_sizes) >= 3 and np.all(np.asarray(tumor_sizes) >= 0):
        raise AttributeError("There must be at least three tumor sizes and they must all be non-negative.")
    if not len(group_sizes) >= 2 and np.all(np.asarray(group_sizes) > 0):
        raise AttributeError("There must be at least two groups and none of them can be empty.")
    if len(tumor_sizes) != sum(group_sizes):
        raise ValueError("Lenght of tumor_sizes list must equal the sum of the number of mice in the groups.")

    #
    # Construct model
    #
    num_mice = len(tumor_sizes)
    num_groups = len(group_sizes)

    all_mice = range(num_mice)
    all_groups = range(num_groups)

    model = mip.Model("mouse_grouping", sense=mip.MINIMIZE, solver_name="CBC")

    # Constants: Group sizes
    g = group_sizes

    # Constants: Tumor size differences (individual differences from overall mean tumor size)
    d = list(np.asarray(tumor_sizes) - np.mean(tumor_sizes))

    # Decision variables x_ij = 1 if mouse i is in group j, 0 otherwise.
    x = [[model.add_var(var_type=mip.BINARY, name=f"x_{i}_{j}") for j in all_groups] for i in all_mice]

    # Proxy variables (non-negative) y_pos_j and y_neg_j
    # These are used in to objective function to minimize the absolute value of deviations from the overall mean.
    y_pos = [model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f"y_pos_{j}") for j in all_groups]
    y_neg = [model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f"y_neg_{j}") for j in all_groups]

    # Constraints: The must be a specific number of mice in each of the groups.
    for j in all_groups:
        model += mip.xsum(x[i][j] for i in all_mice) == g[j], f"Mice_in_group_{j}"

    # Constraints: Each mouse can only be assigned to one group.
    for i in all_mice:
        model += mip.xsum(x[i][j] for j in all_groups) == 1, f"Mouse_{i}_in_one_group"

    # Each group's mean deviation (from the overall mean) is set to the difference between the group's proxy variables.
    # Since they are both non-negative (and their sum is sought minimized), only one of them will differ from zero.
    for j in all_groups:
        model += mip.xsum(d[i] * x[i][j] for i in all_mice) == y_pos[j] - y_neg[j], f"Mean_tumor_diff_in_group_{j}"

    # Objective function: Minimize the sum of the proxy variables across groups, i.e. deviations from overall mean.
    model.objective = mip.minimize(mip.xsum(y_pos[j] + y_neg[j] for j in all_groups))

    return model, x, y_pos, y_neg, all_mice, all_groups


########################################################################################################################


def save_optimization_model_to_file(model: mip.model.Model, model_save_path: str) -> None:
    """
    Save the MIP optimization model to a file, either a .lp or a .mps file.
    :param model: The optimization model
    :param model_save_path: The file path to save the model to, ending with .lp or .mps.
    """
    # Verify that the model path ends with ".lp" or ".mps"
    if not (model_save_path.endswith(".lp") or model_save_path.endswith(".mps")):
        raise ValueError("Model save path must end with \".lp\" or \".mps\" to save the model to a file.")

    # Verify that the model save folder exists
    model_save_folder = os.path.split(model_save_path)[0]
    if not os.path.isdir(model_save_folder):
        raise ValueError(f"Invalid model save folder: \"{model_save_folder}\"")

    # Save model
    model.write(model_save_path)
    print(f"Model successfully written to file: \"{model_save_path}\"\n")


########################################################################################################################
