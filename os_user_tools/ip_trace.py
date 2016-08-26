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

import argparse
import os
from prettytable import PrettyTable
import pymysql
import sys

import osconfigfile


keystone_conf = '/etc/keystone/keystone.conf'
nova_conf = '/etc/nova/nova.conf'
neutron_conf = '/etc/neutron/neutron.conf'


def database_connection(db_parameters):
    pass


def execute_db_query(cursor, query):
    pass


def floatingip_traces(db_cursors, floatingip):
    pass


def create_array(ip_hystoric):
    pass


def main():
    parser = argparse.ArgumentParser(description="Trace IP usage.")
    parser.add_argument('ip', metavar='<IP>', type=str,
                        help='IP address to trac.')
    args = parser.parse_args()
    ip = args.ip


if __name__ == "__main__":
    main()
