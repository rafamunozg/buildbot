# Based from the worker definition at https://github.com/buildbot/buildbot
# Agent will now include go, bazelisk, and gcloud
# buildbot/buildbot-worker

# please follow docker best practices
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/

# Provides a base Ubuntu (16.04) image with latest buildbot worker installed
# the worker image is not optimized for size, but rather uses ubuntu for wider package availability

FROM        ubuntu:16.04

# Last build date - this can be updated whenever there are security updates so
# that everything is rebuilt
ENV         security_updates_as_of 2019-08-28

# This will make apt-get install without question
ARG         DEBIAN_FRONTEND=noninteractive

# Install security updates and required packages
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install -q \
    build-essential \
    git \
    subversion \
    python3-dev \
    libffi-dev \
    libssl-dev \
    python3-setuptools \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    # Test runs produce a great quantity of dead grandchild processes.  In a
    # non-docker environment, these are automatically reaped by init (process 1),
    # so we need to simulate that here.  See https://github.com/Yelp/dumb-init
    curl https://github.com/Yelp/dumb-init/releases/download/v1.2.1/dumb-init_1.2.1_amd64.deb -Lo /tmp/init.deb && dpkg -i /tmp/init.deb &&\
    # ubuntu pip version has issues so we should use the official upstream version it: https://github.com/pypa/pip/pull/3287
    #apt-get install -y openjdk-8-jdk pkg-config zip g++ zlib1g-dev unzip bazel && \
    easy_install3 pip && \
    # Install required python packages, and twisted
    pip --no-cache-dir install 'twisted[tls]' && \
    mkdir /buildbot &&\
    useradd -ms /bin/bash buildbot &&\
    curl https://dl.google.com/go/go1.12.6.linux-amd64.tar.gz | tar -C /usr/local -xz && mkdir -p /usr/local/bazelisk

ENV PATH=$PATH:/usr/local/go/bin:/usr/local/bazelisk/bin
RUN GOPATH=/usr/local/bazelisk go get github.com/bazelbuild/bazelisk \
    && chown -R root:staff /usr/local/go \
    && chown -R root:staff /usr/local/bazelisk 

COPY . /usr/src/buildbot-worker
COPY docker/buildbot.tac /buildbot/buildbot.tac

RUN pip3 install /usr/src/buildbot-worker && \
    chown -R buildbot /buildbot

#Now gcloud
RUN curl https://sdk.cloud.google.com > /tmp/gcp-install.sh \
  && bash /tmp/gcp-install.sh --install-dir=/usr/local --disable-prompts \
  && chown -R root:staff /usr/local/google-cloud-sdk \
  && /usr/local/google-cloud-sdk/bin/gcloud components install --quiet kubectl beta alpha \
  && chown -R buildbot:buildbot /buildbot/.config
ENV PATH=$PATH:/usr/local/google-cloud-sdk/bin

USER buildbot
WORKDIR /buildbot

CMD ["/usr/bin/dumb-init", "twistd", "--pidfile=", "-ny", "buildbot.tac"]

