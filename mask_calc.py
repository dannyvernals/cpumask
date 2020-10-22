"""
Basic script to generate a CPU map for the various roles needed
in a Contrail + Openstack DPDK environment.
Uses cpu topology from lscpu -p and CLI args to provide the roles
"""
import itertools
import argparse


def parse_lscpu(file_location, nic_numa, dpdk_ht, no_dpdk_phy, no_host_phy):
    """
    Take lspcu -p output i.e. lines of:
    # CPU,Core,Socket,Node,,L1d,L1i,L2,L3
    parse it and generate dictionary where numa is key and value is a list of tuples.
    tuples contain phy_cpu_id, its' HT sibling, phy role & HT sibling role
    """
    with open(file_location) as lscpu_file:
        cpu_file = lscpu_file.readlines()
    core_map = {}
    cpu_file = [line.strip().split(',') for line in cpu_file if not line.startswith('#')]
    cpu_file = sorted(cpu_file, key=lambda x: int(x[3]))
    for node, data in itertools.groupby(cpu_file, key=lambda x: x[3]):
        node = int(node)
        data = sorted(data, key=lambda x: int(x[1]))
        core_map.setdefault(node, list())
        index = 0
        numa_count = len({line[3] for line in cpu_file})
        if no_host_phy % numa_count != 0:
            raise ValueError("host cores not divisible by numa nodes. \nScript "
                             "can't handle this as it assigns them evenly to numa nodes")
        for _, data_2 in itertools.groupby(data, key=lambda x: x[1]):
            data_2 = list(data_2)
            cpu_0 = int(data_2[0][0])
            cpu_1 = int(data_2[1][0])
            if index < no_host_phy / numa_count:
                core_map[node].append((cpu_0, cpu_1, 'H', 'H'))
            elif index < no_dpdk_phy + (no_host_phy / numa_count) and node == nic_numa:
                if dpdk_ht:
                    core_map[node].append((cpu_0, cpu_1, 'D', 'D'))
                else:
                    core_map[node].append((cpu_0, cpu_1, 'D', '0'))
            else:
                core_map[node].append((cpu_0, cpu_1, 'N', 'N'))
            index += 1
    return core_map


def format_cores(list_name, cores_list):
    """Take a standard list() of cores and produce the abridged output used in conf files.
    e.g.  1-10,12-24"""
    cores_list = sorted(cores_list)
    cores_terse_list = []
    start = pointer = cores_list[0]
    i = 0
    while i < len(cores_list):
        core = cores_list[i]
        i += 1
        if pointer + 1 == core:
            pointer += 1
            if i == len(cores_list):
                cores_terse_list.append('{}-{}'.format(start, pointer))
        else:
            if start != pointer:
                cores_terse_list.append('{}-{}'.format(start, pointer))
                start = pointer = core
            elif core + 1 != cores_list[1] or i == len(cores_list):
                cores_terse_list.append(str(core))
                start = pointer = core
    print('{}: {}'.format(list_name, ','.join(cores_terse_list)))


def filter_cores(all_cores, purpose):
    """reduce passed list to one containing CPUs with only the specified purpose"""
    cpu_list = []
    for cpu in all_cores:
        if cpu[2] in purpose:
            cpu_list.append(cpu[0])
        if cpu[3] in purpose:
            cpu_list.append(cpu[1])
    return cpu_list


def cli_grab():
    """take stuff from cli, output it in a dict"""
    parser = argparse.ArgumentParser(description="Calculate DPDK cpu mask values from 'lscpu -p'")
    parser.add_argument("lscpu_file", help="Location of file containing lscpu -p output")
    parser.add_argument("nic_numa", type=int, help="NUMA node used for NIC")
    parser.add_argument("dpdk_cores", type=int, help="No. physical cores dedicated"
                                                     " to DPDK data-plane")
    parser.add_argument("host_cores", type=int, help="No. physical cores dedicated to host OS")
    parser.add_argument("no_nics", type=int, help="No. of NICs in bond associated with vhost0")
    parser.add_argument("-t", "--hyper-thread", action="store_true", help="allocate HT siblings "
                                                                          "dpdk_cores to the"
                                                                          "to the dataplane")
    args = vars(parser.parse_args())
    return args


def print_cpu_map(core_map):
    """Print a map of CPU roles against numa nodes and core number.
    Print cpumasks for various Openstack / Contrail components according to the same mapping"""
    print('H = hostOS, D = Contrail DPDK dataplane, 0 = unassigned, N = Nova')
    for numa, cpus in core_map.items():
        format_string = ' ' * 10 + '{:12} '  + '{:2} ' *(len(cpus))
        print('numa-node {}:'.format(numa))
        for index, line_type in zip((0, 2, 1, 3), ('core:', 'role:', 'HT Sibling:', 'role:')):
            print(format_string.format(line_type, *(str(cpu[index]) for cpu in cpus)))
    all_cores = [inner for outer in core_map.values() for inner in outer]
    for line, core_type in zip(('isolcpus', 'nova conf', 'CPU affinity', 'DPDK cores'),
                               (('0', 'D', 'N'), ('N'), ('H'), ('D'))):
        format_cores(line, filter_cores(all_cores, core_type))


def print_mempool(dpdk_cores, hyper_thread, no_nics):
    """calculate mempool size using formula:
    vr_mempool_sz = 2 * (dpdk_rxd_sz + dpdk_txd_sz) * (num_cores) * (num_ports)"""
    if hyper_thread:    
        mempool_size = 2 * 4096 * (dpdk_cores * 2) * no_nics
    else:
        mempool_size = 2 * 4096 * dpdk_cores * no_nics
    print("vr_mempool_sz: {} (assuming 2048 Rx/Tx descriptor ring size)".format(mempool_size))



if __name__ == '__main__':
    ARGS = cli_grab()
    CORE_MAP = parse_lscpu(ARGS['lscpu_file'], ARGS['nic_numa'],
                           ARGS['hyper_thread'], ARGS['dpdk_cores'], ARGS['host_cores']
                           )
    print_cpu_map(CORE_MAP)
    print_mempool(ARGS['dpdk_cores'], ARGS['hyper_thread'], ARGS['no_nics'])

   
