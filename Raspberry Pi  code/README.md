# Raspberry Pi code for webcam and media upload

This code allows for the Raspberry Pi to take a picture with a fisheye USB webcam, flattens the image, then uploads taken photos to a Google Service account

## Requirements

- Python 3.9+
- pip
- venv
- numpy
- fswebcam
- google-auth
- google-auth-oauthlib
- google-api-python-client
- opencv-python

# Installing virtual environment BEFORE DEPENDENCIES

(in the top directory)
sudo apt update
sudo apt install python3 python3-venv python3-pip -y

then,

python3 -m venv envi (creates venv named envi, which is name I use)

## Install dependencies

pip install google-auth google-auth-oauthlib google-api-python-client opencv-python numpy

OR (depending on setup)
sudo apt-get install fswebcam
pip3 install google-auth google-auth-oauthlib google-api-python-client opencv-python numpy

***** Save the code in the directory under the user. I.E. /home/PiName/serviceToDrive.py

# ServiceToDrive.py

Contains code that undistorts a warped image with results 
from calibrating the webcam (saves with line 28), and uploads photos from directory (line 43) 
to a service Google account. 

# Webcam.sh

Bash Script that takes a picture. This link
is good if you want to make your own Bash Script!

https://www-users.york.ac.uk/~mjf5/shed_cam/src/USB%20webcam.html 

# ServiceToDrive.sh

Activates the virtual enviroment (instead of doing it manually)
and executes serviceToDrive.py

# Crontab

Use Cron to run all the Bash Scripts, timing them. 
When you turn on the pi, simply type crontab -e in the terminal and 
add two crontabs, one first for webcam.sh (once per day), and second for serviceRun.sh 
(once per week)



