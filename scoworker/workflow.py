"""Implements the run SCO model workflow for a given user request."""

from abc import abstractmethod
import os
import shutil
import tarfile
import tempfile

import sco


def sco_run(model_run, subject, image_group, output_dir):
    """Core method to run SCO predictive model. Expects resource handles for
    model run, subject, and image group. Creates results as tar file in given
    output directory.

    Parameters
    ----------
    model_run : Model Run handle
        Handle for model run resource (either scocli.scoserv.ModelRunHandle or
        scodata.prediction.ModelRunHandle)
    subject : Subject handle
        Handle for subject resource (either scocli.scoserv.SubjectHandle or
        scodata.subject.SubjectHandle)
    image_group : Image group handle
        Handle for image group resource (either scocli.scoserv.ImageGroupHandle
        or scodata.image.ImageGroupHandle)
    output_dir : string
        Path to output directory

    Returns
    -------
    string
        Path to generated tar file
    """
    # Compose run arguments from image group options and model run arguments.
    opts = {}
    # Add image group options
    for attr in image_group.options:
        opts[attr] = image_group.options[attr].value
    # Add run options
    for attr in model_run.arguments:
        opts[attr] = model_run.arguments[attr].value
    # Get subject directory
    subject_dir = subject.data_directory
    # Create list of image files
    image_files = [img.filename for img in image_group.images]
    # Run model. Exceptions are not caught here to allow callers to adjust run
    # run states according to their respective implementations (i.e., remote or
    # local worker will use different methods to change run state).
    results = sco.calc_sco(
        opts,
        subject=subject_dir,
        stimulus_image_filenames=image_files
    )
    # Create tar file with results. The file will have an images listing called
    # images.txt and a predicted response file called prediction.mgz
    sco.export_predicted_response_volumes(results, export_path=output_dir)
    # Overwrite the generated images file with folders and names of images
    # in image group
    with open(os.path.join(output_dir, 'images.txt'), 'w') as f:
        for img in image_group.images:
            f.write(img.folder + img.name + '\n')
    # Create a tar file in the temp directory
    tar_file = os.path.join(output_dir, 'results.tar.gz')
    with tarfile.open(tar_file, 'w:gz') as t:
        t.add(os.path.join(output_dir, 'prediction.mgz'), arcname='prediction.mgz')
        t.add(os.path.join(output_dir, 'images.txt'), arcname='images.txt')
    # Return tar-file
    return tar_file
