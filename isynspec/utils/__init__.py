"""Utility modules for the isynspec package."""

from pathlib import Path


def deep_update(src: dict, dest: dict) -> None:
    """Recursively update `dest` dictionary with values from `src`.

    This function updates the `dest` dictionary in place, merging
    nested dictionaries and replacing values as necessary.

    Args:
        src (dict): Source dictionary with new values.
        dest (dict): Destination dictionary to be updated.
    """
    for key, value in src.items():
        if key not in dest:
            raise KeyError(f"Key '{key}' not found in destination dictionary.")
        if isinstance(value, dict) and key in dest and isinstance(dest[key], dict):
            deep_update(value, dest[key])
        else:
            dest[key] = value


def convert_dict_value_to_path(dict: dict, key: str) -> None:
    """Convert a dictionary value to a Path object if it exists.

    Args:
        dict (dict): The dictionary to update.
        key (str): The key whose value should be converted to Path.
    """
    if key in dict and isinstance(dict[key], str):
        dict[key] = Path(dict[key])
    elif (
        key in dict
        and isinstance(dict[key], list)
        and all(isinstance(item, str) for item in dict[key])
    ):
        dict[key] = [Path(item) for item in dict[key]]
