#!/usr/bin/env python3
# Sources: Assignment 3 code and lp-notes/mpls from icorsi
# I didn't manage to make the iperf3 work. It shows up as Connection Failed, operation now in progress

usage = """./best_goodput.py [-h] [-p] [-l] [-d] definition

A tool to define the emulation of a network configured to achieve the best
    overall goodput under a given set of flow demands.

positional arguments:
    definition      the definition file of the network and flow demands in YAML

options:
    -h, --help      show this help message and exit
    -p, --print     print the optimal goodput for each flow and exit
    -l, --lp        print the definition of the optimization problem in CPLEX LP format
"""

from argparse import ArgumentParser
import yaml
import subprocess

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import Node, OVSBridge

parser = ArgumentParser(
    description="A tool to define the emulation of a network configured to achieve the best overall goodput under a given set of flow demands."
)
parser.add_argument("-p", "--print", help="print the optimal goodput for each flow and exit", action="store_true")
parser.add_argument("-l", "--lp", help="print the definition of the optimization problem in CPLEX LP format", action="store_true")
parser.add_argument("definition", metavar="definition", help="the definition file of the network and flow demands in YAML")

# With no parameters just start a mininet simulation with the best goodput setup
# So in any case, we need to write the .sol script and:

    # 1. if -l we output it to std

    # 2. -p pass it to the solver, obtain result and print result

    # 3. no args, we pass it to the solver, define rules for each router and
    # start simulation with best setup

args = parser.parse_args()

# Parsing

def mask_to_prefix(mask_str):
    return sum(bin(int(o)).count("1") for o in mask_str.split("."))

stream = open(args.definition, "r")
data = yaml.load(stream, Loader=yaml.Loader)

routers = data["routers"]
hosts   = data["hosts"]
demands = data["demands"]  # list of {src, dst, rate}

networks = {}

# Compute network address for each router interface and index by net_str
for r_id, router in routers.items():
    for iface_id, interface in router.items():
        addr = [int(x) for x in interface["address"].split(".")]
        mask = [int(x) for x in interface["mask"].split(".")]
        net  = [addr[i] & mask[i] for i in range(4)]
        net_str = ".".join(str(o) for o in net)
        interface["net"]     = net
        interface["net_str"] = net_str

# Create the networks object dict
for r_id, router in routers.items():
    for iface_id, interface in router.items():
        net_str = interface["net_str"]
        if net_str in networks:
            networks[net_str]["routers"].append(r_id)
            if "cost" in interface:
                networks[net_str]["cost"] = interface["cost"]
        else:
            networks[net_str] = {
                "cost":    interface["cost"] if "cost" in interface else -1,
                "prefix":  mask_to_prefix(interface["mask"]),
                "routers": [r_id],
                "hosts":   [],
            }

# Compute network address for each host interface
for h_id, host in hosts.items():
    for iface_id, interface in host.items():
        addr = [int(x) for x in interface["address"].split(".")]
        mask = [int(x) for x in interface["mask"].split(".")]
        net  = [addr[i] & mask[i] for i in range(4)]
        net_str = ".".join(str(o) for o in net)
        interface["net_str"] = net_str

# Add hosts to networks object dict
for h_id, host in hosts.items():
    for iface_id, interface in host.items():
        net_str = interface["net_str"]
        if net_str in networks:
            networks[net_str]["hosts"].append(h_id)
            for d in demands:
                if h_id == d["src"]:
                    d["src_router"] = networks[net_str]["routers"][0]
                if h_id == d["dst"]:
                    d["dst_router"] = networks[net_str]["routers"][0]

# Default cost to 1 Mbps if not specified
for net in networks.values():
    if net["cost"] == -1:
        net["cost"] = 1

# Build list of undirected router-to-router edges: (r1, r2, net_str, capacity)
edges = []
for net_str, net in networks.items():
    rs = net["routers"]
    if len(rs) == 2:
        edges.append((rs[0], rs[1], net_str, net["cost"]))

#print(edges)
# Create adj
adj = {}
for e in edges:
    u = e[0]
    v = e[1]
    c = e[2]
    if u not in adj:
        adj[u] = []
    if v not in adj:
        adj[v] = []
    adj[u].append((v, c))
    adj[v].append((u, c))

# Add ids to demands
aux_id = 1
for d in demands:
    d["id"] = str(aux_id)
    aux_id = aux_id + 1

# Helpers

def find_iface(r_id, target_net_str):
    for i_id, iface in routers[r_id].items():
        if iface["net_str"] == target_net_str:
            return i_id, iface
    return None, None

def host_router(h_id):
    """Return the router directly connected to h_id."""
    iface = next(iter(hosts[h_id].values()))
    return networks[iface["net_str"]]["routers"][0]



# LP formulation

def rx(demand_id, u_id, v_id):
        return "rx" + demand_id + "_" + u_id + "_" + v_id
def x(demand_id, u_id, v_id):
    return "x" + demand_id + "_" + u_id + "_" + v_id

def build_lp():
    """Return the LP problem as a CPLEX LP format string."""
    n = len(demands)

    # Our objective function will be to maxmimize m, m is the minimal effectiveness
    # ratio.

    lp = "Maximize\n\tobj: m\nSubject to\n"

    # To achieve m being the minimum of each effectiveness ratio we will put one
    # constraint for each flow and have m <= attained flow / flow demand

    # The flow demand is a constant that we get from the problem statement, while the
    # attained flow is a variable of the lp problem (lambda{i})
    for idx, demand in enumerate(demands):
        lp = lp + f"\t{demand['rate']} m - lambda{demand['id']} <= 0\n"

    # For the flow of each commodity in each edge we will use two variables:
    #   - rxi_u_v (real-valued): The flow of commodity i from nodes u to v.
    #   - xi_u_v (binary): Wether the flow of commodity i is using the edge from u to v.

    # We then add the flow balance constraints for real valued rate variables, that
    # is, the inflow of a specific commodity has to be equal to the outflow.
    # The only nodes to take into account are the routers
    # Flow balance for real-valued rate variables
    for d in demands:
        did = d["id"]
        for u in adj:
            lp1 = "\t"
            for i, v in enumerate([ aux[0] for aux in adj[u]]):
                if i > 0:  # separate terms with +
                    lp1 = lp1 + " + "
                lp1 = lp1 + rx(did, u, v) + " - " + rx(did, v, u)
            if u == d["src_router"]:
                lp1 = lp1 + " - lambda" + did + " = 0\n"  # net_outflow = lambda (positive)
            elif u == d["dst_router"]:
                lp1 = lp1 + " + lambda" + did + " = 0\n"  # net_outflow = -lambda (negative at dst)
            else:
                lp1 = lp1 + " = 0\n"
            lp = lp + lp1

    # Flow balance for binary indicator variables. For a demand, the number of 
    # paths going in has to be the same as the ones going out (except for src
    # and dst). Another constraint later ensures we only go into the same node
    # at most once for each commodity.
    for d in demands:
        did = d["id"]
        for u in adj:
            lp2 = "\t"
            for i, v in enumerate([ aux[0] for aux in adj[u]]):
                if i > 0:
                    lp2 = lp2 + " + "
                lp2 = lp2 + x(did, u, v) + " - " + x(did, v, u)
            if u == d["src_router"]:
                lp2 = lp2 + " = 1\n"
            elif u == d["dst_router"]:
                lp2 = lp2 + " = -1\n"
            else:
                lp2 = lp2 + " = 0\n"
            lp = lp + lp2

    # Mutual exclusion of incoming and outgoing into the same node
    # At most one outgoing edge per node per demand
    lp = lp + "\n\\ Mutual exclusion outgoing\n"
    for d in demands:
        did = d["id"]
        for u in adj:
            lp1 = "\t"
            for i, (v, _) in enumerate(adj[u]):
                lp1 = lp1 + x(did, u, v)
                if i != len(adj[u]) - 1:
                    lp1 = lp1 + " + "
            lp = lp + lp1 + " <= 1\n"

    # At most one incoming edge per node per demand
    lp = lp + "\n\\ Mutual exclusion incoming\n"
    for d in demands:
        did = d["id"]
        for u in adj:
            lp2 = "\t"
            for i, (v, _) in enumerate(adj[u]):
                lp2 = lp2 + x(did, v, u)
                if i != len(adj[u]) - 1:
                    lp2 = lp2 + " + "
            lp = lp + lp2 + " <= 1\n"

    # At most one direction per undirected edge per demand
    lp = lp + "\n\\ Mutual exclusion per edge\n"
    for d in demands:
        did = d["id"]
        for e in edges:
            u, v = e[0], e[1]
            lp = lp + "\t" + x(did, u, v) + " + " + x(did, v, u) + " <= 1\n"

    # Link capacities constraints
    lp = lp + "\n\\ Link capacities constraints\n"
    for e in edges:
        u = e[0]
        v = e[1]
        c = str(e[3])
        lp = lp + "\t"
        for idx, d in enumerate(demands):
            did = d["id"]
            lp = lp + rx(did,u,v) + " + " + rx(did,v,u)
            if idx != len(demands) - 1:
                lp = lp + " + "
        lp = lp + " <= " + c + "\n"

    # Control of real value flow variables by corresponding indicators
    lp = lp + "\n\\ Control of real value flow variables by corresponding indicators\n"
    for d in demands:
        did = d["id"]
        for u in adj:
            for v, net_str in adj[u]:
                cap = networks[net_str]["cost"]
                lp = lp + "\t" + rx(did,u,v) + " - " + str(cap) + " " + x(did,u,v) + " <= 0\n"

    # lambda_i is the actual flow, bounded by [0, demand rate]
    lp = lp + "Bounds\n"
    for d in demands:
        lp = lp + f"\t0 <= lambda{d['id']} <= {d['rate']}\n"

    # x variables are binary path indicators
    lp = lp + "Binary\n"
    for d in demands:
        did = d["id"]
        for u in adj:
            for v, _ in adj[u]:
                lp = lp + "\t" + x(did,u,v) + "\n"

    lp = lp + "End\n"

    return lp


def solve():
    # We pass the output of build_lp to glpsol
    lp_program = build_lp()

    lp_path  = "problem.lp"
    sol_path = "problem.txt"

    with open(lp_path, "w") as lp_f:
        lp_f.write(lp_program)

    try:
        subprocess.run(
            ["glpsol", "-o", sol_path, "--lp", lp_path],
            check=True, capture_output=True
        )

        alpha = 0.0
        flows = [{} for _ in demands]
        lambdas = [0.0] * len(demands)

        with open(sol_path) as sol_f:
            for line in sol_f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                name = parts[1]
                try:
                    val = float(parts[2])
                except (ValueError, IndexError):
                    continue

                if name == "m":
                    alpha = val
                # We take the target flows to output them (in case of -p)
                elif name.startswith("lambda"):
                    i = int(name[6:]) - 1
                    lambdas[i] = val
                # Take the rate of each demand in each edge to set up the mpls
                elif name.startswith("rx"):
                    tokens = name[2:].split("_")
                    i = int(tokens[0]) - 1
                    u = tokens[1]
                    v = tokens[2]
                    flows[i][(u, v)] = val

        return flows, lambdas
    finally:
        pass

# --lp mode

if args.lp:
    print(build_lp(), end="")
    exit(0)

# --print mode

if getattr(args, "print"):
    flows, lambdas = solve()
    for i, d in enumerate(demands):
        print(f"The best goodput for flow demand #{i+1} is {round(lambdas[i], 4)} Mbps")
    exit(0)

# Mininet emulation

flows, lambdas = solve()

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd("sysctl net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.mpls.platform_labels=65535")

    def terminate(self):
        self.cmd("sysctl net.ipv4.ip_forward=0")
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    def build(self, **opts):
        for r_id in routers:
            self.addNode(r_id, cls=LinuxRouter, ip=None)

        for h_id, host in hosts.items():
            # Grab the host interface (we use iter and next to grab the only
            # element of the dict easily)
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
            for r_id in net["routers"]:
                i_id, interface = find_iface(r_id, net_str)
                self.addLink(r_id, sw, intfName1=f'{r_id}-{i_id}', params1={'ip': f"{interface['address']}/{net['prefix']}"})

        for h_id, host in hosts.items():
            for i_id, interface in host.items():
                net_str = interface["net_str"]
                self.addLink(h_id, switches[net_str], intfName1=f'{h_id}-{i_id}', params1={'ip': f"{interface['address']}/{networks[net_str]['prefix']}"})


mn = Mininet(topo=NetworkTopo(), controller=None)
mn.start()

# Enable MPLS on every router interface
for r_id in routers:
    r_node = mn.get(r_id)
    for i_id in routers[r_id]:
        r_node.cmd(f"sysctl -w net.mpls.conf.{r_id}-{i_id}.input=1")

# Set up MPLS forwarding for each demand
# We have one label for each demand
for i, d in enumerate(demands):
    label = i + 1
    src_r = host_router(d["src"])
    dst_r = host_router(d["dst"])
    flow = flows[i]

    for (u, v), fval in flow.items():
        if fval == 0:
            continue
        r_node = mn.get(u)

        # Find the interface/address toward v
        shared_net = None
        for net_str, net in networks.items():
            if u in net["routers"] and v in net["routers"]:
                shared_net = net_str
                break
        if shared_net is None:
            continue
        _, v_iface = find_iface(v, shared_net)
        next_ip = v_iface["address"]

        if u == src_r:
            # push label and forward
            dst_host_iface = next(iter(hosts[d["dst"]].values()))
            dst_ip = dst_host_iface["address"]
            # When sending packets from demand source towards demand destination
            # we add the label of this demand
            r_node.cmd(f"ip route add {dst_ip}/32 encap mpls {label} via inet {next_ip}")
        else:
            # swap/forward
            r_node.cmd(f"ip -f mpls route add {label} as {label} via inet {next_ip}")
    # pop label, deliver locally
    dst_host_iface = next(iter(hosts[d["dst"]].values()))
    dst_ip = dst_host_iface["address"]
    dst_node = mn.get(dst_r)
    dst_node.cmd(f"ip -f mpls route add {label} via inet {dst_ip}")

CLI(mn)
mn.stop()