__author__ = 'aarongary'

import ndex2.client as nc
import os
import unittest
import ndex2
import json
import pandas as pd

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestNdex2Release(unittest.TestCase):
    @unittest.skip("Temporary skipping")
    def test_load_from_pandas(self):
        path_to_network = os.path.join(path_this, 'SIMPLE3.txt')

        with open(path_to_network, 'r') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            niceCx.apply_template('public.ndexbio.org', '56cbe15a-5f7e-11e8-a4bf-0ac135e8bacf')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_first(self):

