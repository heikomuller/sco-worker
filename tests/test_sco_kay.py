import numpy as np
import nibabel as nib
import os
import pimms
import sco


base_dir = '/home/heiko/projects/sco/sco-worker/tests/data'
output_dir = os.path.join(base_dir, 'output')

# The images that are used as input
stimulus_dir = os.path.join(base_dir, 'images', 'kay2008')
img_filenames = [os.path.join(stimulus_dir, 'validate_%04d.png'% i)
                 for i in range(120)]

# This is the filename of the ground-truth functional data
func_filename = os.path.join(base_dir, 'func', 'Sub1_Val.nii.gz')
# The subject's FreeSurfer directory
subject = os.path.join(base_dir, 'subjects', 'kk_subj001')

# Some additional parameters
d2p           = pimms.quant(128.0/20.0, 'px/deg')
max_eccen     = pimms.quant(10.0, 'deg')

# This just sets up the map of parameter dictionary
params = dict(stimulus                     = img_filenames,
              subject                      = subject,
              pixels_per_degree            = d2p,
              normalized_pixels_per_degree = d2p,
              max_eccentricity             = max_eccen,
              ground_truth_filename        = func_filename,
              aperture_edge_width          = 0,
              aperture_radius              = max_eccen,
              output_directory             = output_dir,
              create_directories           = False,
              output_prefix                = None,
              output_suffix                = None)

################################################################################
# Then, build the model and give it the parameters:
model = sco.build_model('benson17')
data  = model(params)

exported_files = data['exported_files']
print 'exported_files'
print exported_files

angles = data['polar_angles']
print 'polar_angles'
print angles
eccens = data['eccentricities']
print 'eccentricities'
print eccens

standard_angles = np.pi/2 - angles.to('rad').m
x = eccens * np.cos(standard_angles)
y = eccens * np.sin(standard_angles)

labels = data['labels']
print 'labels'
print labels

anat_ids = data['anatomical_ids']
print 'anatomical_ids'
print anat_ids
