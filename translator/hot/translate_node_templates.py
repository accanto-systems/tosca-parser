#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from translator.hot.tosca.tosca_block_storage import ToscaBlockStorage
from translator.hot.tosca.tosca_block_storage_attachment import (
    ToscaBlockStorageAttachment
    )
from translator.hot.tosca.tosca_compute import ToscaCompute
from translator.hot.tosca.tosca_database import ToscaDatabase
from translator.hot.tosca.tosca_dbms import ToscaDbms
from translator.hot.tosca.tosca_webserver import ToscaWebserver
from translator.hot.tosca.tosca_wordpress import ToscaWordpress
from translator.toscalib.relationship_template import RelationshipTemplate

SECTIONS = (TYPE, PROPERTIES, REQUIREMENTS, INTERFACES, LIFECYCLE, INPUT) = \
           ('type', 'properties', 'requirements',
            'interfaces', 'lifecycle', 'input')

# TODO(anyone):  the following requirement names should not be hard-coded
# in the translator.  Since they are basically arbitrary names, we have to get
# them from TOSCA type definitions.
# To be fixed with the blueprint:
# https://blueprints.launchpad.net/heat-translator/+spec/tosca-custom-types
REQUIRES = (CONTAINER, DEPENDENCY, DATABASE_ENDPOINT, CONNECTION, HOST) = \
           ('container', 'dependency', 'database_endpoint',
            'connection', 'host')

INTERFACES_STATE = (CREATE, START, CONFIGURE, START, DELETE) = \
                   ('create', 'stop', 'configure', 'start', 'delete')

# dict to look up HOT translation class,
# TODO(replace with function to scan the classes in translator.hot.tosca)
TOSCA_TO_HOT_TYPE = {'tosca.nodes.Compute': ToscaCompute,
                     'tosca.nodes.WebServer': ToscaWebserver,
                     'tosca.nodes.DBMS': ToscaDbms,
                     'tosca.nodes.Database': ToscaDatabase,
                     'tosca.nodes.WebApplication.WordPress': ToscaWordpress,
                     'tosca.nodes.BlockStorage': ToscaBlockStorage}

TOSCA_TO_HOT_REQUIRES = {'container': 'server', 'host': 'server',
                         'dependency': 'depends_on', "connects": 'depends_on'}

TOSCA_TO_HOT_PROPERTIES = {'properties': 'input'}


class TranslateNodeTemplates():
    '''Translate TOSCA NodeTemplates to Heat Resources.'''

    def __init__(self, nodetemplates, hot_template):
        self.nodetemplates = nodetemplates
        self.hot_template = hot_template

    def translate(self):
        return self._translate_nodetemplates()

    def _translate_nodetemplates(self):
        hot_resources = []
        hot_lookup = {}

        attachment_suffix = 0
        # Copy the TOSCA graph: nodetemplate
        for node in self.nodetemplates:
            hot_node = TOSCA_TO_HOT_TYPE[node.type](node)
            hot_resources.append(hot_node)
            hot_lookup[node] = hot_node

            # BlockStorage Attachment is a special case,
            # which doesn't match to Heat Resources 1 to 1.
            if node.type == "tosca.nodes.Compute":
                volume_name = None
                reuirements = node.requirements
                # Find the name of associated BlockStorage node
                for requires in reuirements:
                    for value in requires.values():
                        for n in self.nodetemplates:
                            if n.name == value:
                                volume_name = value
                                break
                attachment_suffix = attachment_suffix + 1
                attachment_node = self._get_attachment_node(node,
                                                            attachment_suffix,
                                                            volume_name)
                if attachment_node:
                    hot_resources.append(attachment_node)

        # Handle life cycle operations: this may expand each node
        # into multiple HOT resources and may change their name
        lifecycle_resources = []
        for resource in hot_resources:
            expanded = resource.handle_life_cycle()
            if expanded:
                lifecycle_resources += expanded
        hot_resources += lifecycle_resources

        # Copy the initial dependencies based on the relationship in
        # the TOSCA template
        for node in self.nodetemplates:
            for node_depend in node.related_nodes:
                # if the source of dependency is a server, add dependency
                # as properties.get_resource
                if node_depend.type == 'tosca.nodes.Compute':
                    hot_lookup[node].properties['server'] = \
                        {'get_resource': hot_lookup[node_depend].name}
                # for all others, add dependency as depends_on
                else:
                    hot_lookup[node].depends_on.append(hot_lookup[node_depend].
                                                       top_of_chain())

        # handle hosting relationship
        for resource in hot_resources:
            resource.handle_hosting()

        # Handle properties
        for resource in hot_resources:
            resource.handle_properties()

        return hot_resources

    def _get_attachment_node(self, node, suffix, volume_name):
        attach = False
        ntpl = self.nodetemplates
        for key, value in node.relationship.items():
            if key.type == 'tosca.relationships.AttachTo':
                if value.type == 'tosca.nodes.BlockStorage':
                    attach = True
            if attach:
                for req in node.requirements:
                    for rkey, rval in req.items():
                        if rkey == 'type':
                            rval = rval + "_" + str(suffix)
                            att = RelationshipTemplate(req, rval, None)
                            hot_node = ToscaBlockStorageAttachment(att, ntpl,
                                                                   node.name,
                                                                   volume_name
                                                                   )
                            return hot_node
