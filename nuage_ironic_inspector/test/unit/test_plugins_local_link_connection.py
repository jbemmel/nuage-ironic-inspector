# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from oslo_config import cfg

from ironic_inspector import node_cache
from ironic_inspector.test import base as test_base
from ironic_inspector import utils
from nuage_ironic_inspector.plugins import local_link_connection


class TestNuageLocalLinkConnectionHook(test_base.NodeTest):
    hook = local_link_connection.NuageLocalLinkConnectionHook()

    def setUp(self):
        super(TestNuageLocalLinkConnectionHook, self).setUp()
        self.data = {
            'inventory': {
                'interfaces': [{
                    'name': 'enp2s0', 'mac_address': '0c:c4:7a:4a:f1:82',
                    'ipv4_address': '192.168.10.12',
                    'lldp': [
                        (0, ''),
                        (1, '046854ed016d00'),
                        (2, '073337383437303430'),
                        (3, '0079'),
                        (4, '312d4769672045746865726e657420534650'),
                        (5, '7673672d69726f6e6963'),
                        (7, '00140014'),
                        (8, '05010a1efe020200000001280000000100000003000000'
                            '060000000100000004000000010000197f000000010000'
                            '001200000001')]
                }],
                'cpu': 1,
                'disks': 1,
                'memory': 1
            },
            'all_interfaces': {
                'enp2s0': {},
            }
        }

        llc = {
            'port_id': '56'
        }

        ports = [mock.Mock(spec=['address', 'uuid', 'local_link_connection'],
                           address=a, local_link_connection=llc)
                 for a in ('0c:c4:7a:4a:f1:82',)]
        self.node_info = node_cache.NodeInfo(uuid=self.uuid, started_at=0,
                                             node=self.node, ports=ports)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_expected_data(self, mock_patch):
        patches = [
            {'path': '/local_link_connection/port_id',
             'value': '1/2/3', 'op': 'add'},
            {'path': '/local_link_connection/switch_id',
             'value': '68:54:ed:01:6d:00', 'op': 'add'},
            {'path': '/local_link_connection/switch_info',
             'value': '10.30.254.2', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_invalid_chassis_id_subtype(self, mock_patch):
        # First byte of TLV value is processed to calculate the subtype for the
        # chassis ID, Subtype 5 ('05...') isn't a subtype supported by this
        # plugin, so we expect it to skip this TLV.
        self.data['inventory']['interfaces'][0]['lldp'][1] = (
            1, '05885a92ec5459')
        patches = [
            {'path': '/local_link_connection/port_id',
             'value': '1/2/3', 'op': 'add'},
            {'path': '/local_link_connection/switch_info',
             'value': '10.30.254.2', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_invalid_port_id_subtype(self, mock_patch):
        # First byte of TLV value is processed to calculate the subtype for the
        # port ID, Subtype 6 ('06...') isn't a subtype supported by this
        # plugin, so we expect it to skip this TLV.
        self.data['inventory']['interfaces'][0]['lldp'][2] = (
            2, '0645746865726e6574312f3138')
        patches = [
            {'path': '/local_link_connection/switch_id',
             'value': '68:54:ed:01:6d:00', 'op': 'add'},
            {'path': '/local_link_connection/switch_info',
             'value': '10.30.254.2', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_port_id_subtype_mac(self, mock_patch):
        self.data['inventory']['interfaces'][0]['lldp'][2] = (
            2, '03885a92ec5458')
        patches = [
            {'path': '/local_link_connection/port_id',
             'value': '88:5a:92:ec:54:58', 'op': 'add'},
            {'path': '/local_link_connection/switch_id',
             'value': '68:54:ed:01:6d:00', 'op': 'add'},
            {'path': '/local_link_connection/switch_info',
             'value': '10.30.254.2', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_lldp_none(self, mock_patch):
        self.data['inventory']['interfaces'][0]['lldp'] = None
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_interface_not_in_all_interfaces(self, mock_patch):
        self.data['all_interfaces'] = {}
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_interface_not_in_ironic(self, mock_patch):
        self.node_info._ports = {}
        patches = []
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)

    def test_no_inventory(self):
        del self.data['inventory']
        self.assertRaises(utils.Error, self.hook.before_update,
                          self.data, self.node_info)

    @mock.patch.object(node_cache.NodeInfo, 'patch_port')
    def test_no_overwrite(self, mock_patch):
        cfg.CONF.set_override('overwrite_existing', False, group='processing')
        patches = [
            {'path': '/local_link_connection/switch_id',
             'value': '68:54:ed:01:6d:00', 'op': 'add'},
            {'path': '/local_link_connection/switch_info',
             'value': '10.30.254.2', 'op': 'add'},
        ]
        self.hook.before_update(self.data, self.node_info)
        self.assertCalledWithPatch(patches, mock_patch)
