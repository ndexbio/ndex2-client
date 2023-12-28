import os
import unittest
import pandas as pd
from ndex2.cx2 import RawCX2NetworkFactory
from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory
from ndex2.cx2 import CX2NetworkPandasDataFrameFactory


class TestPandasDataFrameToCX2NetworkFactory(unittest.TestCase):

    def test_conversion_to_cx2network(self):
        data = {'source': [1, 2], 'target': [2, 3], 'edge_attr': ['a', 'b']}
        df = pd.DataFrame(data)
        factory = PandasDataFrameToCX2NetworkFactory()
        network = factory.get_cx2network(df)

        self.assertEqual(len(network.get_edges()), 2)
        self.assertIn(1, network.get_nodes())
        self.assertIn(2, network.get_nodes())
        self.assertIn(3, network.get_nodes())

    def test_conversion_to_cx2network_with_edge_and_node_attributes(self):
        data = {'source': [1, 2], 'target': [2, 3],
                'weight': [1.0, 0.9],
                'source_size': [5, 6], 'target_size': [6, 7]}
        df = pd.DataFrame(data)

        # Creating an instance of PandasDataFrameToCX2NetworkFactory
        factory = PandasDataFrameToCX2NetworkFactory()

        # Converting DataFrame to CX2Network
        cx2_network = factory.get_cx2network(df)
        self.assertTrue(3, len(cx2_network.get_nodes()))
        self.assertTrue(2, len(cx2_network.get_edges()))

    def get_node_matching_name(self, cx2network=None, name=None):
        """
        Gets 1st node matching name
        :param node_obj:
        :param name:
        :return:
        """
        for node_id, node_obj in cx2network.get_nodes().items():
            if 'v' not in node_obj:
                continue
            if 'name' not in node_obj['v']:
                continue
            if node_obj['v']['name'] == name:
                return node_obj
        return None

    def test_roundtrip_glypican2_network(self):
        glypican_two = os.path.join(os.path.dirname(__file__), 'data', 'glypican2.cx2')
        fac = RawCX2NetworkFactory()
        cx2net = fac.get_cx2network(glypican_two)

        orig_mkd_node = self.get_node_matching_name(cx2network=cx2net, name='MDK')
        orig_gpc_node = self.get_node_matching_name(cx2network=cx2net, name='GPC2')
        orig_edge = cx2net.get_edges()[0]
        pandafac = CX2NetworkPandasDataFrameFactory()
        df = pandafac.get_dataframe(cx2net)

        panda2cxfac = PandasDataFrameToCX2NetworkFactory()

        rt_cx2net = panda2cxfac.get_cx2network(df)
        self.assertEqual(None, rt_cx2net.get_name())
        self.assertEqual(2, len(rt_cx2net.get_nodes()))
        mdk_node = self.get_node_matching_name(cx2network=rt_cx2net, name='MDK')
        self.assertEqual(orig_mkd_node['v'], mdk_node['v'])
        self.assertEqual(None, mdk_node['z'])
        self.assertAlmostEqual(-398.3511334928659, mdk_node['x'], 0.01)
        self.assertAlmostEqual(70.71067799518471, mdk_node['y'], 0.01)

        gpc_node = self.get_node_matching_name(cx2network=rt_cx2net, name='GPC2')
        self.assertEqual(orig_gpc_node['v'], gpc_node['v'])
        self.assertEqual(None, gpc_node['z'])
        self.assertAlmostEqual(-353.49370090105185, gpc_node['x'], 0.01)
        self.assertAlmostEqual(70.71067822788493, gpc_node['y'], 0.01)

        self.assertEqual(1, len(rt_cx2net.get_edges()))
        self.assertEqual(orig_edge['v'], rt_cx2net.get_edges()[0]['v'])


if __name__ == '__main__':
    unittest.main()
