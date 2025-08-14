#!/bin/bash
set -euo pipefail

# Update packages
sudo apt-get update

# ----------------------------
# Install Docker (official)
# ----------------------------
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# ----------------------------
# Set hostname to kmaster
# ----------------------------
sudo hostnamectl set-hostname kmaster

# ----------------------------
# Initialize Kubernetes cluster
# ----------------------------
sudo kubeadm init

# ----------------------------
# Configure kubectl for current user
# ----------------------------
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# ----------------------------
# Check the status of nodes
# ----------------------------
kubectl get nodes

# ----------------------------
# Apply Weave Net CNI plugin
# ----------------------------
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml

# ----------------------------
# Check taints on kmaster node
# ----------------------------
kubectl describe node kmaster | grep Taint

# ----------------------------
# Remove control-plane taint to allow scheduling pods on master
# ----------------------------
kubectl taint node kmaster node-role.kubernetes.io/control-plane:NoSchedule- || true
