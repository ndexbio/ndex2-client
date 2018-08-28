import ndex2
import pandas as pd
from ndex2.NiceCXNetwork import NiceCXNetwork

file =open("sample_edges.txt", "r")
file_info = file.read()
lineiterator = file_info.splitlines()
niceCx = NiceCXNetwork()
list_of_created_nodes = {}
counter = 0
edge_size = 0


upload_server = 'dev.ndexbio.org'
upload_username = 'cc.zhang'
upload_password = 'cc.zhang'

for line in lineiterator:
    data = line.split("    ")
    if not list_of_created_nodes.get(data[0]):
        id_source = niceCx.create_node(node_name=data[0])
        list_of_created_nodes[data[0]] = counter
        counter = counter + 1
    else:
        id_source = list_of_created_nodes.get(data[0])


    if not list_of_created_nodes.get(data[1]):
        id_target = niceCx.create_node(node_name=data[1])
        list_of_created_nodes[data[1]] = counter
        counter = counter + 1
    else:
        id_target = list_of_created_nodes.get(data[1])

    niceCx.create_edge(edge_source=id_source, edge_target=id_target, edge_interaction= data[2])
    edge_size = edge_size + 1

for name, id in list_of_created_nodes.items():
    niceCx.add_node_attribute(property_of=id, name='alias', values='this is a node')

for i in range(edge_size):
    niceCx.add_edge_attribute(property_of=i, name='weight', values='this is an edge')

niceCx.upload_to(upload_server, upload_username, upload_password)

print(niceCx)