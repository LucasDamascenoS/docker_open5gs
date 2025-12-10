# Magma + 4G/5G Simulator Setup Guide

This setup uses three Virtual Machines in **VirtualBox**:

- **Orchestrator:** Ubuntu 22.04 with 4GB of RAM, 4 CPUs, 30GB of storage, and 2 network adapters (NAT and Host-only Adapter).
- **AGW:** Ubuntu 20.04 with 4GB of RAM, 4 CPUs, 15GB of storage, and 2 network adapters (NAT and Host-only Adapter).
- **Simulator:** Ubuntu 22.04 with 4GB of RAM, 4 CPUs, 30GB of storage, and 2 network adapters (NAT and Host-only Adapter).

## 1. 💻 Orchestrator Setup

1. After complete the installation, update and upgrade the Virtual Machine:

    ~~~bash
    sudo apt update && sudo apt upgrade -y
    ~~~

2. Install Docker and Docker Compose:

    ~~~bash
    # Uninstall all conflicting packages:
    sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)

    # Add Docker's official GPG key:
    sudo apt update
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
    Types: deb
    URIs: https://download.docker.com/linux/ubuntu
    Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
    Components: stable
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF

    sudo apt update

    # Install the Docker packages:
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Create a link for the legacy docker-compose
    sudo ln /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose
    ~~~

3. Clone the magma repository:

    ~~~bash
    sudo su -
    git clone https://github.com/magma/magma.git
    cd magma
    git checkout v1.9
    ~~~

4. Build the Orchestrator containers:

    ~~~bash
    cd ~/magma/orc8r/cloud/docker
    ./build.py --all
    ~~~

5. Build the NMS containers:

    ~~~bash
    cd ~/magma/nms
    COMPOSE_PROJECT_NAME=magmalte docker-compose build magmalte
    ~~~

6. Run the Orchestrator:

    ~~~bash
    cd ~/magma/orc8r/cloud/docker
    ./run.py --metrics
    ~~~

7. Run the NMS GUI:

    ~~~bash
    cd ~/magma/nms
    docker-compose up -d
    docker-compose ps
    ~~~

    - ⚠️ If the `nms-nginx-proxy-1` container starts but then exits, you may need to update the `proxy_ssl.conf` file:

        ~~~bash
        cd ~/magma/nms
        
        cat << 'EOF' | tee ./docker/docker_ssl_proxy/proxy_ssl.conf
        server {
        listen 443 ssl;
        ssl_certificate /etc/nginx/conf.d/cert.pem;
        ssl_certificate_key /etc/nginx/conf.d/key.pem;
        location / {
        proxy_pass http://magmalte:8081;
        proxy_set_header Host $http_host;
        }
        }
        EOF
        
        docker-compose up -d --force-recreate
        docker-compose ps
        ~~~

8. Provision the Demo data:

    ~~~bash
    cd ~/magma/nms
    ./scripts/dev_setup.sh
    ~~~

9. Verify that the certificates have been generated:

    ~~~bash
    ls -ltr ~/magma/.cache/test_certs
    more ~/magma/.cache/test_certs/rootCA.pem
    ~~~

10. Connecting to the Orchestrator and Setting Up a Network:

    - Modify the hosts file in the host machine:

        - Add the IP address of the newly created Orchestrator to your `hosts` file in the host machine (change the IP address with the IP of **Host-only Adapter** interface of your machine running the Orchestrator):

            ~~~bash
            vi /etc/hosts

            # Add the following line then save and exit
            xxx.xxx.xxx.xxx magma-test.magma.test
            ~~~
    
        - Open a browser and navigate to:

            ~~~
            https://magma-test.magma.tes

            username: admin@magma.test
            password: password1234
            ~~~

        - Create new Network:

            - Follow the instructions at the link below:

                > ➡️ https://youtu.be/_nQSmbjAL70?si=N9iXdwo4FW9DQmjT&t=3014

        - Create new APN:

            - Follow the instructions at the link below:

                > ➡️ https://youtu.be/_nQSmbjAL70?si=FMoGr7wxijvMqy1g&t=3117

        - Create new Subscriber:

            - Follow the instructions at the link below:

                > ➡️ https://youtu.be/_nQSmbjAL70?si=QETI3B8nSvg_LYfe&t=3200

                | Field | Value |
                |------|-------|
                | IMSI | IMSI001010000000001 |
                | Subscriber Name | 001010000000001 |
                | Auth Key | 00112233445566778899aabbccddeeff |
                | Auth OPC | 63BFA50EE6523365FF14C1F45F88737D |
                | Service | ACTIVE |
                | Data Plan | default |
                | Active APNs | internet |

11. Enable 5G:

    - Navigate to the **Network** tab.
    - Under the **EPC** section, click on the `Edit` button.
    - Switch on the `Enable 5G Features` and save the configuration.

12. Utility Commands:

    - ℹ️ Containers Stop/Start Sequence After Starting the Orchestrator Virtual Machine:
        
        ~~~bash
        sudo su -

        cd ~/magma/nms
        docker-compose stop

        cd ~/magma/orc8r/cloud/docker
        docker-compose stop; sleep 30; docker-compose start;

        cd ~/magma/nms
        docker-compose start
        ~~~

## 2. 💻 AGW Setup

1. After complete the installation, update and upgrade the Virtual Machine:

    ~~~bash
    sudo apt update && sudo apt upgrade -y
    ~~~

2. Configure the GRUB:

    - Open and edit the file:

        ~~~bash
        sudo su -

        vi /etc/default/grub
        
        # Modify the following line then save and exit
        GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0"
        ~~~
    
    - Update the GRUB configuration and reboot the virtual machine:

        ~~~bash
        update-grub

        reboot
        ~~~

3. Configure the netplan:

    - Open the file:

        ~~~bash
        sudo su -

        vi /etc/netplan/00-installer-config.yaml
        ~~~
    
    - Edit the file:

        ~~~bash
        # From
        network:
          ethernets:
            enp0s3:
              dhcp4: true
            enp0s8:
              dhcp4: true
          version: 2

        # To
        network:
          ethernets:
            eth0:
              dhcp4: true
            eth1:
              dhcp4: true
          version: 2
        ~~~
    
    - Apply the netplan:
        ~~~bash
        netplan apply
        ~~~

4. Install necessary packages:

    ~~~bash
    sudo su -

    apt update && apt install python3-pip tshark tmux -y
    ~~~

5. Create magma user and login:

    - Use the following command to add the magma user:
        
        ~~~bash
        adduser magma
        ~~~

    - Use magma as password and leave the other fields blank.

    - Add magma to the sudo group:

        ~~~bash
        usermod -aG sudo magma
        ~~~

    - Allow magma to switch to root with no password:

        ~~~bash
        echo "
        # Magma user can access with no password
        magma ALL=(ALL) NOPASSWD:ALL
        " > /etc/sudoers.d/50-magma-users
        ~~~

    - Switch to magma user:

        ~~~bash
        su - magma
        ~~~

6. Edit the `rootCA` which you have obtained with `more ~/magma/.cache/test_certs/rootCA.pem`from the orchestrator:

    ~~~bash
    sudo su -

    mkdir -p /var/opt/magma/certs
    vi /var/opt/magma/certs/rootCA.pem
    ~~~

7. Edit the `/etc/hosts` (change the IP address with the IP of **Host-only Adapter** interface of your machine running the Orchestrator):

    ~~~bash
    vi /etc/hosts

    # Add the following line then save and exit
    xxx.xxx.xxx.xxx controller.magma.test bootstrapper-controller.magma.test fluentd.magma.test
    ~~~

8. Add the configuration of the `control_proxy`:

    ~~~bash
    mkdir -p /var/opt/magma/configs/

    cat << EOF | sudo tee /var/opt/magma/configs/control_proxy.yml
    cloud_address: controller.magma.test
    bootstrap_address: bootstrapper-controller.magma.test
    fluentd_address: fluentd.magma.test
    fluentd_port: 24224

    rootca_cert: /var/opt/magma/certs/rootCA.pem
    EOF
    ~~~

9. Get the installation script:

    ~~~bash
    wget https://github.com/magma/magma/raw/v1.8/lte/gateway/deploy/agw_install_docker.sh
    ~~~

10. Configure APT to not do GPG validation:

    ~~~bash
    echo "Acquire::AllowInsecureRepositories true;" > /etc/apt/apt.conf.d/99AllowInsecureRepositories

    echo "APT::Get::AllowUnauthenticated true;" >> /etc/apt/apt.conf.d/99AllowInsecureRepositories

    apt update
    ~~~

11. Modify the installation script:

    - Open the script file:

        ~~~bash
        vi agw_install_docker.sh
        ~~~

    - Insert the following lines after the `git checkout` and save:

        ~~~bash
        # Path to the Ansible task file
        TASK_FILE="/opt/magma/lte/gateway/deploy/roles/magma_deploy/tasks/main.yml"
        
        # Comment out the block for unvalidated apt signing key
        sed -i '/- name: Add unvalidated Apt signing key/,/ˆ$/ s/ˆ/#/' "$TASK_FILE"
        ~~~

12. Run the script and reboot the virtual machine after complete:

    ~~~bash
    bash agw_install_docker.sh
    ~~~

13. After reboot, make sure the containers are up and running:

    ~~~bash
    sudo su -

    cd /var/opt/magma/docker

    docker-compose ps
    ~~~

14. Integrate with the Orchestrator:

    - Get the gateway serial number:

        ~~~bash
        docker exec magmad show_gateway_info.py
        ~~~

    - Create AGW in the Orchestrator:

        - Follow the instructions at the link below:

            > ➡️ https://youtu.be/_nQSmbjAL70?si=IRQBsPmA1LYYv4t4&t=6297

    - The AGW will be created on the Orchestrator with a **Bad** healthy.
    
    - Recreate the containers inside the AGW:

        ~~~bash
        docker-compose up -d --force-recreate
        ~~~

    - After 2 minutes, the AGW status will change to **Good** in the Orchestrator.

    - Restart the containers to get the last configurations:

        ~~~bash
        docker-compose up -d --force-recreate
        ~~~

15. Upgrade Version:

    - Open and edit the `env` file:

        ~~~bash
        vi .env
        ~~~

    - Change the `IMAGE_VERSION` variable:

        ~~~bash
        # From
        IMAGE_VERSION=1.8.0

        # To
        IMAGE_VERSION=1.9.0
        ~~~

    - Pull the new image and start the containers correctly:

        ~~~bash
        docker-compose pull; sleep 120; docker-compose down; sleep 30; docker-compose up -d; sleep 120; docker-compose stop; sleep 30; docker-compose up -d;
        ~~~

    - Check if the containers are running with the new version:

        ~~~bash
        docker ps
        ~~~

16. Verify if 5G is enabled:

    - To ensure your gNB can connect, verify that the required SCTP ports are listening:

        ~~~bash
        ss -lpn | grep sctp
        ~~~

    - A successful output should look similar to this:

        ~~~bash
        u_str   LISTEN	  0	  4096	  ///tmp/sctpd_downstream.sock 99166	  * 0	  users:(("sctpd",pid=12422,fd=7))
        u_str   LISTEN	  0	  4096	  ///tmp/sctpd_upstream.sock 106529	  * 0	  users:(("oai_mme",pid=12514,fd=130))
        sctp    LISTEN	  0	  5	  [::ffff:192.168.123.25]:36412		  *:*	  users:(("sctpd",pid=12422,fd=15))
        sctp    LISTEN	  0	  5	  [::ffff:192.168.123.25]:38412		  *:*	  users:(("sctpd",pid=12422,fd=17))
        ~~~
    
    - If the ports are missing, reboot the AGW and restart the containers properly:

        ~~~bash
        cd /var/opt/magma/docker

        docker-compose down; sleep 30; docker-compose up -d; sleep 120; docker-compose stop; sleep 30; docker-compose up -d;
        ~~~

17. Optional Tools:

    - 🛠️ **Monitor:** tmux windows to perform sensitive tasks (mostly used in production environments).

        ~~~bash
        cat << 'EOF' | sudo tee monitor.sh
        if ! [[ -n "${TMUX}" || "${TERM}" =~ "tmux.*" || "${TERM}" =~ "screen.*" ]]; then

          monitor_sess="monitor"

          tmux has-session -t $monitor_sess 2>/dev/null

          if [ $? != 0 ]; then
            tmux new-session -d -t "monitor" -s $monitor_sess
            tmux rename-window S1AP
            tmux send-keys C-z 'tshark -t u -i eth1 sctp' Enter
            tmux split
            tmux send-keys C-z 'docker exec -ti magmad mobility_cli.py get_subscriber_table' Enter
            tmux split -c /var/opt/magma/docker
            tmux select-layout tiled
            tmux new-window -d -n VTYsh
            tmux send-keys -t VTYsh C-z 'vtysh' Enter
            tmux new-window -d -n pingall
            tmux new-window -d -n work
          fi

          tmux attach-session -t $monitor_sess
        fi
        EOF
        ~~~

        ~~~bash
        chmod +x monitor.sh

        ./monitor.sh
        ~~~
    
    - 🛠️ **Fresh Start:** script to clean the AGW's context and restart the containers (should be executed from the `monitor`).

        ~~~bash
        cat << EOF | sudo tee fresh_start.sh
        docker-compose stop
        docker rm redis
        ovs-ofctl del-flows gtp_br0
        tc qdisc del dev gtpu_sys_2152 root
        tc qdisc del dev eth0 root
        tc qdisc del dev eth1 root
        sleep 30
        docker-compose up -d
        EOF
        ~~~

        ~~~bash
        chmod +x fresh_start.sh

        # From the monitor
        ~/fresh_start.sh
        ~~~

## 3. 💻 Simulator Setup

### ⚙️ Docker srsRAN Setup (4G)

1. After complete the installation, update and upgrade the Virtual Machine:

    ~~~bash
    sudo apt update && sudo apt upgrade -y
    ~~~

2. Install Docker and Docker Compose:

    ~~~bash
    # Uninstall all conflicting packages:
    sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)

    # Add Docker's official GPG key:
    sudo apt update
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
    Types: deb
    URIs: https://download.docker.com/linux/ubuntu
    Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
    Components: stable
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF

    sudo apt update

    # Install the Docker packages:
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Create a link for the legacy docker-compose
    sudo ln /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose

    # Allow run Docker without sudo
    sudo groupadd docker || true
    sudo usermod -aG docker $USER
    newgrp docker
    sudo reboot
    ~~~

3. Clone the Open5GS repository:

    ~~~bash
    git clone https://github.com/LucasDamascenoS/docker_open5gs.git

    cd docker_open5gs

    git checkout sim-env
    ~~~

4. Edit the `.env` file:
    - Set `DOCKER_HOST_IP` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.
    - Set `MME_IP` to the IP address of the **Host-only Adapter** interface of your **AGW** Virtual Machine.
    - Set `SRS_ENB_IP` and `SRS_UE_IP` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.

5. Build the Docker image:

    ~~~bash
    cd srslte/

    docker build --no-cache --force-rm -t docker_srslte .
    ~~~

6. Deploy the eNB:

    ~~~bash
    cd ~/docker_open5gs

    docker compose -f srsenb_zmq.yaml up -d && docker container attach srsenb_zmq
    ~~~

7. Deploy the UE:

    ~~~bash
    cd ~/docker_open5gs

    docker compose -f srsue_zmq.yaml up -d && docker container attach srsue_zmq
    ~~~

8. Test Traffic:
   
    If you want to manually utilize the interface, just bind your TCP/IP socket to `uesimtunX` interface.

    ~~~bash
    ping -I tun_srsue google.com
    ~~~

### ⚙️ Docker UERANSIM Setup (5G)

> 💡 This setup uses the Docker-based UERANSIM images and is recommended for simple or single-UE testing.

> 💡 If you need to run multiple UEs or perform load testing, refer to the [Source UERANSIM Setup](#source-ueransim-setup-5g).

1. After complete the installation, update and upgrade the Virtual Machine:

    ~~~bash
    sudo apt update && sudo apt upgrade -y
    ~~~

2. Install Docker and Docker Compose:

    ~~~bash
    # Uninstall all conflicting packages:
    sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)

    # Add Docker's official GPG key:
    sudo apt update
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
    Types: deb
    URIs: https://download.docker.com/linux/ubuntu
    Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
    Components: stable
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF

    sudo apt update

    # Install the Docker packages:
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Create a link for the legacy docker-compose
    sudo ln /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose

    # Allow run Docker without sudo
    sudo groupadd docker || true
    sudo usermod -aG docker $USER
    newgrp docker
    sudo reboot
    ~~~

3. Clone the Open5GS repository:

    ~~~bash
    git clone https://github.com/LucasDamascenoS/docker_open5gs.git

    cd docker_open5gs

    git checkout sim-env
    ~~~

4. Edit the `.env` file:
    - Set `DOCKER_HOST_IP` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.
    - Set `AMF_IP` to the IP address of the **Host-only Adapter** interface of your **AGW** Virtual Machine.
    - Set `NR_GNB_IP` and `NR_UE_IP` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.

5. Build the Docker image:

    ~~~bash
    cd ueransim/

    docker build --no-cache --force-rm -t docker_ueransim .
    ~~~

6. Deploy the gNB:

    ~~~bash
    cd ~/docker_open5gs

    docker compose -f nr-gnb.yaml up -d && docker container attach nr_gnb
    ~~~

7. Deploy the UE:

    ~~~bash
    cd ~/docker_open5gs

    docker compose -f nr-ue.yaml up -d && docker container attach nr_ue
    ~~~

8. Test Traffic:
   
    If you want to manually utilize the interface, just bind your TCP/IP socket to `uesimtunX` interface.

    ~~~bash
    ping -I uesimtun0 google.com
    ~~~

### ⚙️ Source UERANSIM Setup (5G)

> 💡 This setup builds UERANSIM from source and is recommended for multi-UE or load testing.

> 💡 If you only need to connect a single UE for basic testing, refer to the [Docker UERANSIM Setup](#docker-ueransim-setup-5g).

> ℹ️ Please refer to the [UERANSIM](https://github.com/aligungr/UERANSIM) repository for more information.

1. After complete the installation, update and upgrade the Virtual Machine:

    ~~~bash
    sudo apt update && sudo apt upgrade -y
    ~~~

2. Install OS Dependencies:

    ~~~bash
    sudo apt update
    sudo apt upgrade
    ~~~

    ~~~bash
    sudo apt install make
    sudo apt install gcc
    sudo apt install g++
    sudo apt install libsctp-dev lksctp-tools
    sudo apt install iproute2
    sudo snap install cmake --classic
    ~~~

    > ℹ️ Don't install cmake with `sudo apt-get install cmake`, because it installs very old version of cmake by default.

3. Clone the UERANSIM Repository:

    ~~~bash
    git clone https://github.com/aligungr/UERANSIM

    cd ~/UERANSIM

    git checkout tags/v3.2.6
    ~~~

4. Build the UERANSIM:

    ~~~bash
    make
    ~~~

5. Edit the `~/UERANSIM/config/magma-gnb.yaml` file:
    - Set `mcc` to `'001'` and `mnc` to `'01'`.
    - Set `linkIp`, `ngapIp` and `gtpIp` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.
    - Set `address` under `amfConfigs` section to the IP address of the **Host-only Adapter** interface of your **AGW** Virtual Machine.
    - Add `sd: 0xffffff` under `slices` section.

    Your `~/UERANSIM/config/magma-gnb.yaml` file should look like this:
   
    ~~~yml
    mcc: '001'          # Mobile Country Code value
    mnc: '01'           # Mobile Network Code value (2 or 3 digits)

    nci: '0x000000010'  # NR Cell Identity (36-bit)
    idLength: 32        # NR gNB ID length in bits [22...32]
    tac: 1              # Tracking Area Code

    linkIp: <gNB_IP>   # gNB's local IP address for Radio Link Simulation (Usually same with local IP)
    ngapIp: <gNB_IP>   # gNB's local IP address for N2 Interface (Usually same with local IP)
    gtpIp: <gNB_IP>    # gNB's local IP address for N3 Interface (Usually same with local IP)

    # List of AMF address information
    amfConfigs:
    - address: <AMF_IP>
        port: 38412

    # List of supported S-NSSAIs by this gNB
    slices:
    - sst: 1
      sd: 0xffffff

    # Indicates whether or not SCTP stream number errors should be ignored.
    ignoreStreamIds: true
    ~~~

6. Edit the `~/UERANSIM/config/magma-ue.yaml` file:
    - Set `supi` to the first subscriber IMSI on your DB.
    - Set `mcc` to `'001'` and `mnc` to `'01'`.
    - Remove the `protectionScheme`, `homeNetworkPublicKey`, `homeNetworkPublicKeyId` and `routingIndicator` fields.
    - Set `key` and `op` to the corresponding values that you configured for the subscriber.
    - Remove the `tunNetmask` field.
    - Set the `gnbSearchList` to the IP address of the **Host-only Adapter** interface of your **Simulator** Virtual Machine.
    - Add `sd: 0xffffff` under `sessions` section.
    - Add `sd: 0xffffff` under `configured-nssai` section.
    - Set `sd: 0xffffff` under `default-nssai` section.

    Your `~/UERANSIM/config/magma-ue.yaml` file should look like this:

    ~~~yml
    # IMSI number of the UE. IMSI = [MCC|MNC|MSISDN] (In total 15 digits)
    supi: 'imsi-001010000000001'
    # Mobile Country Code value of HPLMN
    mcc: '001'
    # Mobile Network Code value of HPLMN (2 or 3 digits)
    mnc: '01'

    # Permanent subscription key
    key: '00112233445566778899aabbccddeeff'
    # Operator code (OP or OPC) of the UE
    op: '63BFA50EE6523365FF14C1F45F88737D'
    # This value specifies the OP type and it can be either 'OP' or 'OPC'
    opType: 'OPC'
    # Authentication Management Field (AMF) value
    amf: '8000'
    # IMEI number of the device. It is used if no SUPI is provided
    imei: '356938035643803'
    # IMEISV number of the device. It is used if no SUPI and IMEI is provided
    imeiSv: '4370816125816151'

    # List of gNB IP addresses for Radio Link Simulation
    gnbSearchList:
      - <gNB_IP>

    # UAC Access Identities Configuration
    uacAic:
      mps: false
      mcs: false

    # UAC Access Control Class
    uacAcc:
      normalClass: 0
      class11: false
      class12: false
      class13: false
      class14: false
      class15: false

    # Initial PDU sessions to be established
    sessions:
      - type: 'IPv4'
        apn: 'internet'
        slice:
          sst: 1
          sd: 0xffffff

    # Configured NSSAI for this UE by HPLMN
    configured-nssai:
      - sst: 1
        sd: 0xffffff

    # Default Configured NSSAI for this UE
    default-nssai:
      - sst: 1
        sd: 0xffffff

    # Supported integrity algorithms by this UE
    integrity:
      IA1: true
      IA2: true
      IA3: true

    # Supported encryption algorithms by this UE
    ciphering:
      EA1: true
      EA2: true
      EA3: true

    # Integrity protection maximum data rate for user plane
    integrityMaxRate:
      uplink: 'full'
      downlink: 'full'
    ~~~

7. Start the gNB:

    ~~~bash
    cd ~/UERANSIM/build

    ./nr-gnb -c ../config/magma-gnb.yaml
    ~~~

8. Start the UE:

    - To start 1 UE, use the command:
   
        ~~~bash
        cd ~/UERANSIM/build

        sudo ./nr-ue -c ../config/magma-ue.yaml
        ~~~

    - To start 10 UEs, use the command:

        ~~~bash
        cd ~/UERANSIM/build

        sudo ./nr-ue -c ../config/magma-ue.yaml -n 10
        ~~~

        > ℹ️ IMSI number is incremented by one for each of the UEs (starting from the IMSI specified in the `magma-ue.yaml` file).

9. Test Traffic:
   
    If you want to manually utilize the interface, just bind your TCP/IP socket to `uesimtunX` interface.

    ~~~bash
    ping -I uesimtun0 google.com
    ~~~

## 4. ❗ Troubleshooting

1. 🔧 **Not able to create more than 1024 TUN interfaces with UERANSIM:**

    - By default, the maximum number of `uesimtun` interfaces that UERANSIM can create is 1024, although you can connect an unlimited number of UEs (limited only by hardware capacity).
    
    - When trying to create more than 1024 `uesimtun` interfaces, `nr-ue` prints the following error:
         
        ~~~bash
        [2025-12-02 14:04:46.158] [001010000001040|app] [error] TUN allocation failure [TUN interface name could not be allocated. Succcess]
        ~~~

    - To fix this, modify the `MAX_INTERFACE_COUNT` variable inside `~/UERANSIM/src/ue/tun/config.cpp`:
         
        ~~~C
        // From
        #define MAX_INTERFACE_COUNT 1024

        // To
        #define MAX_INTERFACE_COUNT <number>
        ~~~

    - Then rebuild UERANSIM:
         
        ~~~bash
        cd ~/UERANSIM

        make clean

        make
        ~~~

2. 🐞 **Unable to ping the internet with UERANSIM:**

    - After a successful gNB and UE attach to the AGW, a PDU session is established and a TUN interface is created with an assigned IP address.

    - When testing connectivity using `ping -I uesimtun0 google.com`, no responses are received.

    - To resolve this issue, follow the steps below:

        1. Ensure that you are using **UERANSIM v3.2.6**.
        
        2. Verify that there are no errors in the `ovs-vsctl show` output.
        
        3. Check whether the session entries exist in the flow tables:

            ~~~bash
            sudo ovs-ofctl -O OpenFlow13 dump-flows gtp_br0 table=0

            sudo ovs-ofctl -O OpenFlow13 dump-flows gtp_br0 table=12

            sudo ovs-ofctl -O OpenFlow13 dump-flows gtp_br0 table=13
            ~~~
        
        4. If everything appears correct, then this is a known bug in AGW Setup using the VirtualBox, where session packets are dropped. To work around this (for **test/development environments only**), run the commands below and restart the gNB and UE session:

            ~~~bash
            sudo ovs-ofctl del-flows gtp_br0 "table=13,priority=0"

            sudo ovs-ofctl add-flow gtp_br0 "table=13,priority=0,actions=resubmit(,20)"
            ~~~
