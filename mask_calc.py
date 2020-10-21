import itertools
import argparse


def parse_lscpu(file_location, nic_numa, dpdk_ht, no_dpdk_phy):
    """
    Take lspcu -p output i.e. lines of:
    # CPU,Core,Socket,Node,,L1d,L1i,L2,L3
    parse it and generate dictionary where numa is key and value is a list of tuples.
    tuples contain phy_cpu_id, its' HT sibling, phy role & HT sibling role
    """
    with open(file_location) as fh:
        cpu_file = fh.readlines()
    core_map = {}
    cpu_file = [line.strip().split(',') for line in cpu_file if not line.startswith('#')]
    cpu_file = sorted(cpu_file, key=lambda x: int(x[3]))
    for node, data in itertools.groupby(cpu_file, key=lambda x: x[3]):
        node = int(node)
        data = sorted(data, key=lambda x: int(x[1]))
        core_map.setdefault(node, list())
        index = 0
        for _, data_2 in itertools.groupby(data, key=lambda x: x[1]):
            data_2 = list(data_2)
            cpu_0 = int(data_2[0][0])
            cpu_1 = int(data_2[1][0])
            if index == 0: 
                core_map[node].append((cpu_0, cpu_1, 'H', 'H'))
            elif index <= int(no_dpdk_phy) and node == int(nic_numa):
                if dpdk_ht:
                    core_map[node].append((cpu_0, cpu_1, 'D', 'D'))
                else:
                    core_map[node].append((cpu_0, cpu_1, 'D', 'D'))
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
    parser.add_argument("nic_numa", help="NUMA node used for NIC")
    parser.add_argument("dpdk_cores", help="No. physical cores dedicated to DPDK data-plane")
    parser.add_argument("-t", "--hyper-thread", action="store_true", help="allocate HT "
                                                  "siblings of dpdk_cores to the dataplane")
    args = vars(parser.parse_args())
    return args


def print_cpu_map(core_map):
    """Print a map of CPU roles against numa nodes and core number.
    Print cpumasks for various Openstack / Contrail components according to the same mapping"""
    print('H = hostOS, D = Contrail DPDK dataplane, 0 = unassigned, N = Nova')
    for numa, cpus in core_map.items():
        format_string = ' ' * 10 + '{:12} '  + '{:2} ' *(len(cpus))
        print('numa-node {}:'.format(numa))
        for index, line_type in zip((0,2,1,3), ('core:','role:', 'HT Sibling:', 'role:')):
            print(format_string.format(line_type, *(str(cpu[index]) for cpu in cpus)))
    all_cores = [inner for outer in core_map.values() for inner in outer]
    for line, core_type in zip(('isolcpus','nova conf','CPU affinity','DPDK cores'), 
                               (('0', 'D', 'N'),('N'), ('H'), ('D'))):
        format_cores(line, filter_cores(all_cores, core_type))
 


if __name__ == '__main__':
    args = cli_grab()
    core_map = parse_lscpu(args['lscpu_file'], args['nic_numa'], args['hyper_thread'], args['dpdk_cores'])
    print_cpu_map(core_map)