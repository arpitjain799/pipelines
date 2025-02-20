# Copyright 2021 The Kubeflow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test Hyperparameter Tuning Job module."""

import json

from google_cloud_pipeline_components.experimental.hyperparameter_tuning_job import (
    GetBestHyperparametersOp,
    GetBestTrialOp,
    GetHyperparametersOp,
    GetTrialsOp,
    GetWorkerPoolSpecsOp,
    IsMetricBeyondThresholdOp,
    serialize_metrics,
)

import unittest
from unittest import mock
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import (
    hyperparameter_tuning_job,
    study,
)


class HyperparameterTuningJobTest(unittest.TestCase):

  def setUp(self):
    super(HyperparameterTuningJobTest, self).setUp()
    self._gcp_resources = (
        '{ "resources": [ { "resourceType": '
        '"HyperparameterTuningJob", "resourceUri": '
        '"https://us-central1-aiplatform.googleapis.com/'
        'v1/projects/186556260430/locations/us-central1/'
        'hyperparameterTuningJobs/1234567890123456789" '
        '} ] }'
    )
    self._best_trial_max = (
        '{\n "id": "2",\n "state": 4,\n "parameters": '
        '[\n {\n "parameterId": "learning_rate",\n "value": '
        '0.028\n },\n {\n "parameterId": '
        '"momentum",\n "value": 0.5\n },\n {\n "parameterId":'
        ' "num_neurons",\n "value": 128.0\n }\n ],\n '
        '"finalMeasurement": {\n "stepCount": "10",\n '
        '"metrics": [\n {\n "metricId": '
        '"accuracy",\n "value": 0.734375\n }\n ]\n },\n '
        '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
        '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
        '"measurements": [],\n "clientId": "",\n '
        '"infeasibleReason": "",\n "customJob": ""\n, '
        '"webAccessUris": {}\n}'
    )
    self._trials_max = [
        (
            '{\n "id": "1",\n "state": 4,\n "parameters": '
            '[\n {\n "parameterId": "learning_rate",\n "value": '
            '0.03\n },\n {\n "parameterId": '
            '"momentum",\n "value": 0.44\n },\n {\n "parameterId":'
            ' "num_neurons",\n "value": 256.0\n }\n ],\n '
            '"finalMeasurement": {\n "stepCount": "10",\n '
            '"metrics": [\n {\n "metricId": '
            '"accuracy",\n "value": 0.6\n }\n ]\n },\n '
            '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
            '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
            '"measurements": [],\n "clientId": "",\n '
            '"infeasibleReason": "",\n "customJob": ""\n, '
            '"webAccessUris": {}\n}'
        ),
        self._best_trial_max,
        (
            '{\n "id": "3",\n "state": 4,\n "parameters": '
            '[\n {\n "parameterId": "learning_rate",\n "value": '
            '0.022\n },\n {\n "parameterId": '
            '"momentum",\n "value": 0.45\n },\n {\n "parameterId":'
            ' "num_neurons",\n "value": 512.0\n }\n ],\n '
            '"finalMeasurement": {\n "stepCount": "10",\n '
            '"metrics": [\n {\n "metricId": '
            '"accuracy",\n "value": 0.5\n }\n ]\n },\n '
            '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
            '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
            '"measurements": [],\n "clientId": "",\n '
            '"infeasibleReason": "",\n "customJob": ""\n, '
            '"webAccessUris": {}\n}'
        ),
    ]
    self._best_hp_max = [
        '{\n "parameterId": "learning_rate",\n "value": 0.028\n}',
        '{\n "parameterId": "momentum",\n "value": 0.5\n}',
        '{\n "parameterId": "num_neurons",\n "value": 128.0\n}',
    ]
    self._best_trial_min = (
        '{\n "id": "2",\n "state": 4,\n "parameters": '
        '[\n {\n "parameterId": "learning_rate",\n "value": '
        '0.028\n },\n {\n "parameterId": '
        '"momentum",\n "value": 0.4\n },\n {\n "parameterId":'
        ' "num_neurons",\n "value": 256.0\n }\n ],\n '
        '"finalMeasurement": {\n "stepCount": "10",\n '
        '"metrics": [\n {\n "metricId": '
        '"loss",\n "value": 0.4\n }\n ]\n },\n '
        '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
        '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
        '"measurements": [],\n "clientId": "",\n '
        '"infeasibleReason": "",\n "customJob": ""\n, '
        '"webAccessUris": {}\n}'
    )
    self._trials_min = [
        (
            '{\n "id": "1",\n "state": 4,\n "parameters": '
            '[\n {\n "parameterId": "learning_rate",\n "value": '
            '0.03\n },\n {\n "parameterId": '
            '"momentum",\n "value": 0.44\n },\n {\n "parameterId":'
            ' "num_neurons",\n "value": 256.0\n }\n ],\n '
            '"finalMeasurement": {\n "stepCount": "10",\n '
            '"metrics": [\n {\n "metricId": '
            '"loss",\n "value": 0.6\n }\n ]\n },\n '
            '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
            '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
            '"measurements": [],\n "clientId": "",\n '
            '"infeasibleReason": "",\n "customJob": ""\n, '
            '"webAccessUris": {}\n}'
        ),
        self._best_trial_min,
        (
            '{\n "id": "3",\n "state": 4,\n "parameters": '
            '[\n {\n "parameterId": "learning_rate",\n "value": '
            '0.022\n },\n {\n "parameterId": '
            '"momentum",\n "value": 0.45\n },\n {\n "parameterId":'
            ' "num_neurons",\n "value": 512.0\n }\n ],\n '
            '"finalMeasurement": {\n "stepCount": "10",\n '
            '"metrics": [\n {\n "metricId": '
            '"loss",\n "value": 0.7\n }\n ]\n },\n '
            '"startTime": "2021-12-10T00:41:57.675086142Z",\n '
            '"endTime": "2021-12-10T00:52:35Z",\n "name": "",\n '
            '"measurements": [],\n "clientId": "",\n '
            '"infeasibleReason": "",\n "customJob": ""\n, '
            '"webAccessUris": {}\n}'
        ),
    ]
    self._best_hp_min = [
        '{\n "parameterId": "learning_rate",\n "value": 0.028\n}',
        '{\n "parameterId": "momentum",\n "value": 0.4\n}',
        '{\n "parameterId": "num_neurons",\n "value": 256.0\n}',
    ]
    self._worker_pool_specs = [{
        'machine_spec': {
            'machine_type': 'n1-standard-4',
            'accelerator_type': 'NVIDIA_TESLA_T4',
            'accelerator_count': 1,
        },
        'replica_count': 1,
        'container_spec': {'image_uri': 'gcr.io/project_id/test'},
    }]
    self._metrics_spec_max = serialize_metrics({'accuracy': 'maximize'})
    self._metrics_spec_min = serialize_metrics({'loss': 'minimize'})

  @mock.patch.object(aiplatform.gapic, 'JobServiceClient', autospec=True)
  def test_get_trials_op(self, mock_job_service_client):
    job_client = mock.Mock()
    mock_job_service_client.return_value = job_client

    mock_get_hpt_job = mock.Mock()
    job_client.get_hyperparameter_tuning_job = mock_get_hpt_job
    mock_get_hpt_job.return_value = (
        hyperparameter_tuning_job.HyperparameterTuningJob(
            trials=[study.Trial.from_json(trial) for trial in self._trials_max]
        )
    )
    expected_output = [json.loads(trial) for trial in self._trials_max]

    output_trials = GetTrialsOp.python_func(gcp_resources=self._gcp_resources)
    output = [json.loads(trial) for trial in output_trials]

    mock_job_service_client.assert_called_once_with(
        client_options={'api_endpoint': 'us-central1-aiplatform.googleapis.com'}
    )
    mock_get_hpt_job.assert_called_once_with(
        name=(
            'projects/186556260430/locations/us-central1/'
            'hyperparameterTuningJobs/1234567890123456789'
        )
    )
    self.assertEqual(output, expected_output)

  def test_get_best_trial_op_max(self):
    expected_output = self._best_trial_max

    output = GetBestTrialOp.python_func(
        trials=self._trials_max, study_spec_metrics=self._metrics_spec_max
    )

    self.assertEqual(json.loads(output), json.loads(expected_output))

  def test_get_best_hyperparameters_op_max(self):
    expected_output = [json.loads(hp) for hp in self._best_hp_max]

    output = GetBestHyperparametersOp.python_func(
        trials=self._trials_max, study_spec_metrics=self._metrics_spec_max
    )
    json_output = [json.loads(hp) for hp in output]

    self.assertEqual(json_output, expected_output)

  def test_get_best_trial_op_min(self):
    expected_output = self._best_trial_min

    output = GetBestTrialOp.python_func(
        trials=self._trials_min, study_spec_metrics=self._metrics_spec_min
    )

    self.assertEqual(json.loads(output), json.loads(expected_output))

  def test_get_best_hyperparameters_op_min(self):
    expected_output = [json.loads(hp) for hp in self._best_hp_min]

    output = GetBestHyperparametersOp.python_func(
        trials=self._trials_min, study_spec_metrics=self._metrics_spec_min
    )
    json_output = [json.loads(hp) for hp in output]

    self.assertEqual(json_output, expected_output)

  def test_get_hyperparameters_op(self):
    expected_output = [json.loads(hp) for hp in self._best_hp_max]

    output = GetHyperparametersOp.python_func(trial=self._best_trial_max)
    json_output = [json.loads(hp) for hp in output]

    self.assertEqual(json_output, expected_output)

  def test_get_worker_pool_specs_op(self):
    expected_output = [{
        'machine_spec': {
            'machine_type': 'n1-standard-4',
            'accelerator_type': 'NVIDIA_TESLA_T4',
            'accelerator_count': 1,
        },
        'replica_count': 1,
        'container_spec': {
            'image_uri': 'gcr.io/project_id/test',
            'args': [
                '--learning_rate=0.028',
                '--momentum=0.5',
                '--num_neurons=128.0',
            ],
        },
    }]

    output = GetWorkerPoolSpecsOp.python_func(
        best_hyperparameters=self._best_hp_max,
        worker_pool_specs=self._worker_pool_specs,
    )

    self.assertEqual(output, expected_output)

  def test_is_metric_beyond_threshold_op_maximize_above(self):
    trial = study.Trial({
        'id': '2',
        'final_measurement': {
            'metrics': [{
                'metric_id': 'accuracy',
                'value': 0.6,
            }]
        },
    })
    trial_json = study.Trial.to_json(trial)

    expected_output = 'true'

    output = IsMetricBeyondThresholdOp.python_func(
        trial=trial_json,
        study_spec_metrics=self._metrics_spec_max,
        threshold=0.5,
    )

    self.assertEqual(output, expected_output)

  def test_is_metric_beyond_threshold_op_maximize_below(self):
    trial = study.Trial({
        'id': '2',
        'final_measurement': {
            'metrics': [{
                'metric_id': 'accuracy',
                'value': 0.4,
            }]
        },
    })
    trial_json = study.Trial.to_json(trial)

    expected_output = 'false'

    output = IsMetricBeyondThresholdOp.python_func(
        trial=trial_json,
        study_spec_metrics=self._metrics_spec_max,
        threshold=0.5,
    )

    self.assertEqual(output, expected_output)

  def test_is_metric_beyond_threshold_op_minimize_above(self):
    trial = study.Trial({
        'id': '2',
        'final_measurement': {
            'metrics': [{
                'metric_id': 'loss',
                'value': 0.6,
            }]
        },
    })
    trial_json = study.Trial.to_json(trial)

    expected_output = 'false'

    output = IsMetricBeyondThresholdOp.python_func(
        trial=trial_json,
        study_spec_metrics=self._metrics_spec_min,
        threshold=0.5,
    )

    self.assertEqual(output, expected_output)

  def test_is_metric_beyond_threshold_op_minimize_below(self):
    trial = study.Trial({
        'id': '2',
        'final_measurement': {
            'metrics': [{
                'metric_id': 'loss',
                'value': 0.4,
            }]
        },
    })
    trial_json = study.Trial.to_json(trial)

    expected_output = 'true'

    output = IsMetricBeyondThresholdOp.python_func(
        trial=trial_json,
        study_spec_metrics=self._metrics_spec_min,
        threshold=0.5,
    )

    self.assertEqual(output, expected_output)

  def test_experimental_import_path(self):
    pass
