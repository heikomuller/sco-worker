"""Run local copy of SCO predictive model code to ensure that everything is
setup properly.
"""

from neuropythy.freesurfer import add_subject_path
import os
import sco


env_dir = os.path.abspath('./data/subjects')

subject_dir = os.path.abspath('./data/subjects/ernie')

image_files = [
    os.path.abspath('./data/images/tex-320x320-im13-smp1.png'),
    os.path.abspath('./data/images/tex-320x320-im18-smp1.png')
]

opts = {
    'stimulus_edge_value': 0.5,
    'max_eccentricity' : 12,
    'gabor_orientations' : 8
}

add_subject_path(env_dir)

mdl = sco.build_model('benson17', force_exports=True)
res = mdl(subject=subject_dir, stimulus=image_files, ground_truth_filename=None, pixels_per_degree=12, output_directory='./data/output')

print res
