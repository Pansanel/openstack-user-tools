## Introduction ##

The openstack-user-tools project aims to provide a set of Python programs
for helping day-to-day OpenStack operations.

The following tools are available:

* os-user-info (display user details)
* os-ip-trace (display the usage of an IP over the time)

## Usage ##

### os-user-info ###
The os-user-info script displays the following details about a user:

* e-mail address
* project memberships
* associated roles

```
usage: os-user-info [-h] <user>

Display user details.

positional arguments:
  <user>      Name of user to display.

optional arguments:
  -h, --help  show this help message and exit
```


### os-ip-trace ###

This script requires the [OpenStack triggers](https://github.com/FranceGrilles/openstack-triggers) to be installed. The usage of os-ip-trace is the following:

```
usage: os-ip-trace [-h] <IP>

Trace IP usage.

positional arguments:
  <IP>        IP address to trac.

optional arguments:
  -h, --help  show this help message and exit
```
