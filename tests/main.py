import unittest
import _conf
import server
import mocker




class ServerTest(mocker.MockerTestCase):

    UNID = "~testalias/testdoc"
    SOURCE = u"""Test Document
=============
"""

    def setUp(self):
        self.mocker = mocker.Mocker()
        self.store = self.mocker.mock()
        builders = [
                'dotmpe.du.builder.bluelines',
                'dotmpe.du.builder.dotmpe_v5',
                'test.aux.testbuilder',
            ]
        self.server = server.BlueLines(self.store, builders, [])

    def test_server(self):
        assert not self.server.alias

    def test_process(self):
        self.server.process(ServerTest.SOURCE, ServerTest.UNID,
                settings_overrides={'build':'test.aux.testbuilder.Builder'})

    def test_render(self):
        self.server.publish(ServerTest.UNID)


class ServerTestOld(unittest.TestCase):

    def _test_allowed_builders(self):
        builders = [
                'dotmpe.du.builder.bluelines',
                'dotmpe.du.builder.dotmpe_v5',
                'test.aux.testbuilder',
            ]
        srv = server.BlueLines(None, builders, [])
        for package_name in ('bluelines', 'dotmpe_v5', 'testbuilder'):
            assert package_name in srv.builder
            assert package_name in srv.package
            assert not srv.package[package_name].endswith(package_name)
        assert srv.package['bluelines'] == 'dotmpe.du.builder'
        assert srv.package['testbuilder'] == 'test.aux'            
        assert srv._BlueLines__builder('bluelines.Document')
        assert srv.builder['bluelines'].items()[0][0] == 'Document'
        assert srv._BlueLines__builder('bluelines.AliasFormPage')
        assert srv.builder['bluelines'].items()[1][0] == 'AliasFormPage'
        assert srv._BlueLines__builder('dotmpe_v5.Builder')
        assert srv._BlueLines__builder('testbuilder.Builder')
        assert 'Builder' in srv.builder['testbuilder']
        assert srv._BlueLines__builder('testbuilder.Site')
        self.assertRaises(Exception, lambda:srv._BlueLines__builder(
            'test.aux.testbuilder.Site'))

if __name__ == '__main__':
    unittest.main()
