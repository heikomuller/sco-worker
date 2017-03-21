"""Implements the run SCO model workflow for a given user request."""

from abc import abstractmethod
import os
import shutil
import tarfile
import tempfile

import sco


def sco_run(model_run, subject, image_group, output_dir, fmri_data=None):
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
    fmri_data : fMRI handle, optional
        Handle for functional MRI data (either scocli. or scodata.funcdata.FMRIDataHandle). Can be none if no fMRI data is associated with the run experiment .

    Returns
    -------
    string
        Path to generated tar file
    """
    # Get subject directory
    subject_dir = subject.data_directory
    # Create list of image files
    image_files = [img.filename for img in image_group.images]
    # Compose run arguments from image group options and model run arguments.
    args = {'subject' : subject_dir, 'stimulus' : image_files, 'output_directory' : output_dir}
    # Set ground truth data (directory) if fMRI data handle is given
    if not fmri_data is None:
        args['ground_truth_filename'] = fmri_data.directory
    else:
        args['ground_truth_filename'] = None
    # Add image group options
    for attr in image_group.options:
        args[attr] = convert_parameter_value(image_group.options[attr].value)
    # Add run options
    for attr in model_run.arguments:
        args[attr] = convert_parameter_value(model_run.arguments[attr].value)
    # Run model. Exceptions are not caught here to allow callers to adjust run
    # run states according to their respective implementations (i.e., remote or
    # local worker will use different methods to change run state).
    model = sco.build_model(model_run.model_id, force_exports=True)
    model(**args)
    # Overwrite the generated images file with folders and names of images
    # in image group
    with open(os.path.join(output_dir, 'images.txt'), 'w') as f:
        for img in image_group.images:
            f.write(img.folder + img.name + '\n')
    # Create a tar file in the temp directory
    tar_file = os.path.join(output_dir, 'results.tar.gz')
    with tarfile.open(tar_file, 'w:gz') as t:
        for filename in os.listdir(output_dir):
            if filename != 'results.tar.gz':
                t.add(os.path.join(output_dir, filename), arcname=filename)
    # Return tar-file
    return tar_file


def convert_parameter_value(db_value):
    """Converter for parameter values. Converts a parameter value from its
    storage format in the database into the representation that is expected by
    the SCO model.

    This is a (temporary) work-around for dictionaries that have integer values
    as their keys. These dictionares cannot be stored directly in MongoDB
    (keys have to be string). Thus, this function converts the type of the
    dictionary key from string to integer. All other types of parameters remain
    untouched.

    Parameters
    ----------
    db_value : any
        Parameter value as stored in the SCO Data Store

    Returns
    -------
    any
        Parameter value in format expected by SCO model.
    """
    if type(db_value) is dict:
        result = {}
        for key in db_value:
            result[int(key)] = db_value[key]
        return result
    else:
        return db_value
