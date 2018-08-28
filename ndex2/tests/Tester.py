import ndex2
from ndex2.NiceCXNetwork import NiceCXNetwork


upload_server = 'dev.ndexbio.org'
upload_username = 'cc.zhang'
upload_password = 'cc.zhang'


niceCx_creatures = NiceCXNetwork()
niceCx_creatures.set_name("Test")
niceCx_creatures.create_node(node_name="Fox")
niceCx_creatures.add_network_attribute(name="Number of trees", values="433434")
print(niceCx_creatures.get_network_attribute("Number of trees"))
upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)