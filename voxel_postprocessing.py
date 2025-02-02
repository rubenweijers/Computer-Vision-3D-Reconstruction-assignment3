import pickle

import numpy as np
from tqdm import tqdm
from tqdm.contrib import tzip

from assignment import block_size
from data_processing import load_pickle


def intersect_voxels(frame_voxels, pixel_values, stepsize: int, colourise: bool = False):
    """Intersect the voxels from all cameras and return the intersection.

    Optionally colourise the voxels based on the pixel values or randomise the colours.
    """
    all_voxels = []
    all_colours = []
    for camera_number, camera_voxels in enumerate(frame_voxels):
        camera_voxels = np.array(camera_voxels)
        camera_voxels = camera_voxels[:, [0, 2, 1]]  # Swap the y and z axis
        camera_voxels[:, 1] = -camera_voxels[:, 1]  # Rotate y axis by 90 degrees
        camera_voxels = camera_voxels * block_size / stepsize  # Scale the voxel by step size
        camera_voxels = camera_voxels.round(0).astype(int)  # Round to nearest integer instead of floor
        camera_voxels = list(map(tuple, camera_voxels))  # Convert to list of tuples, in an efficient way

        voxel_colours = np.array(pixel_values[camera_number]) / 255  # Scale the pixel value to 0-1
        voxel_colours = voxel_colours[:, [2, 1, 0]]  # BGR to RGB
        voxel_colours = list(map(tuple, voxel_colours))  # Convert to list of tuples, in an efficient way

        all_voxels.append(camera_voxels)
        all_colours.append(voxel_colours)

    # Get the intersection of all voxels
    voxels_filtered = list(set.intersection(*map(set, all_voxels)))

    if colourise:
        # Get the colours of the intersection
        colours_filtered = []
        for voxel_n, voxel in enumerate(tqdm(voxels_filtered, desc="Getting intersection colours")):  # For each voxel
            for camera_n, camera in enumerate(all_voxels):  # For each camera
                if voxels_filtered[voxel_n] in camera:  # If the voxel is in the camera
                    colours_filtered.append(all_colours[camera_n][camera.index(voxel)])  # Get the colour of the voxel
                    break  # TODO: get average of colours instead of the first one found
    else:
        colours_filtered = np.random.rand(len(voxels_filtered), 3).tolist()

    return voxels_filtered, colours_filtered


if __name__ == "__main__":
    # Load the voxel data from pickle
    data_pickle = load_pickle("./data/voxels.pickle")

    all_voxels = data_pickle["voxels"]
    all_pixel_values = data_pickle["pixel_values"]

    bounds = data_pickle["bounds"]
    stepsize = bounds["stepsize"]

    colourise = True  # Either use true colours or use random colours for the voxels

    voxels_postprocessed = []
    colours_postprocessed = []
    for voxels_frame, pixel_values_frame in tzip(all_voxels, all_pixel_values, desc="Postprocessing frames"):
        voxels, colours = intersect_voxels(voxels_frame, pixel_values_frame, stepsize, colourise=colourise)  # False is faster for debugging

        voxels_postprocessed.append(voxels)
        colours_postprocessed.append(colours)

    # Save the intersection to a pickle
    with open("./data/voxels_intersection.pickle", "wb") as f:
        pickle.dump({"voxels": voxels_postprocessed, "colours": colours_postprocessed, "bounds": bounds}, f)
