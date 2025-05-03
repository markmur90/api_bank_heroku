#!/bin/bash
# UFW NORMAL

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 2222/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 5000/tcp
sudo ufw enable
