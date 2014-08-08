# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import os
import translator.toscalib.utils.yamlparser

log = logging.getLogger('tosca')


class EntityType(object):
    '''Base class for TOSCA elements.'''

    SECTIONS = (DERIVED_FROM, PROPERTIES, ATTRIBUTES, REQUIREMENTS,
                INTERFACES, CAPABILITIES) = \
               ('derived_from', 'properties', 'attributes', 'requirements',
                'interfaces', 'capabilities')

    '''TOSCA definition file.'''
    TOSCA_DEF_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "TOSCA_definition.yaml")

    loader = translator.toscalib.utils.yamlparser.load_yaml

    TOSCA_DEF = loader(TOSCA_DEF_FILE)

    RELATIONSHIP_TYPE = (DEPENDSON, HOSTEDON, CONNECTSTO, ATTACHTO) = \
                        ('tosca.relationships.DependsOn',
                         'tosca.relationships.HostedOn',
                         'tosca.relationships.ConnectsTo',
                         'tosca.relationships.AttachTo')

    NODE_PREFIX = 'tosca.nodes.'
    RELATIONSHIP_PREFIX = 'tosca.relationships.'
    CAPABILITY_PREFIX = 'tosca.capabilities.'
    INTERFACE_PREFIX = 'tosca.interfaces.node.'

    def derived_from(self, defs):
        '''Return a type this type is derived from.'''
        return self.entity_value(defs, 'derived_from')

    def entity_value(self, defs, key):
        if key in defs:
            return defs[key]

    def get_value(self, ndtype, defs=None, parent=None):
        value = None
        if defs is None:
            defs = self.defs
        if ndtype in defs:
            value = defs[ndtype]
        if parent and not value:
            p = self.parent_type
            while value is None:
                #check parent node
                if not p:
                    break
                if p and p.type == 'tosca.nodes.Root':
                    break
                value = p.get_value(ndtype)
                p = p.parent_type
        return value
