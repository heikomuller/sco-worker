"""Run test for local worker. Set-up new data store with single experiment.
Create prediction to test the local worker code.
"""

from pymongo import MongoClient
import os
import shutil
import unittest

from neuropythy.freesurfer import add_subject_path

from scodata import SCODataStore
from scodata.mongo import MongoDBFactory
from scoengine import SCOEngine, ModelRunRequest
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
        mongo = MongoDBFactory(db_name='test_sco')
        # Create fresh instance of SCO data store
        self.db = SCODataStore(mongo, API_DIR)
        self.engine = SCOEngine(mongo)

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
            'not a valid model name',
            [],
            'Test Run'
        )
        # Run model
        SCODataStoreWorker(self.db, self.engine, ENV_DIR).run(
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
            'Test Run',
            []
        )
        # Delete Image Group
        self.db.image_groups_delete(images.identifier)
        # Run model
        SCODataStoreWorker(self.db, self.engine, ENV_DIR).run(
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
            'Test Run',
            []
        )
        # Delete subject
        self.db.subjects_delete(subject.identifier)
        # Run model
        SCODataStoreWorker(self.db, self.engine, ENV_DIR).run(
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


if __name__ == '__main__':
    unittest.main()
