"""Run test for remote worker. Expects that the server API is running locally
on port 5000.
"""

from pymongo import MongoClient
import os
import shutil
import unittest

from neuropythy.freesurfer import add_subject_path

from scocli import SCOClient
from scoengine import ModelRunRequest
from scoworker import SCOClientWorker


API_URL = 'http://localhost:5000/sco-server/api/v1'
CLIENT_DIR = '/tmp/test_sco'
ENV_DIR = os.path.abspath('./data/subjects')
DATA_DIR = os.path.abspath('./data')


class TestSCODataStoreWorker(unittest.TestCase):

    def setUp(self):
        """Clean-up eventual existing client cache directory. Create fresh SCO
        client instance."""
        # Set file names for subject and image group files for upload
        self.SUBJECT_FILE = os.path.join(DATA_DIR, 'subjects/ernie.tar.gz')
        self.IMAGES_ARCHIVE = os.path.join(DATA_DIR, 'images/small-sample.tar')
        # Add Freesurfer subject path
        add_subject_path(ENV_DIR)
        # Delete data store directory if exists
        if os.path.isdir(CLIENT_DIR):
            shutil.rmtree(CLIENT_DIR)
        # Create fresh instance of SCO data store
        self.sco = SCOClient(api_url=API_URL, data_dir=CLIENT_DIR)

    def tearDown(self):
        """Delete client cache directory."""
        shutil.rmtree(CLIENT_DIR)

    def test_successful_model_run(self):
        """Test local SCO worker. Create experiment from subject and image group
        files. Run experiment to validate code."""
        # Create subject, image group and experiment
        subject = self.sco.subjects_create(self.SUBJECT_FILE)
        images = self.sco.image_groups_create(self.IMAGES_ARCHIVE, options={'pixels_per_degree' : 12})
        experiment = self.sco.experiments_create(
            'Test Experiment',
            subject.identifier,
            images.identifier,
        )
        # Create new model run
        model_run = experiment.run('benson17', 'Test Run')
        SCOClientWorker(self.sco, ENV_DIR).run(
            ModelRunRequest(
                model_run.identifier,
                experiment.identifier,
                model_run.url
            )
        )
        # Ensure that model run is in SUCCESS state
        model_run = model_run.refresh()
        self.assertTrue(model_run.state.is_success)


if __name__ == '__main__':
    unittest.main()
