#!/bin/bash
# UFW DENY

sudo ufw default deny incoming
sudo ufw default deny outgoing
sudo ufw logging full
sudo ufw enable

sudo systemctl restart NetworkManager.service

sudo systemctl daemon-reload

sudo systemctl restart postgresql
sudo systemctl enable postgresql

sudo systemctl restart docker
sudo systemctl enable docker
