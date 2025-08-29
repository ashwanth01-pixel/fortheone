#!/bin/bash

# Exit on any error
set -e

sudo kubeadm init
echo "===== Updating system packages ====="
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv unzip curl apt-transport-https ca-certificates software-properties-common

echo "===== Installing Docker ====="
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc || true

# Install Docker
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group
sudo groupadd -f docker
sudo usermod -aG docker $USER
newgrp docker || true

echo "===== Setting up backend Flask environment ====="
cd ~/ashappa/backend

# Remove broken venv if exists
rm -rf venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found, installing Flask only"
    pip install flask
fi


echo "===== Setting up kubeconfig for current user ====="
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

echo "===== Deploying Weave Net pod network ====="
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml

echo "===== Untainting control-plane node so pods can run on it ====="
kubectl taint node $(hostname) node-role.kubernetes.io/control-plane:NoSchedule- || true

echo "===== Setup complete. Starting Flask app ====="
python3 app.py

