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
import sys

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient
from novaclient import client as novaclient
from prettytable import PrettyTable


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
                "You must provide the %s " % key +
                "via env[%s].\n" % env
            )
            return None
    if os.environ.has_key('OS_CACERT'):
        verify = os.environ['OS_CACERT']
    else:
        verify = True
    auth = v3.Password(**auth_parameters)
    keystone_session = session.Session(auth=auth, verify=verify)
    return keystone_session


def get_user_details(keystone, username):
    user_details = {}
    for user in keystone.users.list():
        user_info = user.to_dict()
        if user_info['name'] == username:
            user_details['id'] = user_info['id']
            user_details['name'] = user_info['name']
            if 'email' in user_info:
                user_details['email'] = user_info['email']
            else:
                user_details['email'] = ''
            break
    return user_details


def get_user_projects(keystone, user_id):
    user_projects = {}
    for project in keystone.projects.list(user=user_id):
        project_info = {}
        project_info['name'] = project.name
        project_info['description'] = project.description
        user_projects[project.id] = project_info
    return user_projects


def get_user_roles(keystone, user_id, project_id):
    user_roles = []
    for role in keystone.roles.list(user=user_id, project=project_id):
        user_roles.append(role.name)
    return user_roles


def create_array(details, projects):
    array = PrettyTable(["name", "email", "projects", "roles"])
    first_line = True
    row = [details['name'], details['email']]
    if not len(projects):
        row.append('')
        row.append('')
        array.add_row(row)
    for project in projects.values():
        if not first_line:
            row = ['', '']
        else:
            first_line = False
        row.append(project['name'])
        row.append("\n".join(project['roles']))
        array.add_row(row)
    return array


def main():
    parser = argparse.ArgumentParser(description="Display user details.")
    parser.add_argument('username', metavar='<user>', type=str,
                        help='Name of user to display.')
    args = parser.parse_args()
    user = args.username

    keystone_session = get_session()

    if not keystone_session:
        sys.stderr.write('Cannot connect to OpenStack\n')
        sys.exit(1)

    nova = novaclient.Client("2.1", session=keystone_session)
    keystone = keystoneclient.Client(session=keystone_session)

    user_details = get_user_details(keystone, user)
    if not user_details:
        sys.stderr.write("No such user: %s\n" % (user))
        sys.exit(1)

    user_projects = get_user_projects(keystone, user_details['id'])

    for project_id in user_projects:
        user_projects[project_id]['roles'] = get_user_roles(keystone,
                                                            user_details['id'],
                                                            project_id)

    array = create_array(user_details, user_projects)

    print(array)


if __name__ == "__main__":
    main()
