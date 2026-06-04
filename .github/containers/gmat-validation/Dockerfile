FROM ubuntu:24.04

ARG GMAT_URL="https://sourceforge.net/projects/gmat/files/GMAT/GMAT-R2026a/gmat-ubuntu-x64-R2026a.tar.gz/download?use_mirror=autoselect"
ARG GMAT_SHA256="fe124b4a606b2e3b704a6fbb1c37b87598d5df0d18cb661c304b5f60074a7754"

ENV DEBIAN_FRONTEND=noninteractive
ENV GMAT_ROOT=/opt/gmat
ENV PATH="/opt/gmat/bin:${PATH}"
ENV LD_LIBRARY_PATH="/opt/gmat/bin:/opt/gmat/lib:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="/opt/gmat/bin:${PYTHONPATH}"

RUN useradd --create-home --shell /usr/sbin/nologin gmat

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libexpat1 \
    libgl1 \
    libglu1-mesa \
    libgomp1 \
    libgtk-3-0 \
    libice6 \
    libsm6 \
    libstdc++6 \
    libx11-6 \
    libxcb1 \
    libxcursor1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxinerama1 \
    libxmu6 \
    libxrandr2 \
    libxrender1 \
    libxt6 \
    libxxf86vm1 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p "${GMAT_ROOT}" /opt/gmat-validation \
    && curl --retry 5 --retry-all-errors --retry-delay 10 --connect-timeout 30 -fL "${GMAT_URL}" -o /tmp/gmat.tar.gz \
    && echo "${GMAT_SHA256}  /tmp/gmat.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/gmat.tar.gz -C "${GMAT_ROOT}" --strip-components=2 \
    && rm /tmp/gmat.tar.gz

COPY --chown=gmat:gmat self_check.py /opt/gmat-validation/self_check.py

RUN chown -R gmat:gmat "${GMAT_ROOT}" /opt/gmat-validation

USER gmat
WORKDIR /opt/gmat-validation
RUN python3 /opt/gmat-validation/self_check.py

CMD ["python3", "/opt/gmat-validation/self_check.py"]
