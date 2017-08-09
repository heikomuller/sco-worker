"""Run local copy of SCO predictive model code to ensure that everything is
setup properly.
"""

from neuropythy.freesurfer import add_subject_path
import os
import sco
import pimms
import pint
import nibabel as nib
import numpy as np

# Use this flag to control whether cortical images are created at the end of
# the model run
generate_cortical_images = True

env_dir = os.path.abspath('./data/subjects')

subject_dir = os.path.abspath('./data/subjects/kk_subj001')
func_filename = './data/func/sample.nii'
output_dir = './data/output'

image_files = [
    os.path.abspath('./data/images/validate_0000.png'),
    os.path.abspath('./data/images/validate_0001.png'),
    os.path.abspath('./data/images/validate_0002.png'),
    os.path.abspath('./data/images/validate_0003.png'),
    os.path.abspath('./data/images/validate_0004.png'),
    os.path.abspath('./data/images/validate_0005.png'),
    os.path.abspath('./data/images/validate_0006.png'),
    os.path.abspath('./data/images/validate_0007.png'),
    os.path.abspath('./data/images/validate_0008.png'),
    os.path.abspath('./data/images/validate_0009.png')
]

d2p           = pimms.quant(128.0/20.0, 'px/deg')
max_eccen     = pimms.quant(10.0, 'deg')

opts = {
    'stimulus': image_files,
    'subject': subject_dir,
    'stimulus_edge_value': 0.5,
    'gabor_orientations' : 8,
    'pixels_per_degree': d2p,
    'normalized_pixels_per_degree' : d2p,
    'max_eccentricity': max_eccen,
    'aperture_edge_width': 0,
    'aperture_radius': max_eccen,
    'output_directory': output_dir,
    'measurements_filename': func_filename
}

add_subject_path(env_dir)

model = sco.build_model('benson17')
data  = model(opts)

print data['exported_files']

if generate_cortical_images:
    cortex_idcs = data['cortex_indices']
    measurement_idcs = data['measurement_indices']

    # Get the filename of the predicted results out of the exported_files list:
    pred_filename = os.path.join(output_dir, 'prediction.nii.gz')

    # use nibabel (import nibabel as nib) to load this file
    pred_nii = nib.load(pred_filename)

    # the header and data can be obtained like so:
    pred_hdr = pred_nii.header
    pred_dat = pred_nii.dataobj.get_unscaled()


    func_nii = nib.load(func_filename )
    func_hdr = func_nii.header
    func_dat = func_nii.dataobj.get_unscaled()

    pred = np.asarray([pred_dat[ii,jj,kk,:] for (ii,jj,kk) in cortex_idcs])
    func = np.asarray([func_dat[ii,jj,kk,:] for (ii,jj,kk) in measurement_idcs])

    for imno in range(len(image_files)):
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
            img.savefig(os.path.join(output_dir, img_filename))
            img.clf()

    sco = sco.reload_sco()

    for imno in range(len(image_files)):
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
            img.savefig(os.path.join(output_dir, img_filename))
            img.clf()
