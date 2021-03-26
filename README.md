# cpumask
Calculate CPU mask configurations for Contrail + Openstack DPDK Data-Plane

## About
To have a working & high-performance Contrail deployment using DPDK Data-Plane:  
* CPU cores need to be dedicated to the Data-Plane.  
* We need to dedicate CPUs to the HostOS.
* Make sure Nova doesn't allocate either of these to VMs.  
* The highest performance also requires colocating the Data-Plane cores in the same NUMA as the physical NICs.  

This can involve configuration in several areas: kernel isolcpus, systemd CPUAffinity, nova.conf vcpu_pin_set and within Contrail.  

This script generates the required values for these parameters based on the CPU topology (lscpu -p) and required allocations.

```
python mask_calc.py -h
usage: mask_calc.py [-h] [-t] lscpu_file nic_numa dpdk_cores host_cores nics

Calculate DPDK cpu mask values from 'lscpu -p'

positional arguments:
  lscpu_file          Location of file containing lscpu -p output
  nic_numa            NUMA node used for NIC
  dpdk_cores          No. physical cores dedicated to DPDK data-plane
  host_cores          No. physical cores dedicated to host OS
  nics                No. of NICs in bond associated with vhost0

optional arguments:
  -h, --help          show this help message and exit
  -t, --hyper-thread  allocate HT siblings dpdk_cores to the to the dataplane

```

```
python mask_calc.py cpus/6148 0 4 2 2 -t
H = hostOS, D = Contrail DPDK dataplane, 0 = unassigned, N = Nova
numa-node 0:
          core:        0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 
          role:        H  D  D  D  D  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
          HT Sibling:  40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 
          role:        H  D  D  D  D  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
numa-node 1:
          core:        20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 
          role:        H  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
          HT Sibling:  60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 
          role:        H  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
isolcpus: 1-19,21-39,41-59,61-79
nova conf: 5-19,21-39,45-59,61-79
CPU affinity: 0,20,40,60
DPDK cores: 1-4,41-44
vr_mempool_sz: 131072 (assuming 2048 Rx/Tx descriptor ring size)
```
