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
from datetime import datetime
import os
from prettytable import PrettyTable
import pymysql
import sys

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient

import osconfigfile

nova_conf = '/etc/nova/nova.conf'
neutron_conf = '/etc/neutron/neutron.conf'


def get_session():
    auth_keys = {
        'auth_url': 'OS_AUTH_URL',
        'username': 'OS_USERNAME',
        'password': 'OS_PASSWORD',
        'project_name': 'OS_TENANT_NAME',
        'user_domain_name': 'OS_USER_DOMAIN_NAME',
        'project_domain_name': 'OS_PROJECT_DOMAIN_NAME'
    }
    auth_parameters = {}
    for (key, env) in auth_keys.items():
        try:
            auth_parameters[key] = os.environ[env]
        except KeyError:
            sys.stderr.write(
                "If you want to display the username, you must provide " +
                "the %s via env[%s].\n" % (key, env)
            )
            return None
    if OS_CACERT in os.environ:
        verify = os.environ['OS_CACERT']
    else:
        verify = True
    auth = v3.Password(**auth_parameters)
    keystone_session = session.Session(auth=auth, verify=verify)
    return keystone_session


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


def get_username(keystone, user_id):
    try:
        user_name = keystone.users.get(user_id).name
    except:
        user_name = user_id
    return user_name


def floatingip_traces(db_cursors, ip, after_date=None, before_date=None):
    floatingip_traces = []
    query = """SELECT device_id, start_date FROM floatingip_actions
               WHERE ip_address='%s' AND action='associate'""" % ip
    if before_date:
        query = query + """ AND start_date < '%s'""" % before_date
    neutron_data = execute_db_query(db_cursors['neutron'], query)

    keystone_session = get_session()
    keystone = keystoneclient.Client(session=keystone_session)

    for instances_details in neutron_data:
        trace_details = {'end': '-'}
        query = """SELECT user_id FROM instances
                   WHERE uuid='%s'""" % instances_details[0]
        user_id = execute_db_query(db_cursors['nova'], query)

        user_name = get_username(keystone, user_id[0][0])

        query = """SELECT start_date FROM floatingip_actions
                   WHERE ip_address='%s' AND action='disassociate'
                   AND device_id='%s'""" % (ip, instances_details[0])
        end_date = execute_db_query(db_cursors['neutron'], query)
        if after_date and end_date:
            end_datetime = end_date[0][0]
            if end_datetime < after_date:
                continue
        trace_details['device_id'] = instances_details[0]
        trace_details['start'] = instances_details[1]
        trace_details['user_name'] = user_name
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


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def main():
    parser = argparse.ArgumentParser(description="Trace IP usage.")
    parser.add_argument('ip', metavar='<IP>', type=str,
                        help='IP address to trace.')
    parser.add_argument('-a', '--after', metavar='YYYY-MM-DD',
                        type=valid_date, required=False,
                        help='Display only IP disassociated after this date.')
    parser.add_argument('-b', '--before', metavar='YYYY-MM-DD',
                        type=valid_date, required=False,
                        help='Display only IP associated before this date.')
    args = parser.parse_args()
    ip = args.ip
    before = args.before
    after = args.after

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
    db_cursors['nova'] = database_connection(nova_db_params)
    db_cursors['neutron'] = database_connection(neutron_db_params)

    ip_traces = floatingip_traces(db_cursors, ip,
                                  after_date=after, before_date=before)

    array = create_array(ip_traces)

    print(array)


if __name__ == "__main__":
    main()
