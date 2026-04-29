
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
            aux["routers"] = []
            aux["routers"].append(r_id)
            networks[net_str] = aux

for n in networks.values():
    if n["cost"] == -1:
        n["cost"] = 1

#print(data)

# # 1.  Compute adjacency
# # 1.1 Init adjacency arrays
# for router in routers.values():
#     for interface in router.values():
#         interface['adj'] = []

# # 1.2 Fill in adjacency ararys
# # The array for a given interface contains a dict with id: string id of the
# # router to which the interface connects and cost: int cost of the link.
# adj = {}
# print_list = []
# for r1_id, r1 in routers.items():
#     for i1 in r1.values():
#         for r2_id, r2 in routers.items():
#             if r1 == r2:
#                 continue
#             for i2 in r2.values():
#                 if i1["net"] == i2["net"]:
#                     aux = {}
#                     cost = int(i1["cost"]) if "cost" in i1 else 1
#                     aux["cost"] = cost
#                     aux["id"] = r2_id
#                     aux["net"] = i1["net"]
#                     i1['adj'].append(aux)

#                     print_aux = {}
#                     print_aux["r1"] = r1_id
#                     print_aux["r2"] = r2_id
#                     print_aux["cost"] = cost
#                     print_list.append(print_aux)

# 1. Print adjacency
# for r_id, r in routers.items():
#     for i_id, i in r.items():
#         print(f"{r_id}: {i_id}: ", i['adj'])

# 2. Draw graph
if args.draw:
    out = "graph Network {"
    for r in routers:
        out = out + f"\n\t{r} [shape=circle];"

    # for l in print_list:
    #     out = out + f"\n\t{l["r1"]} -- {l["r2"]} [label={l["cost"]}]"

    for net in networks.values():
        n = len(net["routers"])
        for i in range(n-1):
            for j in range(i+1, n):
                out = out + f"\n\t{net["routers"][i]} -- {net["routers"][j]} [label={net["cost"]}];"

    # seen = {}
    # for r_id, r in routers.items():
    #     for i in r.values():
    #         for a in i['adj']:
    #             if i["net_str"] in seen:
    #                 continue
    #             out = out + f"\n\t{r_id} -- {a["id"]} [label={a["cost"]}];"
    #             seen[i["net_str"]] = True

    out = out + "\n}"
    print(out)
