import xarray as xr
import pathlib
import numpy as np
import pandas as pd
import os
import shutil
from datetime import datetime


def generate_combined_sequence(
    quintile_sequence: pd.DataFrame,
    quintile_to_year_map: dict[int, int],
    source_folder: str,  # Path where HEC-RAS .tif files are stored
    output_folder: str,  # Path to store the combined 25-year sequence
):
    """
    Generate a 25-year sequence of HEC-RAS .tif files based on quintile assignments. Currently
    requires raster input to be MONTHLY timeseries.

    Parameters
    ----------
    quintile_sequence : pd.DataFrame
        The 25-year sequence of quintiles.
    quintile_to_year_map : dict[int, int])
        Maps quintiles to available years (e.g., {1: 2006, 2: 2023}).
    source_folder : str
        Path where HEC-RAS .tif files are stored.
    output_folder : str
        Path to store the combined 25-year sequence.

    Returns
    --------
    Saves WSE data with new filenames to simulate 25 year model output from analog years.
    """
    os.makedirs(output_folder, exist_ok=True)
    path = pathlib.Path(source_folder)

    source_files = [
        file for file in list(path.rglob("*.tif")) if "SLR" not in str(file)
    ]

    if not source_files:
        raise FileNotFoundError(f"No .tif files found for year in {source_folder}")

    # Loop through the 25-year quintile sequence
    for _, i in quintile_sequence.iterrows():
        analog_year = int(i["Water Year"])
        source_year = quintile_to_year_map[i.Quintile]
        start = datetime(source_year - 1, 10, 1)
        end = datetime(source_year, 9, 30)

        source_year_paths = [
            path for path in source_files if start <= extract_date(path) <= end
        ]
        source_year_paths.sort()

        print(f"Mapping {source_year} to {analog_year}")

        if len(source_year_paths) < 12:
            raise ValueError(f"Missing data in source files for {source_year}.")

        for p in source_year_paths:
            print(f"input path: {p}")
            # for each monthly file, copy and rename to analog year
            file_date = extract_date(p)
            # October 1 is the start of the water year
            if file_date.month in [10, 11, 12]:
                replacement_year = str(int(analog_year) - 1)
            else:  # Before October, it's the previous water year
                replacement_year = analog_year

            # Reconstruct the string with the new water year (with zero padding)
            new_file_name = f"WSE_MEAN_{replacement_year}_{file_date.month:02d}_{file_date.day:02d}.tif"
            print(f"output name: {new_file_name}")

            dest_file = os.path.join(output_folder, new_file_name)
            shutil.copy(p, dest_file)

        print("All months completed.")

    print(f"Generated 25-year sequence in {output_folder}")
    print("WARN: only files NAMES were modified, original timestamps still in place.")


def extract_date(path: pathlib.Path):
    """
    Extract date from HEC-RAS filepaths, or any filepath with dates in a YYYY_MM_DD format.
    Must use pathlib object not str.

    Parameters
    ----------
    path : pathlib.Path
        Path to the file with a date embedded in its name in the format YYYY_MM_DD.

    Returns
    -------
    datetime or None
        The extracted date as a datetime object, or None if no valid date is found.
    """
    try:
        # Assuming the date is located just before the file extension in YYYY_MM_DD format
        date_str = path.stem.split("_")[-3:]  # Extract the last three
        date_str = "_".join(date_str)  # Combine back into "YYYY_MM_DD"
        return datetime.strptime(date_str, "%Y_%m_%d")
    except (ValueError, IndexError):
        return None


def create_dataset_from_template(
    template: xr.Dataset, new_variables: dict[np.ndarray, str]
):
    """
    Create an xarray.Dataset based on a template dataset.

    Parameters
    ----------
    template : xr.Dataset
        The template dataset containing dimensions, coordinates, and optional global attributes.
    new_variables : dict
        Dictionary defining new variables. Keys are variable names, and values are tuples (data, attrs).
        - `data`: NumPy array of the same shape as the template's data variables.
        - `attrs`: Metadata for the variable.

    Returns
    -------
    xr.Dataset
        A new dataset based on the template, containing the new variables and copied template attributes.
    """
    coords = {name: template.coords[name] for name in template.coords}
    new_ds = xr.Dataset(coords=coords)

    for var_name, (data, attrs) in new_variables.items():
        # Check that the shape matches the template
        if data.shape != template["WSE_MEAN"].shape:
            raise ValueError(
                f"Shape of variable '{var_name}' ({data.shape}) does not match "
                f"the template shape ({template['WSE_MEAN'].shape})."
            )
        # Add the variable
        new_ds[var_name] = xr.DataArray(
            data, dims=template["WSE_MEAN"].dims, attrs=attrs
        )

    # Optionally, copy global attributes from the template
    new_ds.attrs = template.attrs

    return new_ds
