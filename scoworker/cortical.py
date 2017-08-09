"""This module conatins methods for creating and manipulating cortical images
that are generated from SCO model run predictions and functional data.

csv
img.identifier, Func/Pred, V1-3, Filename

"""

import os
import shutil
import tempfile
import tarfile
import sco
import pimms
import pint
import nibabel as nib
import numpy as np


DEFAULT_TARFILE_NAME = 'cortical-images.tar'


def create_cortical_image_tar(data, input_images, func_filename, output_dir):
    """Create a tar-file of cortical images for given model output.

    Parameters
    ----------
    data : sco.model output
        Data object returned by SCO model
    input_images : ImageGroupHandle
        List of input images
    func_filename : string
        Path to functionl data file. May be None. If None, no coritcal images
        for functional data are generated.
    output_dir : stringd
        Path to the directory where the tar file is created.
    """
    cortex_idcs = data['cortex_indices']
    measurement_idcs = data['measurement_indices']

    # Get the filename of the predicted results out of the exported_files list:
    pred_filename = os.path.join(output_dir, 'prediction.nii.gz')

    # use nibabel (import nibabel as nib) to load this file
    pred_nii = nib.load(pred_filename)

    # the header and data can be obtained like so:
    pred_hdr = pred_nii.header
    pred_dat = pred_nii.dataobj.get_unscaled()
    pred = np.asarray([pred_dat[ii,jj,kk,:] for (ii,jj,kk) in cortex_idcs])

    if not func_filename is None:
        func_nii = nib.load(func_filename)
        func_hdr = func_nii.header
        func_dat = func_nii.dataobj.get_unscaled()
        func = np.asarray([func_dat[ii,jj,kk,:] for (ii,jj,kk) in measurement_idcs])

    # Create temporary directory for cortical images
    tar_dir = tempfile.mkdtemp()

    # List of rows in the final CSV file
    csv_rows = []

    if not func_filename is None:
        for imno in range(len(input_images.images)):
            for va in range(1,4):
                img = sco.util.cortical_image(
                    func,
                    data['measurement_labels'],
                    data['measurement_pRFs'],
                    data['max_eccentricity'],
                    visual_area=va,
                    image_number=imno,
                    smoothing=0.5, speckle=500
                )
                img_filename = 'func_' + str(imno) + '.v' + str(va) + '.png'
                img.savefig(os.path.join(tar_dir, img_filename))
                img.clf()
                csv_rows.append([
                    input_images.images[imno].identifier,
                    'FUNCTIONAL',
                    str(va),
                    img_filename
                ])

    sco_load = sco.reload_sco()

    for imno in range(len(input_images.images)):
        for va in range(1,4):
            img = sco.util.cortical_image(
                pred,
                data['labels'],
                data['pRFs'],
                data['max_eccentricity'],
                visual_area=va,
                image_number=imno
            )
            img_filename = 'pred_' + str(imno) + '.v' + str(va) + '.png'
            img.savefig(os.path.join(tar_dir, img_filename))
            img.clf()
            csv_rows.append([
                input_images.images[imno].identifier,
                'PREDICTION',
                str(va),
                img_filename
            ])

    with open(os.path.join(tar_dir, 'index.csv'), 'w') as f:
        for row in csv_rows:
            f.write(','.join(row) + '\n')

    tar_file_name = os.path.join(output_dir, DEFAULT_TARFILE_NAME)

    # TODO: Create a tar-file that contains all the files in directory tar_dir
    #Create Tar file
    tFile = tarfile.open(tar_file_name, 'w')

    files = os.listdir(tar_dir)
    for f in files:
        tFile.add(os.path.join(tar_dir, f), arcname=f)

    tFile.close()

    # Clean up. Remove temporary ter directory
    shutil.rmtree(tar_dir)

    return DEFAULT_TARFILE_NAME
