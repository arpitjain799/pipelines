# This image has the script to kick off the ML pipeline sample e2e test,

FROM google/cloud-sdk:352.0.0

RUN apt-get update -y
RUN apt-get install --no-install-recommends -y -q libssl-dev libffi-dev wget ssh
RUN apt-get install --no-install-recommends -y -q default-jre default-jdk python3-setuptools python3.7-dev gcc libpython3.7-dev zlib1g-dev

RUN wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

COPY ./test/sample-test/requirements.txt /python/src/github.com/kubeflow/pipelines/test/sample-test/requirements.txt
RUN pip3 install -r /python/src/github.com/kubeflow/pipelines/test/sample-test/requirements.txt
# TODO: remove deprecated dependency
# COPY ./sdk/python/requirements-deprecated.txt /python/src/github.com/kubeflow/pipelines/sdk/python/requirements-deprecated.txt
# RUN pip3 install -r /python/src/github.com/kubeflow/pipelines/sdk/python/requirements-deprecated.txt
# Install python client, including DSL compiler.
# COPY ./sdk/python /sdk/python
# RUN pip3 install /sdk/python
RUN pip3 install kfp~=1.8

# Copy sample test and samples source code.
COPY ./test/sample-test /python/src/github.com/kubeflow/pipelines/test/sample-test
COPY ./samples /python/src/github.com/kubeflow/pipelines/samples
RUN cd /python/src/github.com/kubeflow/pipelines

# Downloading Argo CLI so that the samples are validated
ENV ARGO_VERSION v3.3.8
RUN curl -sLO https://github.com/argoproj/argo-workflows/releases/download/${ARGO_VERSION}/argo-linux-amd64.gz && \
  gunzip argo-linux-amd64.gz && \
  chmod +x argo-linux-amd64 && \
  mv ./argo-linux-amd64 /usr/local/bin/argo

ENTRYPOINT ["python3", "/python/src/github.com/kubeflow/pipelines/test/sample-test/sample_test_launcher.py"]
