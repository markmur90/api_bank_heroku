#!/bin/bash

sudo apt-get update
sudo apt-get full-upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean
echo ""
echo "✅ Actualización 1 COMPLETA."
echo ""
echo ""
echo ""
sudo apt-get update
sudo apt-get full-upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean
echo ""
echo "✅ Actualización 2 COMPLETA."
echo ""
echo ""
echo ""
sudo ./01ufwNormal.sh
echo ""
echo "✅ UFW COMPLETA."
echo ""
echo ""
echo ""
sudo apt-get update && sudo apt-get install macchanger
chmod +x cambia_mac.sh
sudo ./cambia_mac.sh wlan0
echo ""
echo "✅ CAMBIO MAC COMPLETA."

