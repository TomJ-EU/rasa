
# Rasa

I tried to deploy Rasa through Kubernetes.  
In this repository is what I got so far and how you can replicate what I did.  
Also the things I tried that didn't work.


## Prerequisites
Rasa, Docker, Docker-compose, Kubernetes and Minikube are necessary to run the project.  
The others are optional or only for recreating this yourself.
- Rasa
- Docker
- Docker-compose
- Kubernetes 
- Minikube
- Kompose
- Move2Kube
- Virtualbox

### Rasa
https://rasa.com/docs/rasa/installation/installing-rasa-open-source  
I recommend using Python 3.8 for Rasa (I personally used 3.8.10), even though it does now also seem to work with newer Python versions.

### Docker
https://docs.docker.com/desktop/install/windows-install/  
Follow the steps carefully.  
I used Ubuntu 20.04 for my WSL.

### Docker-compose
Comes with Docker desktop.

### Kubernetes
https://kubernetes.io/docs/tasks/tools/

### Minikube
https://minikube.sigs.k8s.io/docs/start/

### Kompose
https://kompose.io/installation/

### Move2Kube
https://move2kube.konveyor.io/installation/cli  
I just downloaded the binary directly: https://github.com/konveyor/move2kube/releases

### Virtualbox
https://www.virtualbox.org/wiki/Downloads
## Files

| Folder             | What it does                                                                |
| ----------------- | ------------------------------------------------------------------ |
| rasaDocker | runs Rasa in Docker |
| rasaDockerNoNginx | runs Rasa in Docker without an nginx container |
| rasaM2K | the Kubernetes cluster after moving RasaDocker from Docker-compose to Kubernetes using Move2Kube |
| rasaKompose | the Kubernetes cluster after moving RasaDocker from Docker-compose to Kubernetes using Kompose |
| rasaKomposeNoNginx | the Kubernetes cluster after moving RasaDockerNoNginx from Docker-compose to Kubernetes using Kompose |

## The project

### Start

I started with another github repo that I found:  
https://github.com/AmirStudy/Rasa_Deployment  
Follow the instructions on their github page.  
TLDR:  
`docker-compose up --build` and then go to http://localhost.

#### Changes

Make sure that at the top of the Dockerfile in frontend the correct version of Ubuntu (or whatever else you used) is mentioned.  
So for me I had to change it to `FROM ubuntu:20.04`

If you have any files you wish to have ignored add a .dockerignore file in the folder your Dockerfile resides in too.

With the project as it is now it will run rasa train every time we restart the backend container.  
If you want to use a pretrained model (and save time) you just need to add back in the models folder and add your model to it.  
Then delete `RUN rasa train` from the backend Dockerfile.  
You can then also remove `COPY ./data /app/data` and `VOLUME /app/data` if you wish and add the data folder to your .dockerignore or just straight up remove it.

I also made some small changes to the frontend and obviously my Rasa backend and action server are different.
### Database

After succesfully running Rasa from within Docker, we can now add a Database to it.  
I chose to use mySql as it has prebuilt Docker containers and is easy to use.  
1. Add a folder named `db` to your project
2. Add a Dockerfile to the `db` folder with the following:
```bash
  FROM mysql:latest
  COPY . /docker-entrypoint-initdb.d/
```
3. Add a .sql file to the `db` folder and put `use db;` at the top.
4. You can then add whatever tables and other stuff to the .sql file
5. Add the following to your `docker-compose.yml` file:
```bash
      mysql:
      container_name: "db"
      build:
        context: db
      restart: always
      environment:
        MYSQL_DATABASE: "db"
        MYSQL_ROOT_PASSWORD: 'password'
      ports:
        - "3306:3306"
```
6. Add `RUN pip install mysql-connector-python` to your Dockerfile in the `actions` folder below the already existing pip install command.  
And `import mysql.connector` in your `actions.py` file.
This is so you can connect to the database in your custom actions.  
Start your connection like this:
```bash
      conn = mysql.connector.connect(
            user='root',
            password='password',
            host='mysql',
            port='3306',
            database='db'
        )
        cur = conn.cursor(prepared=True)
```

We are now at the point of rasaDocker.
### Removing nginx

The project is quite small and simple so we could easily do without.  
I thought that maybe this was causing some of the problems I faced later, so decided removing it was worth a try.

1. Remove the `nginx.config` file
2. Remove the following from you `docker-compose.yml` file:
```bash
      nginx:
      container_name: "nginx"
      image: nginx
      volumes:
        - ./nginx.conf:/etc/nginx/nginx.conf
      restart: always
      ports:
        - 80:80
      depends_on: 
        - rasa
        - action-server
        - chatbotui
```
3. Works the same except that you have to go to http://localhost:3000.
  
  
We are now at the point of rasaDockerNoNginx
## Kompose

Now we need to change our Docker containers into a kubernetes cluster.  
The first thing I tried is something called Kompose,  
which can directly change your docker-compose file into kubernetes manifests.  
After downloading Kompose simply run:  
`kompose convert -f docker-compose.yml -o <output file>.yaml`  
Kompose is not perfect, so we have to make some changes,  
but first let's look at kubernetes
## kubectl

If you want to run kubernetes clusters locally, you're going to need some tools.  
I chose Minikube, since it's the most widely used.
After downloading Minikube you can run `minikube start`  
with the `--driver=<your driver>` flag you can decide which driver minikube uses.  
If you have just followed this tutorial so far, you should only have Docker available.  
So minikube will use that (make sure to open Docker Desktop first),  
otherwise just use `minikube start --driver=docker`.

After this you can get your manifests file, created in the previous step and apply it with  
`kubectl apply -f <your file>.yaml`,  
for this project (rasaKompose and rasaKomposeNoNginx) that is `kubectl apply -f kompose-manifests.yaml`


### Commands

| Command             | What it does                                                                |
| ----------------- | ------------------------------------------------------------------ |
| `kubectl apply -f <your file>.yaml` | runs a kubernetes cluster with the assinged file |
| `kubectl create namespace <name>` | creates a namespace, if you do this, make sure to put `--namespace <name>` after kubectl everytime you use a command if you want to use your namespace, |
|  | if not specified, kubectl will use the `default` namespace |
| `kubectl get pods` | shows all current kubernetes pods (in the `default` namespace) |
| `kubectl get svc` | shows all current services |
| `kubectl get all`| shows everything |
| `kubectl describe pod <podname>` | shows you details about the pod (handy for debugging) |
| `kubectl describe svc <servicename>`| shows you details about the service |
| `kubectl logs <podname>`| shows you the logs of a pod (also handy for debugging) |
| `kubectl delete --all deployments` | deletes all deployments |
| `kubectl delete --all svc` | deletes all services (used together with above command will delete everything in your namespace) | 

Now you can see that the pods are not running, due to some imagePullBackOff errors.  
This is because previously Docker knew where all our images were, but kubernetes does not know that.  
and needs to pull the image from somewhere  
You need to push your images to your docker hub repository and then pull them from there.  
This is done by doing `docker login -u <username> -p <password>`  
Then `docker tag <image name> <username>/<image name on docker hub>:<tag>`
You can choose whatever image name on docker hub you want,  
for the tag it is common to do a version number,  
if the tag is not specified it will default to the `latest` tag.  
If you always do this it will overwrite your previous pushes.  
To push do `docker push <username>/<image name on docker hub>:<tag>`  
Then change the image in the manifests to the one you pushed.  
In the rasaKompose and rasaKomposeNoNginx folders, you can see the images being pulled from my repository.

If images take too long to pull (I believe longer than 120 seconds) Kubernetes will think it can't be done,  
however it is not abnormal that an image is too big or network too bad that it simply takes longer.  
You can do `minikube ssh docker pull <image>` to pull it manually.

We are now at the point of rasaKomposeNoNginx

If you used the rasaDocker for your kubernetes cluster, one last change is needed.  
In the volume mounts of the nginx Deployments, kubernetes doesn't like it if you try mount a single file.  
So just add `subPath: nginx.conf` below
```bash
    - mountPath: /etc/nginx.conf
      name: nginx-claim0
```
like this
```bash
volumeMounts:
    - mountPath: /etc/nginx.conf
        name: nginx-claim0
        subPath: nginx.conf
```

We are now at the point of rasaKompose
## Problem

This is the point where I am stuck. All the pods and services are running.  
The problem is the communication between them doesn't work, and I can't reach them directly either.  

## Things I tried

Within a cluster, pods have their own cluster IP, however these pods may go down or be restarted  
and everytime that happens their IP changes, which is not handy.  
So instead every pod that needs to communicate has their own service,  
which does have a consistent IP, and you can reach the pod through that service.  
Reaching a service should be really straightforward from within the cluster:  
`http://<svc_name>`should do the trick.  
In this SO post: https://stackoverflow.com/questions/59558303/how-to-find-the-url-of-a-service-in-kubernetes  
some other options are also discussed (I tried all of them, and I couldn't get it to work)
### Move2Kube

I tried using M2K instead of Kompose to go from the docker-compose file to kubernetes manifests,  
but this gave me even more errors, when trying to run the pods and services.  
You can see the result in the rasaM2K file (includes nginx).  
So I didn't even manage to run all the pods and services individually there.
### Virtualbox

Another suggested fix would be to use a different driver for minikube.  
Docker can mess with the IP addresses of the cluster.  
The most stable driver is Virtualbox (although it is much, much slower than docker).  
The problem I faced when using this is that when running the backend pod (rasa)  
it told me that my hardware doesn't support AVX instructions, so that pod kept crashing.  
I checked with HWiNFO and Steam and both said my processor does support them, so idk.  
So this is where I got stuck for Virtualbox.

You can use the Virtualbox driver by first calling `minikube delete`.  
Then `minikube start --driver=virtualbox`.  
If this fails you can instead run `minkube start --driver=virtualbox --no-vtx-check=true`.  
After that just use the kubectl commands like you're used to, just be prepared for slowness.
### How to send requests

The frontend sends requests to the rasa server in the `send(message)` function.  
This can be found in `frontend` -> `static` -> `js` -> `script.js` -> ~line 145.  
Here you can change the url.
