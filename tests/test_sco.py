"""Run local copy of SCO predictive model code to ensure that everything is
setup properly.
"""

from neuropythy.freesurfer import add_subject_path
import os
import sco
import pimms
import pint

env_dir = os.path.abspath('./data/subjects')

subject_dir = os.path.abspath('./data/subjects/ernie')

image_files = [
    os.path.abspath('./data/images/tex-320x320-im13-smp1.png'),
    os.path.abspath('./data/images/tex-320x320-im18-smp1.png')
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
    'output_directory': './data/output',
    'measurements_filename': None
}

add_subject_path(env_dir)

model = sco.build_model('benson17')
data  = model(opts)

print data['exported_files']
