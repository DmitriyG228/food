## edit .ssh/config ip address
## open vscode and ssh to remote
## git clone ab
## make this  file executable with chmod +x build.sh edit and run
## copy ad_data to remote


# ## clean anaconda if exists also rm -r anaconda3
# conda install anaconda-clean
# anaconda-clean --yes

# sudo apt update && apt upgrade
# sudo apt install wget
# wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh
# chmod +x Anaconda3-2020.11-Linux-x86_64.sh
# ./Anaconda3-2020.11-Linux-x86_64.sh
# rm Anaconda3-2020.11-Linux-x86_64.sh

# export PATH="$HOME/anaconda3/bin:$PATH"
# alias python="$HOME/anaconda3/bin/python"

# ### docker 
#$ sudo apt-get update
# $ sudo apt-get install \
#     apt-transport-https \
#     ca-certificates \
#     curl \
#     gnupg-agent \
#     software-properties-common

# curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# sudo apt-key fingerprint 0EBFCD88
# sudo add-apt-repository \
#    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
#    $(lsb_release -cs) \
#    stable"

# sudo apt-get update
# sudo apt-get install docker-ce docker-ce-cli containerd.io
# apt-cache madison docker-ce
# sudo apt-get install docker-ce docker-ce-clicontainerd.io
# sudo docker run hello-world


# docker container postgis
docker pull postgres
sudo docker run --name psql_food_prod -e POSTGRES_PASSWORD=KJnbuiwuef89k -d -p 5434:5432 postgres


# github 
# sudo apt-get install git-core git-gui git-doc
# git config --global credential.helper store
# git config --global user.email "2280905@gmail.com"
# git config --global user.name "DmitriyG228"
# git clone https://github.com/DmitriyG228/ab

# # ### conda env
# conda init bash
conda env create
# conda env update --file environment.yml --prune
# source $HOME/anaconda3/etc/profile.d/conda.sh
# conda activate ab
# conda install ipykernel
# python -m ipykernel install --user --name ab
# python -m pip install -e $HOME/ab
# jupyter nbextension enable --py widgetsnbextension

# ### crontabcront
# crontab -ecc
# crontab -l | { cat; echo @reboot /bin/bash -c "cd $HOME; source ~/.bashrc; conda activate base; (jupyter lab --ip=0.0.0.0 --port=9996)"; } | crontab - 
# crontab -l | { cat; echo @reboot sudo docker start postgis; } | crontab -
# crontab -l | { cat; echo @reboot "conda activate ab; cd; cd ab/procs; python proc_app.py"; } | crontab -
# crontab -l | { cat; echo @reboot sudo $HOME/remount_data.sh; } | crontab -

# # ### jupyter
# conda activate
# jupyter-notebook --generate-config
# jupyter-notebook password
# conda install nodejs

# # ### plotly
# jupyter labextension install jupyterlab-plotly@4.14.1
# jupyter labextension install @jupyter-widgets/jupyterlab-manager plotlywidget@4.14.1

# ### ctop
# sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.5/ctop-0.7.5-linux-amd64 -O /usr/local/bin/ctop
# sudo chmod +x /usr/local/bin/ctop



### load db backup
## transfer backup
## unpack
# zstd -T0 -d dump_21-01-2021_15_51_08.sql.zst dump_21-01-2021_15_51_08.sql & 
## load backup
# cat dump_21-01-2021_15_51_08.sql | docker exec -i postgis psql -U postgres | ts '[%Y-%m-%d %H:%M:%S]' >> log.log & 
