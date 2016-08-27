# -*- coding: utf-8 -*-

# Copyright 2016 CNRS and University of Strasbourg
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ConfigParser
import re


class OSConfigFile(object):
    def __init__(self, filename):
        self.config_parser = ConfigParser.ConfigParser()
        self.config_parser.read(filename)

    def get_value(self, section, option):
        try:
            value = self.config_parser.get(section, option)
        except:
            value = None

        return value

    def get_mysql_parameters(self):
        mysql_line = self.get_value('database', 'connection')
        parameters_types = ['user', 'password', 'host', 'database']

        parameters = {}

        if mysql_line: 
            regex = re.compile('^mysql.*//(.*):(.*)@(.*)/(.*)')
            capturing_groups = regex.match(mysql_line).groups()

            if len(capturing_groups) == len(parameters_types):
                parameters = dict(zip(parameters_types, capturing_groups))

        return parameters
