FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    git \
    build-essential \
    libxext6 \
    libgl1 \
    libglx-mesa0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /FYP_Metaverse

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN bash setup.sh

CMD ["/bin/bash"]
