
usage = """emulation.py [-h] [-d] definition
A tool to define the emulation of a network.
positional arguments:
    definition the definition file of the network in YAML

options:
    -h, --help show this help message and exit
    -d, --draw output a map of the routers in GraphViz format
"""


from argparse import ArgumentParser
import yaml

def mask_to_prefix(mask_str):
    return sum(bin(int(o)).count('1') for o in mask_str.split('.'))
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import Node, OVSBridge


parser = ArgumentParser(description="A tool to define the emulation of a network.", usage=usage)
#parser.add_argument("-h", "--help", help="show this help message and exit", action="store_true")
parser.add_argument("-d", "--draw", help="output a map of the routers in GraphViz format", action="store_true")
parser.add_argument("definition", metavar="FILE")

args = parser.parse_args()

# Read yaml file
stream = open(args.definition, "r")
data = yaml.load(stream, Loader=yaml.Loader)

routers = data['routers']
hosts = data['hosts']

networks = {}

# Preprocess data to compute network
for r_id,router in routers.items():
    for interface in router.values():
        addr= [ int(aux) for aux in interface['address'].split(".") ]
        mask = [ int(aux) for aux in interface['mask'].split(".") ]
        net =  [ addr[i] & mask[i] for i in range(4) ]
        net_str = ".".join(str(o) for o in net)
        interface['net'] = net
        interface['net_str'] = net_str

        if net_str in networks:
            networks[net_str]["routers"].append(r_id)
            if "cost" in interface:
                networks[net_str]["cost"] = interface["cost"]
        else:
            aux = {}
            aux["cost"] = interface["cost"] if "cost" in interface else -1
            aux["prefix"] = mask_to_prefix(interface["mask"])
            aux["routers"] = []
            aux["routers"].append(r_id)
            networks[net_str] = aux

# Preprocess hosts (compute net_str per interface)
for h_id, host in hosts.items():
    for interface in host.values():
        addr = [int(x) for x in interface['address'].split('.')]
        mask = [int(x) for x in interface['mask'].split('.')]
        net = [addr[i] & mask[i] for i in range(4)]
        interface['net_str'] = '.'.join(str(o) for o in net)

for n in networks.values():
    if n["cost"] == -1:
        n["cost"] = 1


# Draw graph
if args.draw:
    out = "graph Network {"
    for r in routers:
        out = out + f"\n\t{r} [shape=circle];"
    for net in networks.values():
        n = len(net["routers"])
        for i in range(n-1):
            for j in range(i+1, n):
                out = out + f"\n\t{net['routers'][i]} -- {net['routers'][j]} [label={net['cost']}];"
    out = out + "\n}"
    print(out)
    exit(0)

import heapq

# Find the interface of a router for a given network
def find_iface(r_id, target_net_str):
    for i_id, iface in routers[r_id].items():
        if iface['net_str'] == target_net_str:
            return i_id, iface
    return None, None

# Build graph: router nodes, edges = shared networks with cost
graph = {r_id: [] for r_id in routers}
for net_str, net in networks.items():
    rs = net['routers']
    cost = net['cost']
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            graph[rs[i]].append((rs[j], cost, net_str))
            graph[rs[j]].append((rs[i], cost, net_str))

# compute shortest path for a given source
def dijkstra(src):
    dist = {r: float('inf') for r in routers}
    prev = {r: None for r in routers}
    dist[src] = 0
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for neighbor, w, link_net in graph[u]:
            if dist[u] + w < dist[neighbor]:
                dist[neighbor] = dist[u] + w
                prev[neighbor] = (u, link_net)
                heapq.heappush(pq, (dist[neighbor], neighbor))
    return prev

# next_hop[src][dst] = (first_hop_router_id, net_str shared between src and first_hop)
next_hop = {}
for r_id in routers:
    prev_map = dijkstra(r_id)
    next_hop[r_id] = {}
    for dst in routers:
        if dst == r_id or prev_map[dst] is None:
            continue
        cur = dst
        while prev_map[cur] is not None and prev_map[cur][0] != r_id:
            cur = prev_map[cur][0]
        if prev_map[cur] is not None:
            next_hop[r_id][dst] = (cur, prev_map[cur][1])


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate( self ):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    def build(self, **opts):
        for r_id in routers:
            self.addNode(r_id, cls=LinuxRouter, ip=None)

        for h_id, host in hosts.items():
            # Grab the host interface (we use iter and next to grab the only element of the dict easily)
            iface = next(iter(host.values()))
            # There should only be one router on this network
            r_id = networks[iface['net_str']]['routers'][0]
            # Get routers interface connecting to the host
            _, r_iface = find_iface(r_id, iface['net_str'])
            # Add host to the topology
            self.addHost(h_id, ip=None, defaultRoute=f'via {r_iface["address"]}')

        switches = {}
        
        # We add a switch for each network
        for net_str, net in networks.items():
            sw = self.addSwitch('s' + net_str.replace('.', ''), cls=OVSBridge)
            switches[net_str] = sw
            for r_id in net['routers']:
                i_id, interface = find_iface(r_id, net_str)
                self.addLink(r_id, sw, intfName1=f'{r_id}-{i_id}', params1={'ip': f"{interface['address']}/{net['prefix']}"})

        for h_id, host in hosts.items():
            for i_id, interface in host.items():
                net_str = interface['net_str']
                self.addLink(h_id, switches[net_str], intfName1=f'{h_id}-{i_id}', params1={'ip': f"{interface['address']}/{networks[net_str]['prefix']}"})

# --- Mininet setup ---
mn = Mininet(topo=NetworkTopo(), controller=None)
mn.start()

# Install routes on each router for every non-directly-connected network
for r_id in routers:
    r_node = mn.get(r_id)
    directly_connected = {iface['net_str'] for iface in routers[r_id].values()}
    for dst_net_str, dst_net_info in networks.items():
        if dst_net_str in directly_connected:
            # we dont need to add a rule
            continue
        gateway_ip = None # Immediate neighbor to send the packet to (obtained before with Djikstra)
        for dest_r in dst_net_info['routers']:
            if dest_r in next_hop.get(r_id, {}):
                # Obtain neighbor and the network
                first_hop_id, shared_net = next_hop[r_id][dest_r]
                # Obtain the interface
                _, gw_iface = find_iface(first_hop_id, shared_net)
                gateway_ip = gw_iface['address']
                break
        if gateway_ip is None:
            continue
        prefix = dst_net_info['prefix']
        if prefix is not None:
            r_node.cmd(f'ip route add {dst_net_str}/{prefix} via {gateway_ip}')

CLI(mn)
mn.stop()