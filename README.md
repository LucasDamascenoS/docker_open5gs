# Open5GS + SIMULATOR Setup Guide

This setup uses three Ubuntu 22.04 Virtual Machines with 4GB of RAM, 4 CPUs and 15GB of storage:
- **AMF**
- **UPF**
- **SIMULATOR**

> ⚙️ Steps **1** and **2** must be completed on all Virtual Machines.

> ⚙️ Steps **3** and **4** must be completed on both the **AMF** and **UPF** Virtual Machines.

> ⚙️ Step **7** must be completed on the **SIMULATOR** Virtual Machine.

## 1. Install Docker and Docker Compose

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

# Allow run Docker without sudo
sudo groupadd docker || true
sudo usermod -aG docker $USER
newgrp docker
sudo reboot
~~~


## 2. Install pip and PyMongo

~~~bash
sudo apt install python3-pip

pip3 install pymongo
~~~

## 3. Pull Base Images

~~~bash
docker pull ghcr.io/herlesupreeth/docker_open5gs:master
docker tag ghcr.io/herlesupreeth/docker_open5gs:master docker_open5gs

docker pull ghcr.io/herlesupreeth/docker_grafana:master
docker tag ghcr.io/herlesupreeth/docker_grafana:master docker_grafana

docker pull ghcr.io/herlesupreeth/docker_metrics:master
docker tag ghcr.io/herlesupreeth/docker_metrics:master docker_metrics
~~~

## 4. Clone the Open5GS Repository

~~~bash
git clone https://github.com/LucasDamascenoS/docker_open5gs.git

cd docker_open5gs

git checkout custom-setup
~~~

## 5. AMF Setup
1. Edit the `.env` file:
   - Set `UPF_IP` to the IP address of the **UPF** Virtual Machine.
   - Set `SMF_IP` and `AMF_IP` to the IP address of the **AMF** Virtual Machine.

2. Deploy the AMF components:

   ~~~bash
   docker compose -f sa-deploy.yaml up -d nrf scp udm mongo udr ausf bsf pcf amf nssf metrics grafana smf webui
   ~~~

3. Access the Open5GS WebUI at `http://<AMF-IP>:9999`

   Credentials:
   - Username: `admin`
   - Password: `1423`

4. Add a Subscriber

   Create a subscriber with the following values:

   | Field | Value |
   |------|-------|
   | IMSI | 001010000000001 |
   | K (Key) | 00112233445566778899AABBCCDDEEFF |
   | OPc | 00112233445566778899AABBCCDDEEFF |
   | DNN (APN) | internet |
   | SST | 1 |
   | SD | 000001 |

   Or use the CLI to create multiple subscribers:

   ~~~bash
   python3 script/add_imsi.py --count 10 --start 001010000000001
   ~~~

   > ⚙️ To add subscribers with a different DNN (APN), open the `script/add_imsi.py` file and modify the field `'name': 'internet'` at line 61.

## 6. UPF Setup
1. Edit the `.env` file:
   - Set `UPF_IP` and `UPF_ADVERTISE_IP` to the IP address of the **UPF** Virtual Machine.
   - Set `SMF_IP` to the IP address of the **AMF** Virtual Machine.

2. Deploy the UPF component:

   ~~~bash
   docker compose -f sa-deploy.yaml up -d --no-deps upf
   ~~~

3. Add UE route for WAN access:

   ~~~bash
   # Enable IPv4 forwarding
   sudo sysctl -w net.ipv4.ip_forward=1

   # Add NAT rule
   sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE
   sudo iptables -A FORWARD -i ogstun -o enp0s3 -j ACCEPT
   sudo iptables -A FORWARD -i enp0s3 -o ogstun -m state --state RELATED,ESTABLISHED -j ACCEPT
   ~~~

## 7. SIMULATOR Setup

### UERANSIM Setup (Please refer to the [UERANSIM](https://github.com/aligungr/UERANSIM) repository for more information.)

1. Install OS Dependencies:

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

   > ⚙️ Don't install cmake with `sudo apt-get install cmake`, because it installs very old version of cmake by default.

2. Clone the UERANSIM Repository:

   ~~~bash
   git clone https://github.com/aligungr/UERANSIM
   
   cd ~/UERANSIM
   ~~~

3. Build the UERANSIM:

   ~~~bash
   make
   ~~~

4. Edit the `~/UERANSIM/config/open5gs-gnb.yaml` file:
   - Set `mcc` to `'001'` and `mnc` to `'01'`.
   - Set `linkIp`, `ngapIp` and `gtpIp` to the IP address of the **SIMULATOR** Virtual Machine.
   - Set `address` under `amfConfigs` section to the IP address of the **AMF** Virtual Machine.
   - Add `sd: 000001` under `slices` section.

   Your `~/UERANSIM/config/open5gs-gnb.yaml` file should look like this:
   
   ~~~yml
   mcc: '001'          # Mobile Country Code value
   mnc: '01'           # Mobile Network Code value (2 or 3 digits)
   
   nci: '0x000000010'  # NR Cell Identity (36-bit)
   idLength: 32        # NR gNB ID length in bits [22...32]
   tac: 1              # Tracking Area Code
   
   linkIp: <SIMULATOR_IP>   # gNB's local IP address for Radio Link Simulation (Usually same with local IP)
   ngapIp: <SIMULATOR_IP>   # gNB's local IP address for N2 Interface (Usually same with local IP)
   gtpIp: <SIMULATOR_IP>    # gNB's local IP address for N3 Interface (Usually same with local IP)
   
   # List of AMF address information
   amfConfigs:
   - address: <AMF_IP>
       port: 38412
   
   # List of supported S-NSSAIs by this gNB
   slices:
   - sst: 1
     sd: 000001
   
   # Indicates whether or not SCTP stream number errors should be ignored.
   ignoreStreamIds: true
   ~~~

5. Edit the `~/UERANSIM/config/open5gs-ue.yaml` file:
   - Set `supi` to the first subscriber IMSI on your DB.
   - Set `mcc` to `'001'` and `mnc` to `'01'`.
   - Remove the `protectionScheme`, `homeNetworkPublicKey`, `homeNetworkPublicKeyId` and `routingIndicator` fields.
   - Set `key` and `op` to the corresponding values that you configured in Step **5**.
   - Remove the `tunNetmask` field.
   - Set the `gnbSearchList` to the IP address of the **SIMULATOR** Virtual Machine.
   - Add `sd: 000001` under `sessions` section.
   - Add `sd: 000001` under `configured-nssai` section.
   - Set `sd: 000001` under `default-nssai` section.

   Your `~/UERANSIM/config/open5gs-ue.yaml` file should look like this:

   ~~~yml
   # IMSI number of the UE. IMSI = [MCC|MNC|MSISDN] (In total 15 digits)
   supi: 'imsi-001010000000001'
   # Mobile Country Code value of HPLMN
   mcc: '001'
   # Mobile Network Code value of HPLMN (2 or 3 digits)
   mnc: '01'
   
   # Permanent subscription key
   key: '00112233445566778899AABBCCDDEEFF'
   # Operator code (OP or OPC) of the UE
   op: '00112233445566778899AABBCCDDEEFF'
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
     - <SIMULATOR_IP>
   
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
         sd: 000001
   
   # Configured NSSAI for this UE by HPLMN
   configured-nssai:
     - sst: 1
       sd: 000001
   
   # Default Configured NSSAI for this UE
   default-nssai:
     - sst: 1
       sd: 000001
   
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

6. Start the gNB:

   ~~~bash
   cd ~/UERANSIM/build

   ./nr-gnb -c ../config/open5gs-gnb.yaml
   ~~~

7. Start the UE:

   - To start 1 UE, use the command:
   
      ~~~bash
      cd ~/UERANSIM/build      
      
      sudo ./nr-ue -c ../config/open5gs-ue.yaml
      ~~~

   - To start 10 UEs, use the command:

      ~~~bash
      cd ~/UERANSIM/buil      
      
      sudo ./nr-ue -c ../config/open5gs-ue.yaml -n 10
      ~~~

      > ⚙️ IMSI number is incremented by one for each of the UEs (starting from the IMSI specified in the `open5gs-ue.yaml` file).

8. Test Traffic:
   
   If you want to manually utilize the interface, just bind your TCP/IP socket to `uesimtunX` interface.

   ~~~bash
   ping -I uesimtun0 google.com
   ~~~