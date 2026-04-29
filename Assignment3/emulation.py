
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


parser = ArgumentParser(description="A tool to define the emulation of a network.", usage=usage)
#parser.add_argument("-h", "--help", help="show this help message and exit", action="store_true")
parser.add_argument("-d", "--draw", help="output a map of the routers in GraphViz format", action="store_true")
parser.add_argument("definition", metavar="FILE")

args = parser.parse_args()

# Read yaml file
stream = open(args.definition, "r")
data = yaml.load(stream, Loader=yaml.Loader)

routers = data['routers']

# Preprocess data to compute network
for r in routers:
    for i in routers[r]:
        addr= [ int(aux) for aux in routers[r][i]['address'].split(".") ]
        mask = [ int(aux) for aux in routers[r][i]['mask'].split(".") ]
        net =  [ addr[i] & mask[i] for i in range(4) ]
        routers[r][i]['net'] = net

print(data)

# Compute adjacency
for r in routers:
    for i in routers[r]:
        routers[r][i]['adj'] = []

adj = {}
for r1 in routers:
    for i1 in routers[r1]:
        for r2 in routers:
            if r1 == r2:
                continue
            for i2 in routers[r2]:
                if routers[r1][i1]["net"] == routers[r2][i2]["net"]:
                    routers[r1][i1]['adj'].append(r2)


for r in routers:
    for i in routers[r]:
        print(f"{r}: {i}: ", routers[r][i]['adj'])

if args.draw:
    out = "graph Network {"
    for r in routers:
        out = out + f"\n\t{r} [shape=circle];"

    for r in routers:
        for i in routers[r]:
            for a in routers[r][i]['adj']:
                out = out + f"\n\t{r} -- {a} [label=1];"

    out = out + "\n}"
    print(out)
