Ndex2 REST client
--------------------------------

The Ndex2 class provides methods to interface with the
`NDEx REST Server API`_  The :py:class:`~ndex2.client.Ndex2` object can be used to access
an `NDEx`_ server either anonymously or using a specific user account. For
each `NDEx`_ server and user account that you want to use in your script or
application, you create an :py:class:`~ndex2.client.Ndex2` instance.

    Example creating anonymous connection:

        .. code-block:: python

            import ndex2.client
            anon_ndex=ndex2.client.Ndex2()

    Example creating connection with username and password:

        .. code-block:: python

            import ndex2.client
            my_account="your account"
            my_password="your password"
            my_ndex=ndex2.client.Ndex2("http://public.ndexbio.org", my_account, my_password)


.. autoclass:: ndex2.client.Ndex2
    :members: add_networks_to_networkset, create_networkset, delete_network, delete_networks_from_networkset, delete_networkset, get_neighborhood, get_neighborhood_as_cx_stream, get_network_as_cx_stream, get_network_aspect_as_cx_stream, get_network_ids_for_user, get_networkset, get_network_set, get_network_summary, get_sample_network, get_task_by_id, get_user_by_username, get_user_network_summaries, grant_network_to_user_by_username, grant_networks_to_group, grant_networks_to_user, make_network_private, make_network_public, save_cx_stream_as_new_network, save_new_network, search_networks, set_network_properties, set_network_system_properties, set_read_only, update_cx_network, update_network_group_permission, update_network_profile, update_network_user_permission

.. _NDEx REST Server API: http://www.home.ndexbio.org/using-the-ndex-server-api
.. _NDEx: https://ndexbio.org