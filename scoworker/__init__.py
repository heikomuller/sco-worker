"""Standard Cortical Observer - Workers

Worker classes are used to execute predictive model run requests. Different
implementations for these workers may exists. We currently distinguish based on
the way they interact with the SCO data store to retrieve and create resources.

A worker that runs on the same machine as the SCO data store can use an instance
of the SCODataStore class to access SCO resources. A worker that runs on a
remote machine will use the SCOClient to access SCO resources.
"""

from abc import abstractmethod
import logging
from neuropythy.freesurfer import add_subject_path
import shutil
import tempfile
import scodata.prediction as runs
import scodata.funcdata as funcdata
from scoworker.workflow import sco_run


class SCOWorker(object):
    """SCO worker executes the predictive SCO model. Different implementations
    for the worker may exists, e.g., local or remote worker.
    """
    def __init__(self, env_subject):
        """Initialize the environment path for 'average' subject fsaverage_sym.

        Parameters
        ----------
        env_subject : string
            Path to directory containing subject fsaverage_sym.
        """
        add_subject_path(env_subject)

    @abstractmethod
    def run(self, request):
        """Run SCO model for given request. Expects a model run request
        containing run and experiment identifier as well as run resource URL.

        Parameters
        ----------
        request : scoengine.ModelRunRequest
            Object containing information about requested model run
        """
        pass


class SCODataStoreWorker(SCOWorker):
    """Implementation for SCO worker running on same machine as the SCO data
    store. Uses and instance of the SCODataStore to access and manipulate SCO
    resources.
    """
    def __init__(self, db, env_subject):
        """Initialize the data store instance and average subject path.

        Parameters
        ----------
        db : scodata.SCODataStore
            Connection to local SCO data store
        env_subject : string
            Path to directory containing subject fsaverage_sym.
        """
        super(SCODataStoreWorker, self).__init__(env_subject)
        self.db = db

    def run(self, request):
        """Run SCO model for given request on a local instance of the SCO data
        store. Expects a model run request containing run and experiment
        identifier as well as run resource URL.

        Parameters
        ----------
        request : scoengine.ModelRunRequest
            Object containing information about requested model run
        """
        # Get model run handler from database. Ensure that it is in state IDLE
        # or RUNNING.
        try:
            model_run = self.db.experiments_predictions_get(
                request.experiment_id,
                request.run_id
            )
            if model_run is None:
                raise ValueError('unknown model run: ' + request.run_id + ':' + request.experiment_id)
            if not (model_run.state.is_idle or model_run.state.is_running):
                raise ValueError('invalid run state: ' + str(model_run.state))
        except ValueError as ex:
            # In case of an exception return. No point in updating the state
            # of a non-existing model run
            logging.exception(ex)
            return
        # Get resources that are associated with the model run and necessary to
        # run the prediction. Raise ValueError (and set model run state to
        # FAILED) if either of the resources does not exist.
        try:
            # Get experiment. Raise exception if experiment does not exist.
            experiment = self.db.experiments_get(model_run.experiment)
            if experiment is None:
                raise ValueError('unknown experiment: ' + model_run.experiment)
            # Get associated subject. Raise exception if subject does not exist
            subject = self.db.subjects_get(experiment.subject)
            if subject is None:
                raise ValueError('unknown subject: ' + experiment.subject)
            # Get associated image group. Raise exception if image group does not exist
            image_group = self.db.image_groups_get(experiment.images)
            if image_group is None:
                raise ValueError('unknown image group: ' + experiment.images)
        except ValueError as ex:
            logging.exception(ex)
            # In case of an exception set run state to failed and return
            self.db.experiments_predictions_update_state_error(
                model_run.experiment,
                model_run.identifier,
                [str(ex)]
            )
            return
        # Set run state to RUNNING (only if IDLE) and call generic run_sco
        # workflow. Make sure to catch all exceptions.
        if model_run.state.is_idle:
            self.db.experiments_predictions_update_state_active(
                model_run.experiment,
                model_run.identifier
            )
        # Temporal directory for run results
        temp_dir = tempfile.mkdtemp()
        try:
            tar_file = sco_run(model_run, subject, image_group, temp_dir)
        except Exception as ex:
            logging.exception(ex)
            # In case of an exception set run state to failed and return
            self.db.experiments_predictions_update_state_error(
                model_run.experiment,
                model_run.identifier,
                [type(ex).__name__ + ': ' + str(ex)]
            )
            return
        # Update run state to success by uploading resoult file
        self.db.experiments_predictions_update_state_success(
            model_run.experiment,
            model_run.identifier,
            tar_file
        )
        # Clean-up
        shutil.rmtree(temp_dir)


class SCOClientWorker(SCOWorker):
    """Implementation for SCO worker that uses the SCO client to access and
    create resources.
    """
    def __init__(self, sco, env_subject):
        """Initialize the SCO client instance and average subject path.

        Parameters
        ----------
        sco : scocli.SCOClient
            Connection to SCO data store via SCO client
        env_subject : string
            Path to directory containing subject fsaverage_sym.
        """
        super(SCOClientWorker, self).__init__(env_subject)
        self.sco = sco

    def run(self, request):
        """Run SCO model for given request. Uses the resource URL in the given
        request to access the model run information and to fetch associated
        resources.

        Parameters
        ----------
        request : scoengine.ModelRunRequest
            Object containing information about requested model run
        """
        # Get model run handler from database. Ensure that it is in state IDLE
        # or RUNNING.
        try:
            model_run = self.sco.experiments_runs_get(request.resource_url)
            if model_run is None:
                raise ValueError('unknown model run: ' + request.run_id + ':' + request.experiment_id)
            if not (model_run.state.is_idle or model_run.state.is_running):
                raise ValueError('invalid run state: ' + str(model_run.state))
        except ValueError as ex:
            # In case of an exception return. No point in updating the state
            # of a non-existing model run
            logging.exception(ex)
            return
        # Get resources that are associated with the model run and necessary to
        # run the prediction. Catch ValueError (and set model run state to
        # FAILED) if either of the resources does not exist.
        try:
            # Get experiment. Raise exception if experiment does not exist.
            experiment = model_run.experiment
        except ValueError as ex:
            # In case of an exception set run state to failed and return
            model_run.update_state_error([
                'unknown experiment: ' + model_run.experiment_url,
                str(ex)
            ])
            return
        try:
            # Get associated subject. Raise exception if subject does not exist
            subject = experiment.subject
        except ValueError as ex:
            # In case of an exception set run state to failed and return
            model_run.update_state_error([
                'unknown subject: ' + model_run.subject_url,
                str(ex)
            ])
            return
        try:
            # Get associated image group. Raise exception if image group does not exist
            image_group = experiment.image_group
        except ValueError as ex:
            # In case of an exception set run state to failed and return
            model_run.update_state_error(
                'unknown image group: ' + experiment.image_group_url,
                [str(ex)]
            )
            return
        # Set run state to RUNNING (only if IDLE) and call generic run_sco
        # workflow. Make sure to catch all exceptions.
        if model_run.state.is_idle:
            model_run.update_state_active()
        # Temporal directory for run results
        temp_dir = tempfile.mkdtemp()
        try:
            tar_file = sco_run(model_run, subject, image_group, temp_dir)
        except Exception as ex:
            # In case of an exception set run state to failed and return
            model_run.update_state_error([type(ex).__name__ + ': ' + str(ex)])
            return
        # Update run state to success. This will upload the given tar file as
        # model run result
        model_run.update_state_success(tar_file)
        # Clean-up
        shutil.rmtree(temp_dir)
