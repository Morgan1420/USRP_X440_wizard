# Installation process

## Backend

'''
cd Backend
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
'''

If you don't have uhd do:

'''
sudo add-apt-repository ppa:ettusresearch/uhd
sudo apt-get update
sudo apt-get install libuhd-dev uhd-host
cd /usr/lib/uhd/utils
sudo cp uhd-usrp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
'''

You you should be able to run the code:

'''
python app.py
'''

A warning should appear because this is a development server, it's normal

Also you should have the backend port at 127.0.0.1:5000 (the output from the command should tell you)



## Frontend

go to directory and check if node is installed
'''
cd UI_vue
node -v
npm -v
'''

Install node if required using:
'''
curl -fsSL https://fnm.vercel.app/install | bash
source ~/.bashrc
fnm install --lts
node -v
npm -v
'''


Now you can:
'''
npm install
npm run dev
'''
