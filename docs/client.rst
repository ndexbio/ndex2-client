:py:mod:`~ndex2.client` Module
--------------------------------

The :py:mod:`~ndex2.client` module provides a class :py:class:`~ndex2.client.Ndex2`
with methods to interface with the
`NDEx REST Server <https://home.ndexbio.org/using-the-ndex-server-api>`_
The :py:class:`~ndex2.client.Ndex2` object can be used to access
an NDEx server either anonymously or using a specific user account. For
each NDEx server and user account that you want to use in your script or
application, you create an :py:class:`~ndex2.client.Ndex2` instance.

.. note::
   Not all of the `NDEx REST Server <https://home.ndexbio.org/using-the-ndex-server-api>`_
   is exposed. `Click here to view full API of NDEx REST Server <http://openapi.ndextools.org/>`_

.. autoclass:: ndex2.client.Ndex2
    :members: add_networks_to_networkset, create_networkset, delete_networkset, \
              delete_networks_from_networkset, \
              get_neighborhood, get_neighborhood_as_cx_stream, \
              get_network_ids_for_user, \
              get_network_summaries_for_user, get_user_network_summaries, \
              get_networkset, get_network_set, get_network_summary, \
              get_sample_network, get_task_by_id, get_user_by_username, \
              get_user_network_summaries, grant_network_to_user_by_username, \
              grant_networks_to_group, grant_networks_to_user, \
              make_network_private, make_network_public, \
              get_network_as_cx_stream, save_cx_stream_as_new_network, save_new_network, delete_network, \
              search_networks, set_network_properties, \
              set_network_system_properties, set_read_only, \
              update_cx_network, update_network_group_permission, \
              update_network_profile, update_network_user_permission
