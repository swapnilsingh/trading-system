#!/bin/bash

# Enable memory overcommit permanently for Redis
echo "🔧 Setting vm.overcommit_memory=1..."
grep -qxF 'vm.overcommit_memory=1' /etc/sysctl.conf || echo 'vm.overcommit_memory=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -w vm.overcommit_memory=1
echo "✅ Memory overcommit set. Current value: $(cat /proc/sys/vm/overcommit_memory)"
