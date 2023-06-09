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
#
################################################################################

FROM gcr.io/oss-fuzz-base/base-builder@sha256:87ca1e9e19235e731fac8de8d1892ebe8d55caf18e7aa131346fc582a2034fdd

RUN apt-get update && \
    apt-get install -y \
        make autoconf automake libtool g++ sqlite3 pkg-config wget liblzma-dev

RUN git clone https://github.com/OSGeo/PROJ PROJ

RUN git clone https://github.com/curl/curl.git PROJ/curl && \
    git -C PROJ/curl checkout c12fb3ddaf48e709a7a4deaa55ec485e4df163ee

RUN git clone https://gitlab.com/libtiff/libtiff.git PROJ/libtiff && \
    git -C PROJ/libtiff checkout c8e1289deff3fa60ba833ccec6c030934b02c281

WORKDIR PROJ

COPY third_party/build.sh $SRC/
# This is to fix Fuzz Introspector build by using LLVM old pass manager
# re https://github.com/ossf/fuzz-introspector/issues/305
ENV OLD_LLVMPASS 1
