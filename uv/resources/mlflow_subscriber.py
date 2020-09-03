#!/usr/bin/env python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''This utility subscribes to a GCP pubsub topic to log mlflow metrics
to a backend server.
'''

import argparse
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message
import json
import logging
import mlflow as mlf
from mlflow.entities import Metric
import os
import sys
import time
import traceback

logging.basicConfig(level=logging.INFO)


def _parser():  # pragma: no cover
  parser = argparse.ArgumentParser(
      description='Subscriber for mlflow metric reporting.',
      prog='mlflow_subscriber',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )

  parser.add_argument(
      '--project',
      help='gcp project for pubsub subscription',
      required=True,
  )
  parser.add_argument(
      '--subscription',
      help='gcp pubsub subscription',
      required=True,
  )
  parser.add_argument(
      '--mlflow_uri',
      help='mlflow tracking uri',
      required=True,
  )
  parser.add_argument(
      '--verbose',
      action='store_true',
      help='verbose logging',
  )

  return parser


def _parse_flags(argv):  # pragma: no cover
  return _parser().parse_args(argv[1:])


def log_metrics(client: mlf.tracking.MlflowClient,
                msg: Message,
                verbose: bool = False):
  '''log received pubsub metrics message to mlflow backend'''
  try:
    if verbose:
      logging.info(f'received msg: {msg}')
    msg.ack()
    d = json.loads(msg.data.decode('utf-8'))
    if verbose:
      logging.info(f'{d}')
    run_id = d['run_id']
    metrics = [Metric(**x) for x in d['metrics']]
    client.log_batch(run_id=run_id, metrics=metrics)
  except Exception as e:
    logging.error(f'exception: {e}')
    logging.error(f'{traceback.format_exc()}')


def main():  # pragma: no cover
  args = _parse_flags(sys.argv)
  project = args.project
  subscription = args.subscription
  mlflow_uri = args.mlflow_uri

  client = mlf.tracking.MlflowClient(tracking_uri=mlflow_uri)
  subscriber = pubsub_v1.SubscriberClient()
  sub_path = subscriber.subscription_path(project, subscription)
  future = subscriber.subscribe(
      sub_path, callback=lambda msg: log_metrics(client, msg, args.verbose))

  with subscriber:
    try:
      future.result()
    except TimeoutError as e:
      future.cancel()


if __name__ == '__main__':  # pragma: no cover
  main()
