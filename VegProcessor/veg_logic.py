import numpy as np
import xarray as xr
import datetime

import plotting


def zone_v(
    logger,
    veg_type: np.ndarray,
    water_depth: xr.Dataset,
    date: datetime.date,
    plot: bool = False,
) -> np.ndarray:
    """Calculate transition for Zone V

    MAR, APRIL, MAY, or JUNE
    inundation depth <= 0, AND
    GS inundation >20%

    Zone V = 15

    Params:
        - veg_type (np.ndarray): array of current vegetation types.
        - water_depth (xr.Dataset): Dataset of 1 year of inundation depth from hydrologic model,
            created from water surface elevation and the domain DEM.
        - date (datetime.date): Date to derive year for filtering.
        - plot (bool): If True, plots the array before and after transformation.

    Returns:
        - np.ndarray: Modified vegetation type array with updated transitions.
    """
    veg_type_input = veg_type.copy()
    growing_season = {"start": f"{date.year}-04", "end": f"{date.year}-09"}

    # Subset for veg type Zone V (value 15)
    type_mask = veg_type == 15

    # Condition 1: MAR, APR, MAY inundation depth <= 0
    filtered_1 = water_depth.sel(time=slice(f"{date.year}-03", f"{date.year}-05"))
    condition_1 = (filtered_1["WSE_MEAN"] <= 0).any(dim="time")

    # Condition 2: Growing Season (GS) inundation > 20%
    filtered_2 = water_depth.sel(
        time=slice(growing_season["start"], growing_season["end"])
    )
    # Note: this assumes time is serially complete
    condition_2_pct = (filtered_2["WSE_MEAN"] > 0).mean(dim="time")
    condition_2 = condition_2_pct > 0.2

    # Combined transition condition
    transition_mask = np.logical_and(condition_1, condition_2)
    combined_mask = np.logical_and(type_mask, transition_mask)

    # Apply transitions
    veg_type[combined_mask] = 16

    # Deferred Plotting
    if plot:
        plotting.np_arr(veg_type_input, "Input - Zone V")
        plotting.np_arr(
            np.where(type_mask, veg_type, np.nan),
            "Veg Type Mask (Zone V)",
        )
        plotting.np_arr(
            np.where(condition_1, veg_type, np.nan),
            "Condition 1 (Inundation Depth <= 0)",
        )
        plotting.np_arr(
            np.where(condition_2, veg_type, np.nan),
            "Condition 2 (GS Inundation > 20%)",
        )
        plotting.np_arr(
            np.where(combined_mask, veg_type, np.nan),
            "Combined Mask (All Conditions Met)",
        )
        plotting.np_arr(
            veg_type,
            "Output - Updated Veg Types",
        )

    logger.info("Finished Zone V transitions.")
    return veg_type


def zone_iv(arg1, arg2, arg3) -> np.ndarray:
    """ """
    return NotImplementedError


def zone_iii(arg1, arg2, arg3) -> np.ndarray:
    """ """
    return NotImplementedError
