import unittest

import ndex.client as nc

ndex_host = "http://dev2.ndexbio.org"

#
# Python Client APIs tested:
#
#   get_user_by_username
#

class MyTestCase(unittest.TestCase):

    def test_get_user_by_username(self):

        ndex = nc.Ndex(host=ndex_host)

        user_ttt = ndex.get_user_by_username('scratch')
        self.assertTrue(str(user_ttt['externalId']) == '6b8b841c-43d1-11e6-a5c7-06603eb7f303')
        self.assertTrue(str(user_ttt['firstName']) == 'scratch')
        self.assertTrue(str(user_ttt['lastName']) == 'scratch')
        self.assertTrue(str(user_ttt['userName']) == 'scratch')
        self.assertTrue(str(user_ttt['emailAddress']) == 'scratch@example.com')

        user_drh = ndex.get_user_by_username('drh')
        self.assertTrue(str(user_drh['externalId']) == '972e6b69-b3bd-11e4-ae6e-000c29cb28fb')
        self.assertTrue(str(user_drh['firstName']) == 'Dexter')
        self.assertTrue(str(user_drh['lastName']) == 'Pratt')
        self.assertTrue(str(user_drh['userName']) == 'drh')
        self.assertTrue(str(user_drh['emailAddress']) == 'drh@example.com')

if __name__ == '__main__':
    unittest.main()

