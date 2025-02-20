# Copyright 2022 The Kubeflow Authors. All Rights Reserved.
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

import json
import logging

import google.auth
import google.auth.transport.requests
from google_cloud_pipeline_components.container.v1.bigquery.utils import bigquery_util
from google_cloud_pipeline_components.container.v1.gcp_launcher.utils import artifact_util
from google_cloud_pipeline_components.types.artifact_types import BQMLModel
import requests


def bigquery_explain_predict_model_job(
    type,
    project,
    location,
    model_name,
    table_name,
    query_statement,
    top_k_features,
    threshold,
    payload,
    num_integral_steps,
    job_configuration_query_override,
    gcp_resources,
    executor_input,
):
  """Create and poll bigquery explain predict model job till it reaches a final state.

  This follows the typical launching logic:
  1. Read if the bigquery job already exists in gcp_resources
     - If already exists, jump to step 3 and poll the job status. This happens
     if the launcher container experienced unexpected termination, such as
     preemption
  2. Deserialize the payload into the job spec and create the bigquery job
  3. Poll the bigquery job status every
  job_remote_runner._POLLING_INTERVAL_IN_SECONDS seconds
     - If the bigquery job is succeeded, return succeeded
     - If the bigquery job is pending/running, continue polling the status

  Also retry on ConnectionError up to
  job_remote_runner._CONNECTION_ERROR_RETRY_LIMIT times during the poll.


  Args:
      type: BigQuery model explain predict job type.
      project: Project to launch the query job.
      location: location to launch the query job. For more details, see
        https://cloud.google.com/bigquery/docs/locations#specifying_your_location
      model_name: BigQuery ML model name for generating explanations. For more
        details, see
      https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#model_name
      table_name: BigQuery table id of the input table that contains the
        prediction data. For more details, see
        https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#table_name
      query_statement: query statement string used to generate the prediction
        data. For more details, see
        https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#query_statement
      top_k_features: This argument specifies how many top feature attribution
        pairs are generated per row of input data. The features are ranked by
        the absolute values of their attributions. For more details, see
        https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#top_k_features
      threshold: A custom threshold for the binary logistic regression model
        used as the cutoff between two labels. Predictions above the threshold
        are treated as positive prediction. Predictions below the threshold are
        negative predictions. For more details, see
        https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#threshold
      num_integral_steps: This argument specifies the number of steps to sample
        between the example being explained and its baseline for approximating
        the integral in integrated gradients attribution methods. For more
        details, see
        https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-explain-predict#num_integral_steps
      payload: A json serialized Job proto. For more details, see
        https://cloud.google.com/bigquery/docs/reference/rest/v2/Job
      job_configuration_query_override: A json serialized JobConfigurationQuery
        proto. For more details, see
        https://cloud.google.com/bigquery/docs/reference/rest/v2/Job#JobConfigurationQuery
      gcp_resources: File path for storing `gcp_resources` output parameter.
      executor_input: A json serialized pipeline executor input.
  """
  if not (not query_statement) ^ (not table_name):
    raise ValueError(
        'One and only one of query_statement and table_name should be '
        'populated for BigQuery explain predict model job.'
    )
  input_data_sql = (
      'TABLE %s' % bigquery_util.back_quoted_if_needed(table_name)
      if table_name
      else '(%s)' % query_statement
  )

  settings_field_sql_list = []
  if top_k_features is not None and top_k_features > 0:
    settings_field_sql_list.append('%s AS top_k_features' % top_k_features)

  if threshold is not None and threshold > 0.0 and threshold < 1.0:
    settings_field_sql_list.append('%s AS threshold' % threshold)

  if num_integral_steps is not None and num_integral_steps > 0:
    settings_field_sql_list.append(
        '%s AS num_integral_steps' % num_integral_steps
    )

  settings_field_sql = ','.join(settings_field_sql_list)
  settings_sql = ', STRUCT(%s)' % settings_field_sql

  job_configuration_query_override_json = json.loads(
      job_configuration_query_override, strict=False
  )
  job_configuration_query_override_json['query'] = (
      'SELECT * FROM ML.EXPLAIN_PREDICT(MODEL `%s`, %s%s)'
      % (model_name, input_data_sql, settings_sql)
  )

  # TODO(mingge): check if model is a valid BigQuery model resource.
  return bigquery_util.bigquery_query_job(
      type,
      project,
      location,
      payload,
      json.dumps(job_configuration_query_override_json),
      gcp_resources,
      executor_input,
  )
