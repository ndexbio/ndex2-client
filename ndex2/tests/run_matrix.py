import numpy as np
import ndex2
import os
import time

path_this = os.path.dirname(os.path.abspath(__file__))

params = {
    'name': 'SIM MATRIX TEST',
    'ndex_server': 'http://dev.ndexbio.org',
    'ndex_user': 'scratch3',
    'ndex_pass': 'scratch3'
}

X = np.array(
    [[1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
     [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
     [0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0],
     [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
     [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0],
     [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0],
     [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
     [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]]
)

X_cols = ['ABC', 'DEF', 'GHI', 'XYZ', 'ABC1', 'DEF1', 'GHI1', 'XYZ1', 'ABC2', 'DEF2',
          'GHI2', 'XYZ2', 'ABC3', 'DEF3', 'GHI3']

X_rows = ['ABC', 'DEF', 'GHI', 'XYZ', 'ABC1', 'DEF1', 'GHI1', 'XYZ1', 'ABC2', 'DEF2',
          'GHI2', 'XYZ2', 'ABC3', 'DEF3', 'GHI3']

new_network_url = ndex2.load_matrix_to_ndex(X, X_cols, X_rows, params['ndex_server'], params['ndex_user'],
                                            params['ndex_pass'], 'matrix test')

uuid = new_network_url.split('/')[-1]

time.sleep(2)
new_network, x_cols, y_rows = ndex2.get_matrix_from_ndex(params['ndex_server'], params['ndex_user'],
                                                         params['ndex_pass'], uuid)
print(new_network)
