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
        self.SUBJECT_FILE = os.path.join(DATA_DIR, 'subjects/ernie.tar.gz')
        self.IMAGES_ARCHIVE = os.path.join(DATA_DIR, 'images/small-sample.tar')
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
        shutil.rmtree(API_DIR)
        MongoClient().drop_database('test_sco')

    def test_invalid_model_name(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Create run with an invalid run name."""
        # Create subject, image group and experiment
        subject = self.db.subjects_create(self.SUBJECT_FILE)
        images = self.db.images_create(self.IMAGES_ARCHIVE)
        experiment = self.db.experiments_create(
            subject.identifier,
            images.identifier,
            {'name':'Test Experiment'}
        )
        # Create new model run
        model_run = self.db.experiments_predictions_create(
            experiment.identifier,
            'not a valid run name',
            'Test Run'
        )
        # Run model
        SCODataStoreWorker(self.db, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                'ok to have a dummy Url here'
            )
        )
        # Ensure that model run is in FAILED state
        model_run = self.db.experiments_predictions_get(
            experiment.identifier,
            model_run.identifier
        )
        self.assertTrue(model_run.state.is_failed)

    def test_missing_image_group(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Run experiment to validate code."""
        # Create subject, image group and experiment
        subject = self.db.subjects_create(self.SUBJECT_FILE)
        images = self.db.images_create(self.IMAGES_ARCHIVE)
        experiment = self.db.experiments_create(
            subject.identifier,
            images.identifier,
            {'name':'Test Experiment'}
        )
        # Create new model run
        model_run = self.db.experiments_predictions_create(
            experiment.identifier,
            'benson17',
            'Test Run'
        )
        # Delete Image Group
        self.db.image_groups_delete(images.identifier)
        # Run model
        SCODataStoreWorker(self.db, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                'ok to have a dummy Url here'
            )
        )
        # Ensure that model run is in FAILED state
        model_run = self.db.experiments_predictions_get(
            experiment.identifier,
            model_run.identifier
        )
        self.assertTrue(model_run.state.is_failed)

    def test_missing_subject(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Run experiment to validate code."""
        # Create subject, image group and experiment
        subject = self.db.subjects_create(self.SUBJECT_FILE)
        images = self.db.images_create(self.IMAGES_ARCHIVE)
        experiment = self.db.experiments_create(
            subject.identifier,
            images.identifier,
            {'name':'Test Experiment'}
        )
        # Create new model run
        model_run = self.db.experiments_predictions_create(
            experiment.identifier,
            'benson17',
            'Test Run'
        )
        # Delete subject
        self.db.subjects_delete(subject.identifier)
        # Run model
        SCODataStoreWorker(self.db, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                'ok to have a dummy Url here'
            )
        )
        # Ensure that model run is in FAILED state
        model_run = self.db.experiments_predictions_get(
            experiment.identifier,
            model_run.identifier
        )
        self.assertTrue(model_run.state.is_failed)

    def test_successful_model_run(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Run experiment to validate code."""
        # Create subject, image group and experiment
        subject = self.db.subjects_create(self.SUBJECT_FILE)
        images = self.db.images_create(self.IMAGES_ARCHIVE)
        experiment = self.db.experiments_create(
            subject.identifier,
            images.identifier,
            {'name':'Test Experiment'}
        )
        # Create new model run
        model_run = self.db.experiments_predictions_create(
            experiment.identifier,
            'benson17',
            'Test Run',
            arguments=[
                Attribute('contrast_constants_by_label', {'1': 0.93, '2': 0.99, '3': 0.99}),
                Attribute('max_eccentricity', 12),
                Attribute('modality', 'volume'),
                Attribute('divisive_exponents_by_label', {'1': 1.0, '2': 1.0, '3': 1.0}),
                Attribute('pRF_sigma_slopes_by_label', {'1': 0.1, '2': 0.15, '3': 0.27}),
                Attribute('compressive_constants_by_label', {'1': 0.18, '2': 0.13, '3': 0.12}),
                Attribute('normalized_pixels_per_degree', 12),
                Attribute('gabor_orientations', 8),
                Attribute('pRF_n_radii', 3.0),
                Attribute('saturation_constants_by_label', {'1': 0.5, '2': 0.5, '3': 0.5}),
                Attribute('aperture_radius', 0.5),
                Attribute('pixels_per_degree', 0.6),
                Attribute('background', 0.5),
                Attribute('aperture_edge_width', 0),
                Attribute('gamma', [2,6,7,50,90])
            ]
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
        # Nothing should happen if we try to run the same prediction again
        SCODataStoreWorker(self.db, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                'ok to have a dummy Url here'
            )
        )
        model_run = self.db.experiments_predictions_get(
            experiment.identifier,
            model_run.identifier
        )


if __name__ == '__main__':
    unittest.main()
