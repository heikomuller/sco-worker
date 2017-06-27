"""Run test for local worker. Set-up new data store with single experiment.
Create prediction to test the local worker code.
"""

from pymongo import MongoClient
import os
import shutil
import unittest

from neuropythy.freesurfer import add_subject_path

from scodata import SCODataStore
from scodata.attribute import Attribute
from scodata.mongo import MongoDBFactory
from scoengine import ModelRunRequest
from scoworker import SCODataStoreWorker


API_DIR = '/tmp/test_sco'
ENV_DIR = os.path.abspath('./data/subjects')
DATA_DIR = os.path.abspath('./data')


class TestSCODataStoreWorker(unittest.TestCase):

    def setUp(self):
        """Clean-up eventual existing test data store. Create fresh data store
        instance."""
        # Set file names for subject and image group files for upload
        self.SUBJECT_FILE = os.path.join(DATA_DIR, 'subjects/kay2008_subj1.tar.gz')
        self.IMAGES_ARCHIVE = os.path.join(DATA_DIR, 'images/sample_images.tar.gz')
        self.FUNC_DATA = os.path.join(DATA_DIR, 'func/sample.nii')
        # Add Freesurfer subject path
        add_subject_path(ENV_DIR)
        # Delete data store directory if exists
        if os.path.isdir(API_DIR):
            shutil.rmtree(API_DIR)
        # Drop test database
        MongoClient().drop_database('test_sco')
        # Create fresh instance of SCO data store
        self.db = SCODataStore(MongoDBFactory(db_name='test_sco'), API_DIR)

    def tearDown(self):
        """Delete data store directory and database."""
        pass
        shutil.rmtree(API_DIR)
        MongoClient().drop_database('test_sco')

    def test_successful_model_run(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Run experiment to validate code."""
        # Create subject, image group and experiment
        subject = self.db.subjects_create(self.SUBJECT_FILE)
        images = self.db.images_create(self.IMAGES_ARCHIVE)
        self.db.image_groups_update_options(
            images.identifier,
            [Attribute('pixels_per_degree', 6.4)]
        )
        experiment = self.db.experiments_create(
            subject.identifier,
            images.identifier,
            {'name':'Test Experiment'}
        )
        self.db.experiments_fmri_create(experiment.identifier, self.FUNC_DATA)
        # Create new model run
        args={
            'stimulus_edge_value': 0.5,
            'gabor_orientations' : 8,
            'normalized_pixels_per_degree' : 6.4,
            'max_eccentricity': 10.0,
            'aperture_edge_width': 0,
            'aperture_radius': 10.0,
        }
        model_run = self.db.experiments_predictions_create(
            experiment.identifier,
            'benson17',
            'Test Run',
            arguments=[{'name' : key, 'value' : args[key]} for key in args]
        )
        SCODataStoreWorker(self.db, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                'ok to have a dummy Url here'
            )
        )
        # Ensure that model run is in SUCCESS state
        model_run = self.db.experiments_predictions_get(
            experiment.identifier,
            model_run.identifier
        )
        self.assertTrue(model_run.state.is_success)
        # Make sure that the attachments are correct. We expect one attachment
        # containing the list of images.\# Count the number of lines in the
        # images.txt file. This should be the same as the number of images in
        # the image group
        self.assertTrue('input-image-list' in model_run.attachments)
        line_count = 0
        image_list_file = self.db.experiments_predictions_attachments_download(
            experiment.identifier,
            model_run.identifier,
            'input-image-list'
        ).file
        with open(image_list_file, 'r') as f:
            for line in f:
                line_count += 1
        self.assertEqual(line_count, len(images.images))

if __name__ == '__main__':
    unittest.main()