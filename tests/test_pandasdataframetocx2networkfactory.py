import os
import unittest
import pandas as pd
from ndex2.cx2 import RawCX2NetworkFactory
from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory
from ndex2.cx2 import PandasDataFrameFactory


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

    def test_roundtrip_glypican2_network(self):
        glypican_two = os.path.join(os.path.dirname(__file__), 'data', 'glypican2.cx2')
        fac = RawCX2NetworkFactory()
        cx2net = fac.get_cx2network(glypican_two)

        pandafac = PandasDataFrameFactory()
        df = pandafac.get_dataframe(cx2net)

        panda2cxfac = PandasDataFrameToCX2NetworkFactory()

        rt_cx2net = panda2cxfac.get_cx2network(df)
        self.assertEqual('', rt_cx2net.get_name())


if __name__ == '__main__':
    unittest.main()
