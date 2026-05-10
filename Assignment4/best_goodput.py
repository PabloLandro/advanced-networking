#!/usr/bin/env python3
# Sources: Assignment 3 code and lp-notes from icorsi

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
import tempfile
import os

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import Node, OVSBridge
from mininet.link import TCLink

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

# ── Parsing ──────────────────────────────────────────────────────────────────

def mask_to_prefix(mask_str):
    return sum(bin(int(o)).count('1') for o in mask_str.split('.'))

stream = open(args.definition, "r")
data = yaml.load(stream, Loader=yaml.Loader)

routers = data['routers']
hosts   = data['hosts']
demands = data['demands']  # list of {src, dst, rate}

networks = {}

# Compute network address for each router interface and index by net_str
for r_id, router in routers.items():
    for iface_id, interface in router.items():
        addr = [int(x) for x in interface['address'].split('.')]
        mask = [int(x) for x in interface['mask'].split('.')]
        net  = [addr[i] & mask[i] for i in range(4)]
        net_str = '.'.join(str(o) for o in net)
        interface['net']     = net
        interface['net_str'] = net_str

        if net_str in networks:
            networks[net_str]['routers'].append(r_id)
            if 'cost' in interface:
                networks[net_str]['cost'] = interface['cost']
        else:
            networks[net_str] = {
                'cost':    interface.get('cost', -1),
                'prefix':  mask_to_prefix(interface['mask']),
                'routers': [r_id],
                'hosts':   [],
            }

# Compute network address for each host interface
for h_id, host in hosts.items():
    for iface_id, interface in host.items():
        addr = [int(x) for x in interface['address'].split('.')]
        mask = [int(x) for x in interface['mask'].split('.')]
        net  = [addr[i] & mask[i] for i in range(4)]
        net_str = '.'.join(str(o) for o in net)
        interface['net_str'] = net_str
        if net_str in networks:
            networks[net_str]['hosts'].append(h_id)

# Default cost to 1 Mbps if not specified
for net in networks.values():
    if net['cost'] == -1:
        net['cost'] = 1

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_iface(r_id, target_net_str):
    for i_id, iface in routers[r_id].items():
        if iface['net_str'] == target_net_str:
            return i_id, iface
    return None, None

def host_gateway(h_id):
    """Return the router interface address that serves as default gateway for h_id."""
    iface = next(iter(hosts[h_id].values()))
    net_str = iface['net_str']
    r_id = networks[net_str]['routers'][0]
    _, r_iface = find_iface(r_id, net_str)
    return r_id, r_iface['address']

def host_router(h_id):
    """Return the router directly connected to h_id."""
    iface = next(iter(hosts[h_id].values()))
    return networks[iface['net_str']]['routers'][0]

# Build list of undirected router-to-router edges: (r1, r2, net_str, capacity)
edges = []
for net_str, net in networks.items():
    rs = net['routers']
    if len(rs) == 2:
        edges.append((rs[0], rs[1], net_str, net['cost']))

# ── LP formulation ────────────────────────────────────────────────────────────

def build_lp():
    """Return the LP problem as a CPLEX LP format string."""
    n = len(demands)

    # Variable names: f_{i}_{u}_{v} for demand i on directed edge u->v
    def fvar(i, u, v):
        return f"f_{i}_{u}_{v}"

    obj_terms = ["alpha"]

    lines_obj  = [f" obj: alpha"]
    lines_subj = []

    # For each demand: total flow leaving the source router >= alpha * rate
    for i, d in enumerate(demands):
        src_r = host_router(d['src'])
        dst_r = host_router(d['dst'])
        rate  = d['rate']

        # Collect all directed edges incident to each router for this demand
        out = {r: [] for r in routers}
        inc = {r: [] for r in routers}
        for (u, v, net_str, cap) in edges:
            out[u].append(fvar(i, u, v))
            inc[v].append(fvar(i, u, v))
            out[v].append(fvar(i, v, u))
            inc[u].append(fvar(i, v, u))

        # Effectiveness ratio: outflow from source >= alpha * rate
        out_src = ' + '.join(out[src_r])
        lines_subj.append(f" eff_{i}: {out_src} - {rate} alpha >= 0")

        # Flow conservation at intermediate routers
        for r in routers:
            if r == src_r or r == dst_r:
                continue
            if not out[r]:
                continue
            in_vars  = ' + '.join(inc[r])  if inc[r]  else '0'
            out_vars = ' + '.join(out[r]) if out[r] else '0'
            lines_subj.append(f" cons_{i}_{r}: {in_vars} - {out_vars} = 0")

        # No flow into source, no flow out of destination (cleaner LP)
        # (capacity constraints handle physical limits anyway)

    # Capacity constraints: sum of all flows on each undirected link <= capacity
    for (u, v, net_str, cap) in edges:
        terms = []
        for i in range(n):
            terms.append(fvar(i, u, v))
            terms.append(fvar(i, v, u))
        lhs = ' + '.join(terms)
        lines_subj.append(f" cap_{u}_{v}: {lhs} <= {cap}")

    # Non-negativity (alpha and all f vars)
    all_fvars = []
    for i in range(n):
        for (u, v, net_str, cap) in edges:
            all_fvars.append(fvar(i, u, v))
            all_fvars.append(fvar(i, v, u))

    bounds_lines = [" alpha >= 0"]
    for fv in all_fvars:
        bounds_lines.append(f" {fv} >= 0")

    lp  = "Maximize\n"
    lp += lines_obj[0] + "\n"
    lp += "Subject to\n"
    lp += "\n".join(lines_subj) + "\n"
    lp += "Bounds\n"
    lp += "\n".join(bounds_lines) + "\n"
    lp += "End\n"
    return lp

# ── GLPK solver ───────────────────────────────────────────────────────────────

def solve():
    """Run glpsol, return (alpha, flows) where flows[i][(u,v)] = flow value."""
    lp_text = build_lp()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.lp', delete=False) as lp_f:
        lp_f.write(lp_text)
        lp_path = lp_f.name

    sol_path = lp_path.replace('.lp', '.sol')

    try:
        subprocess.run(
            ['glpsol', '--lp', lp_path, '--sol', sol_path],
            check=True, capture_output=True
        )

        alpha = 0.0
        flows = [{} for _ in demands]

        with open(sol_path) as sol_f:
            for line in sol_f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                name = parts[1]
                try:
                    val = float(parts[3])
                except (ValueError, IndexError):
                    continue

                if name == 'alpha':
                    alpha = val
                elif name.startswith('f_'):
                    tokens = name.split('_')
                    # f_{i}_{u}_{v}
                    i = int(tokens[1])
                    u = tokens[2]
                    v = tokens[3]
                    flows[i][(u, v)] = val

        return alpha, flows
    finally:
        os.unlink(lp_path)
        if os.path.exists(sol_path):
            os.unlink(sol_path)

# ── --lp mode ─────────────────────────────────────────────────────────────────

if args.lp:
    print(build_lp(), end='')
    exit(0)

# ── --print mode ──────────────────────────────────────────────────────────────

if getattr(args, 'print'):
    alpha, flows = solve()
    for i, d in enumerate(demands):
        goodput = round(alpha * d['rate'], 4)
        print(f"The best goodput for flow demand #{i+1} is {goodput} Mbps")
    exit(0)

# ── Mininet emulation ─────────────────────────────────────────────────────────

alpha, flows = solve()

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')
        self.cmd('sysctl -w net.mpls.platform_labels=1048575')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super().terminate()

class NetworkTopo(Topo):
    def build(self, **opts):
        for r_id in routers:
            self.addNode(r_id, cls=LinuxRouter, ip=None)

        for h_id, host in hosts.items():
            iface = next(iter(host.values()))
            r_id = networks[iface['net_str']]['routers'][0]
            _, r_iface = find_iface(r_id, iface['net_str'])
            self.addHost(h_id, ip=None, defaultRoute=f"via {r_iface['address']}")

        switches = {}
        switch_idx = 1

        for net_str, net in networks.items():
            sw = self.addSwitch(f's{switch_idx}', cls=OVSBridge)
            switches[net_str] = sw
            switch_idx += 1

            for r_id in net['routers']:
                i_id, iface = find_iface(r_id, net_str)
                self.addLink(
                    r_id, sw,
                    cls=TCLink,
                    bw=net['cost'],
                    intfName1=f'{r_id}-{i_id}',
                    params1={'ip': f"{iface['address']}/{net['prefix']}"}
                )

        for h_id, host in hosts.items():
            for i_id, iface in host.items():
                net_str = iface['net_str']
                self.addLink(
                    h_id, switches[net_str],
                    intfName1=f'{h_id}-{i_id}',
                    params1={'ip': f"{iface['address']}/{networks[net_str]['prefix']}"}
                )

mn = Mininet(topo=NetworkTopo(), controller=None)
mn.start()

# Enable MPLS on every router interface
for r_id in routers:
    r_node = mn.get(r_id)
    for i_id in routers[r_id]:
        r_node.cmd(f'sysctl -w net.mpls.conf.{r_id}-{i_id}.input=1')

# Set up MPLS forwarding for each demand
# Label i+1 is reserved for demand i
for i, d in enumerate(demands):
    label     = i + 1
    src_r     = host_router(d['src'])
    dst_r     = host_router(d['dst'])
    flow      = flows[i]
    goodput   = alpha * d['rate']

    for (u, v), fval in flow.items():
        if fval < 1e-6:
            continue
        r_node = mn.get(u)

        # Find the interface/address toward v
        shared_net = None
        for net_str, net in networks.items():
            if u in net['routers'] and v in net['routers']:
                shared_net = net_str
                break
        if shared_net is None:
            continue
        _, v_iface = find_iface(v, shared_net)
        next_ip = v_iface['address']

        if u == src_r:
            # Ingress: push label and forward
            dst_host_iface = next(iter(hosts[d['dst']].values()))
            dst_ip = dst_host_iface['address']
            r_node.cmd(f'ip route add {dst_ip}/32 encap mpls {label} via {next_ip}')
        elif v == dst_r:
            # Penultimate hop: forward with label (dst router will pop)
            r_node.cmd(f'ip -f mpls route add {label} via inet {next_ip}')
        else:
            # Transit: swap/forward
            r_node.cmd(f'ip -f mpls route add {label} via inet {next_ip}')

    # Egress (destination router): pop label, deliver locally
    dst_node = mn.get(dst_r)
    dst_node.cmd(f'ip -f mpls route add {label} via inet 0.0.0.0')

    # Rate-limit outgoing traffic at the source host
    src_node  = mn.get(d['src'])
    src_iface = next(iter(hosts[d['src']].keys()))
    src_node.cmd(
        f'tc qdisc add dev {d["src"]}-{src_iface} root tbf '
        f'rate {goodput}mbit burst 32kbit latency 400ms'
    )

CLI(mn)
mn.stop()
