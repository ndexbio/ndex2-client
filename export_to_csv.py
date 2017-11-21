__author__ = 'aarongary'

from nicecxModel.NiceCXNetwork import NiceCXNetwork

niceCx = NiceCXNetwork()

#================================
# Load network from ndex server
#================================
niceCx.create_from_server('public.ndexbio.org', None, None, 'dfba0dfb-6192-11e5-8ac5-06603eb7f303')

#=============================
# convert to pandas dataframe
#=============================
my_pd = niceCx.to_pandas_dataframe()

#=====================
# Export to csv file
#=====================
my_pd.to_csv('CXExport.csv', sep=',')

print('Done')

