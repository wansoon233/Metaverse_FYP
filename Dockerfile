FROM python:3.12-slim

# 1. Install wget, git, and download EnergyPlus 24.1.0
RUN apt-get update && apt-get install -y wget git && \
    wget https://github.com/NREL/EnergyPlus/releases/download/v24.1.0/EnergyPlus-24.1.0-9d7789a3ac-Linux-Ubuntu22.04-x86_64.sh && \
    chmod +x EnergyPlus-24.1.0-9d7789a3ac-Linux-Ubuntu22.04-x86_64.sh && \
    echo "y" | ./EnergyPlus-24.1.0-9d7789a3ac-Linux-Ubuntu22.04-x86_64.sh && \
    rm EnergyPlus-24.1.0-9d7789a3ac-Linux-Ubuntu22.04-x86_64.sh

# 2. Set Environment Variables for Sinergym
ENV PYTHONPATH=/usr/local/EnergyPlus-24-1-0:$PYTHONPATH
ENV ENERGYPLUS=/usr/local/EnergyPlus-24-1-0
ENV EPLUS_PATH=/usr/local/EnergyPlus-24-1-0

WORKDIR /FYP_Metaverse

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN bash setup.sh

CMD ["/bin/bash"]
