# OMV

## Модели

Face ID на 14.10.19:
1. [modules/face_identification/model-weights/YOLO_Face.h5](https://drive.google.com/open?id=1oMw2gF0Q6JQy_4Sa6tMypBBQ4CEoD7eR)
1. [modules/face_identification/faceDetectorMobilenetSSD.pb](https://drive.google.com/open?id=1PnPqeV1mKr_OqnJNj8190MHCCMiRLSen)
1. [modules/face_identification/face_model.pkl](https://drive.google.com/open?id=1ZXzrZtdcPUNX4pByPv80Dos-bKZowVEg)
1. [modules/face_identification/fer2013_mini_XCEPTION.46-0.82.hdf5](https://drive.google.com/open?id=1k3DGVcm9MalWNmnYb6ijIjFjsrB2qQgS)

Object detector на 28.09.19:
1. [modules/object_detector/data/darknet_weights/yolov3.ckpt.index](https://drive.google.com/open?id=1sAvRsQ8XOT9rboUb54CA17OX7jyxtHNm)
1. [modules/object_detector/data/darknet_weights/yolov3.ckpt.meta](https://drive.google.com/open?id=1WFc9252CTsaycAEBvs0uLDTU5NXo0_61)
1. [modules/object_detector/data/darknet_weights/yolov3.ckpt.data-00000-of-00001](https://drive.google.com/open?id=1OrZVHms6iBZ47NTCTBxtjrVKSTsUGVAd)
1. [modules/hardhat_detector/data/hardhat-frcnn-frozen_inference_graph.pb](https://drive.google.com/open?id=1o0tJK8VnqQTvEBckLGba6LJBAsectQXM)
1. [modules/fire_detector/trained_graph.pb](https://drive.google.com/open?id=1IjOQNt9-uwI59wZo_SJCc1M1pvk_H7sc)
1. [modules/fire_detector/trained_graphDEFAULT.pb](https://drive.google.com/open?id=1kd7qxJAhWUXP7bR8HXkJMauyjt0yVys2)
1. [modules_helper/deep_sort_tracker_helper/model_data/mars-small128.pb](https://drive.google.com/open?id=1GQ3mxpgVqEsoIpqUvxsJFnRxVN2lWBpG)

## Полезные ссылки

### Датасет лиц:

1. [dataset](https://drive.google.com/open?id=1EpcCvKGJ7YpdqxY3M7jkaG9MM6CSAhjt)

### Камеры

1. camera4(HiWatch 4 Mp): `rtsp://admin:Admin123)@192.168.1.64:554/ISAPI/streaming/Channels/101`
1. camera5(HiWatch 4 Mp): `rtsp://admin:Admin123)@192.168.1.65:554/ISAPI/streaming/Channels/101`
1. Old(PST-IP102CP): `rtsp://192.168.1.204:554/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp?real_stream`
1. Omny купольная: `rtsp://admin:admin@192.168.1.66/`
1. Omny pro: `rtsp://admin:TriChizburgera3@192.168.1.2/`
1. Axis: `rtsp://192.168.1.69/axis-media/media.amp`
1. Omny bullet: `rtsp://admin:admin@192.168.1.67:554`

## Installation instruction  

pup

### Install NVIDIA drivers 410 with CUDA 10.0 and CUDNN 7.5. [Source](https://medium.com/repro-repo/install-cuda-10-1-and-cudnn-7-5-0-for-pytorch-on-ubuntu-18-04-lts-9b6124c44cc)

#### 0. Install nvidia-driver-410 from the graphics-drivers ppa
```
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt-get update
sudo apt-get install nvidia-driver-410
sudo reboot
```

##### Check installation with:
```
nvidia-smi
```

#### 1. Install CUDA 10.0.

##### Download the [CUDA .deb file](https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Linux&target_arch=x86_64&target_distro=Ubuntu&target_version=1804&target_type=deblocal)

##### To install:
```
sudo dpkg -i cuda-repo-ubuntu1804-10-0-local-10.0.130-410.48_1.0-1_amd64.deb
sudo apt-key add /var/cuda-repo-10-0-local-10.0.130-410.48/7fa2af80.pub
sudo apt-get update
sudo apt-get install cuda
sudo reboot
```

##### Add these two lines to the bottom of your ~/.bashrc to complete post-installation configuration:
```
sudo nano ~/.bashrc
```
```
# CUDA Config - ~/.bashrc
export PATH=/usr/local/cuda-10.0/bin:/usr/local/cuda-10.0/NsightCompute-1.0${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-10.0/lib64\
                        ${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
```

##### To apply this change, reload ~/.bashrc with:
```
source ~/.bashrc                         	
```

##### To verify CUDA installation:
```
cd /usr/local/cuda-10.0/samples
sudo make
```
```
/usr/local/cuda-10.0/samples/bin/x86_64/linux/release/deviceQuery
```



###### You should get something like:
```
/usr/local/cuda-10.0/samples/bin/x86_64/linux/release/deviceQuery Starting...
CUDA Device Query (Runtime API) version (CUDART static linking)
Detected 1 CUDA Capable device(s)
Device 0: "GeForce GTX 1060"
  CUDA Driver Version / Runtime Version          10.0 / 10.0
  CUDA Capability Major/Minor version number:    6.1
  Total amount of global memory:                 6078 MBytes (6373572608 bytes)
  (10) Multiprocessors, (128) CUDA Cores/MP:     1280 CUDA Cores
  GPU Max Clock rate:                            1671 MHz (1.67 GHz)
  Memory Clock rate:                             4004 Mhz
  Memory Bus Width:                              192-bit
  L2 Cache Size:                                 1572864 bytes
  Maximum Texture Dimension Size (x,y,z)         1D=(131072), 2D=(131072, 65536), 3D=(16384, 16384, 16384)
  Maximum Layered 1D Texture Size, (num) layers  1D=(32768), 2048 layers
  Maximum Layered 2D Texture Size, (num) layers  2D=(32768, 32768), 2048 layers
  Total amount of constant memory:               65536 bytes
  Total amount of shared memory per block:       49152 bytes
  Total number of registers available per block: 65536
  Warp size:                                     32
  Maximum number of threads per multiprocessor:  2048
  Maximum number of threads per block:           1024
  Max dimension size of a thread block (x,y,z): (1024, 1024, 64)
  Max dimension size of a grid size    (x,y,z): (2147483647, 65535, 65535)
  Maximum memory pitch:                          2147483647 bytes
  Texture alignment:                             512 bytes
  Concurrent copy and kernel execution:          Yes with 2 copy engine(s)
  Run time limit on kernels:                     Yes
  Integrated GPU sharing Host Memory:            No
  Support host page-locked memory mapping:       Yes
  Alignment requirement for Surfaces:            Yes
  Device has ECC support:                        Disabled
  Device supports Unified Addressing (UVA):      Yes
  Device supports Compute Preemption:            Yes
  Supports Cooperative Kernel Launch:            Yes
  Supports MultiDevice Co-op Kernel Launch:      Yes
  Device PCI Domain ID / Bus ID / location ID:   0 / 1 / 0
  Compute Mode:
     < Default (multiple host threads can use ::cudaSetDevice() with device simultaneously) >
deviceQuery, CUDA Driver = CUDART, CUDA Driver Version = 10.0, CUDA Runtime Version = 10.0, NumDevs = 1
Result = PASS
```

##### Just to make sure we’ve configured CUDA correctly, run a computation-based test:
```
/usr/local/cuda-10.0/samples/bin/x86_64/linux/release/matrixMulCUBLAS
```

#### 2. Install cuDNN 7.5.0

##### Go to the cuDNN download page -(https://developer.nvidia.com/rdp/cudnn-download) (need registration) and select the latest cuDNN 7.5.* version made for CUDA 10.0.

##### Download all 3 .deb files: the runtime library, the developer library, and the code samples library for Ubuntu 18.04.

##### In your download folder, install them in the same order:
```
sudo dpkg -i libcudnn7_7.5.0.56–1+cuda10.0_amd64.deb (the runtime library),
sudo dpkg -i libcudnn7-dev_7.5.0.56–1+cuda10.0_amd64.deb (the developer library), and
sudo dpkg -i libcudnn7-doc_7.5.0.56–1+cuda10.0_amd64.deb (the code samples).
```

##### Now we can verify the cuDNN installation (below is just the official guide, which surprisingly works out of the box):
```
cd /usr/src/cudnn_samples_v7/mnistCUDNN/.
sudo make clean && sudo make.
./mnistCUDNN. 
```

##### If your installation is successful, you should see Test passed! at the end of the output, like this:
```
cudnnGetVersion() : 7500 , CUDNN_VERSION from cudnn.h : 7500 (7.5.0)
Host compiler version : GCC 7.3.0
There are 1 CUDA capable devices on your machine :
device 0 : sms 10  Capabilities 6.1, SmClock 1670.5 Mhz, MemSize (Mb) 6078, MemClock 4004.0 Mhz, Ecc=0, boardGroupID=0
Using device 0
Testing single precision
Loading image data/one_28x28.pgm
Performing forward propagation ...
Testing cudnnGetConvolutionForwardAlgorithm ...
Fastest algorithm is Algo 1
Testing cudnnFindConvolutionForwardAlgorithm ...
^^^^ CUDNN_STATUS_SUCCESS for Algo 0: 0.014336 time requiring 0 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 1: 0.030304 time requiring 3464 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 2: 0.031744 time requiring 57600 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 4: 0.081920 time requiring 207360 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 7: 0.114688 time requiring 2057744 memory
Resulting weights from Softmax:
0.0000000 0.9999399 0.0000000 0.0000000 0.0000561 0.0000000 0.0000012 0.0000017 0.0000010 0.0000000 
Loading image data/three_28x28.pgm
Performing forward propagation ...
Resulting weights from Softmax:
0.0000000 0.0000000 0.0000000 0.9999288 0.0000000 0.0000711 0.0000000 0.0000000 0.0000000 0.0000000 
Loading image data/five_28x28.pgm
Performing forward propagation ...
Resulting weights from Softmax:
0.0000000 0.0000008 0.0000000 0.0000002 0.0000000 0.9999820 0.0000154 0.0000000 0.0000012 0.0000006
Result of classification: 1 3 5
Test passed!
Testing half precision (math in single precision)
Loading image data/one_28x28.pgm
Performing forward propagation ...
Testing cudnnGetConvolutionForwardAlgorithm ...
Fastest algorithm is Algo 1
Testing cudnnFindConvolutionForwardAlgorithm ...
^^^^ CUDNN_STATUS_SUCCESS for Algo 0: 0.016096 time requiring 0 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 1: 0.023552 time requiring 3464 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 2: 0.028672 time requiring 28800 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 4: 0.082944 time requiring 207360 memory
^^^^ CUDNN_STATUS_SUCCESS for Algo 7: 0.116736 time requiring 2057744 memory
Resulting weights from Softmax:
0.0000001 1.0000000 0.0000001 0.0000000 0.0000563 0.0000001 0.0000012 0.0000017 0.0000010 0.0000001 
Loading image data/three_28x28.pgm
Performing forward propagation ...
Resulting weights from Softmax:
0.0000000 0.0000000 0.0000000 1.0000000 0.0000000 0.0000714 0.0000000 0.0000000 0.0000000 0.0000000 
Loading image data/five_28x28.pgm
Performing forward propagation ...
Resulting weights from Softmax:
0.0000000 0.0000008 0.0000000 0.0000002 0.0000000 1.0000000 0.0000154 0.0000000 0.0000012 0.0000006
Result of classification: 1 3 5
Test passed!
```

### Docker

#### 3. Install Docker [Source](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

##### Update the apt package index:
```
sudo apt-get update
```

##### Install packages to allow apt to use a repository over HTTPS:
```
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
```

##### Add Docker’s official GPG key:
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

##### Use the following command to set up the stable repository:
```
sudo add-apt-repository \
  "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) \
  stable"
```

#### 4. Manage Docker as a non-root user

##### Create the docker group:
```
sudo groupadd docker
```
##### Add your user to the docker group:
```
sudo usermod -aG docker $USER
sudo reboot
```
##### Run the following command to activate the changes to groups:
```
newgrp docker
```
##### Verify that you can run docker commands without sudo:
```
docker run hello-world
```
   	
#### 5. Configure Docker to start on boot
```
sudo systemctl enable docker
```
   
### Configure Nvidia-Docker runtime [Source](https://github.com/NVIDIA/nvidia-container-runtime)

##### Install the repository for your distribution by following the instructions:
```
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | sudo tee
/etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | sudo apt-key add -
```

##### Install the nvidia-container-runtime package:
```
sudo apt-get install nvidia-container-runtime
```

##### Docker Engine setup:
```
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf <<EOF
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --host=fd:// --add-runtime=nvidia=/usr/bin/nvidia-container-runtime
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```
```
sudo tee /etc/docker/daemon.json <<EOF
{
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF
sudo pkill -SIGHUP dockerd
```

##### To check installation:
```
sudo docker run --rm ufoym/deepo nvidia-smi
```

### Всякое

1. [Содержимое репозитория до Великой чистки](https://drive.google.com/open?id=1aL3zPLPu17kXU6b3sTTFS09U3a3GrhNf)
