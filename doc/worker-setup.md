Remote Worker VM Setup
======================

Commands to setup remote worker on AWS Ubuntu machine

Install Python
--------------

See Ask Ubuntu [How do I install python 2.7.2 on Ubuntu?](http://askubuntu.com/questions/101591/how-do-i-install-python-2-7-2-on-ubuntu)

sudo apt-get update
sudo apt-get install build-essential checkinstall
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
tar -xvf Python-2.7.13.tgz
cd Python-2.7.13/
./configure
make
sudo checkinstall

Optinal Clenup:
cd ~
sudo rm -Rf Python-2.7.13*


Setup SCO
---------

sudo apt install virtualenv

mkdir sco
mkdir sco/src
mkdir sco/db
mkdir sco/db/data
mkdir sco/db/env
cd sco/db/env
scp -r heiko@cds-swg1.cims.nyu.edu:~/projects/sco/sco-datastore/resources/env/subjects .
cd ~/sco/src

### Install SCO Worker

pip install sco-datastore
pip install sco-engine
pip install sco-client
git clone https://github.com/heikomuller/sco-worker.git
cd sco-worker/scoworker
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python install -e .

### Install SCO Model

cd ~/sco/src/sco-worker
git clone https://github.com/WinawerLab/sco.git
cd sco
pip install -r requirements.txt
pip install -e .

python rabbitmq_worker.py -p "..." -h cds-swg1.cims.nyu.edu -s http://cds-swg1.cims.nyu.edu:5000/sco-server/api/v1 -e ../../../db/env/subjects/ -d ../../../db/data/
