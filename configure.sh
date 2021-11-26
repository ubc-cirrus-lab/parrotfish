# This script sets some universal parameters.
# It should be run oly once.

# Installing some dependencies if needed
# sudo apt-get install -y moreutils
#sudo python3 -m pip install -r numpy requests_futures

# Configure path variables used by the platform
ROOTLINE='SPOT_ROOT="'$(echo $PWD)'"'
echo $ROOTLINE >> GenConfigs.py
# echo 'WSK_PATH = "'$(which wsk)'"' >> GenConfigs.py
echo 'AWS_PATH = "'$(which aws)'"' >> GenConfigs.py
# Configure root path
# echo $ROOTLINE | cat - invocation-scripts/monitoring.sh | sponge invocation-scripts/monitoring.sh
# echo $ROOTLINE | cat - monitoring/RuntimeMonitoring.sh | sponge monitoring/RuntimeMonitoring.sh

# Make local directories
# mkdir logs
# mkdir data_archive
