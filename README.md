# cpumask
Calculate CPU mask configurations for Contrail DPDK based on lscpu

```
python mask_calc.py -h
usage: mask_calc.py [-h] [-t] lscpu_file nic_numa dpdk_cores

Calculate DPDK cpu mask values from 'lscpu -p'

positional arguments:
  lscpu_file          Location of file containing lscpu -p output
  nic_numa            NUMA node used for NIC
  dpdk_cores          No. physical cores dedicated to DPDK data-plane

optional arguments:
  -h, --help          show this help message and exit
  -t, --hyper-thread  allocate HT siblings of dpdk_cores to the dataplane
danny@newtop:~/vm-shared-disk/script_clones/sdn/cpumask$ 
```

```
python mask_calc.py cpus/6148 0 3 -t
H = hostOS, D = Contrail DPDK dataplane, 0 = unassigned, N = Nova
numa-node 0:
          core:        0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 
          role:        H  D  D  D  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
          HT Sibling:  40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 
          role:        H  D  D  D  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
numa-node 1:
          core:        20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 
          role:        H  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
          HT Sibling:  60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 
          role:        H  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  
isolcpus: 1-19,21-39,41-59,61-78
nova conf: 4-19,21-39,44-59,61-78
CPU affinity: 0,20,40,60
DPDK cores: 1-3,41-42
```
