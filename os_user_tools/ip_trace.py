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
    connection = pymysql.connect(user=db_parameters['user'],
                                 password=db_parameters['password'],
                                 host=db_parameters['host'],
                                 database=db_parameters['database'])
    cursor = connection.cursor()
    return cursor


def execute_db_query(cursor, query):
    cursor.execute(query)
    data = cursor.fetchall()
    return data


def floatingip_traces(db_cursors, ip):
    floatingip_traces = []
    query = """SELECT device_id, start_date FROM floatingip_actions
               WHERE ip_address='%s' AND action='associate'""" % ip
    neutron_data = execute_db_query(db_cursors['neutron'], query)
    for instances_details in neutron_data:
        trace_details = {'end': '-'}
        query = """SELECT user_id FROM instances
                   WHERE uuid='%s'""" % instances_details[0]
        user_id = execute_db_query(db_cursors['nova'], query)
        query = """SELECT name FROM user WHERE id='%s'""" % user_id[0][0]
        user_name = execute_db_query(db_cursors['keystone'], query)
        # Deal with the case where the user has been deleted
        if not user_name:
            user_name = user_id
        query = """SELECT start_date FROM floatingip_actions
                   WHERE ip_address='%s' AND action='disassociate'
                   AND device_id='%s'""" % (ip, instances_details[0])
        end_date = execute_db_query(db_cursors['neutron'], query)
        trace_details['device_id'] = instances_details[0]
        trace_details['start'] = instances_details[1]
        trace_details['user_name'] = user_name[0][0]
        if end_date:
            trace_details['end'] = end_date[0][0]
        floatingip_traces.append(trace_details)

    return floatingip_traces


def create_array(ip_traces):
    array = PrettyTable(["device id",
                         "user name",
                         "associating date",
                         "disassociating date"])
    for trace in ip_traces:
        row = []
        row.append(trace['device_id'])
        row.append(trace['user_name'])
        row.append(trace['start'])
        row.append(trace['end'])
        array.add_row(row)
    return array


def main():
    parser = argparse.ArgumentParser(description="Trace IP usage.")
    parser.add_argument('ip', metavar='<IP>', type=str,
                        help='IP address to trac.')
    args = parser.parse_args()
    ip = args.ip

    keystone_config = osconfigfile.OSConfigFile(keystone_conf)
    keystone_db_params = keystone_config.get_mysql_parameters()
    if not keystone_db_params:
        sys.stderr.write("ERROR: Could not find Keystone DB parameters\n")
        sys.exit(1)
    nova_config = osconfigfile.OSConfigFile(nova_conf)
    nova_db_params = nova_config.get_mysql_parameters()
    if not nova_db_params:
        sys.stderr.write("ERROR: Could not find nova DB parameters\n")
        sys.exit(1)
    neutron_config = osconfigfile.OSConfigFile(neutron_conf)
    neutron_db_params = neutron_config.get_mysql_parameters()
    if not neutron_db_params:
        sys.stderr.write("ERROR: Could not find Neutron DB parameters\n")
        sys.exit(1)

    db_cursors = {}
    db_cursors['keystone'] = database_connection(keystone_db_params)
    db_cursors['nova'] = database_connection(nova_db_params)
    db_cursors['neutron'] = database_connection(neutron_db_params)

    ip_traces = floatingip_traces(db_cursors, ip)

    array = create_array(ip_traces)

    print(array)


if __name__ == "__main__":
    main()
