FROM python:3.11-slim

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
  build-essential \
  git-core \
  libxml2-dev \
  locales \
  locales-all \
  libxslt-dev&& \
  apt-get upgrade -y && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV LANG C.UTF-8

RUN pip install --upgrade pip

COPY ./requirements.txt ./
RUN pip --no-cache-dir install -r requirements.txt && rm -f requirements.txt

COPY ./*.whl ./
RUN pip --no-cache-dir install *.whl && rm -f *.whl
