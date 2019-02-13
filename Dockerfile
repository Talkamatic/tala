FROM python:2.7-slim

# Run updates, install basics and cleanup
# - build-essential: Compile specific dependencies
# - git-core: Checkout git repos
RUN apt-get update -qq && apt-get install -y --no-install-recommends \\
  build-essential \\
  git-core \\
  libxml2-dev \\
  libmagic1 \\
  locales \\
  locales-all \\
  wget \\
  libxslt-dev&& \\
  apt-get upgrade -y && \\
  apt-get clean && \\
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#COPY requirements.txt .
#RUN pip install -r requirements.txt


ENV LANG C.UTF-8


RUN pip install --upgrade pip

RUN wget http://www.grammaticalframework.org/download/gf_3.8-1_amd64.deb && apt-get purge -y --auto-remove wget && dpkg -i gf_3.8-1_amd64.deb && rm gf_3.8-1_amd64.deb && mv /usr/lib/python2.7/dist-packages/pgf.so /usr/local/lib/python2.7/site-packages/pgf.so

COPY ./artifacts/dist/*.whl ./

RUN pip --no-cache-dir install *.whl

RUN rm -f *.whl