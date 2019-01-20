#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Isawan Millican <admin@isawan.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: lxd_storage_pool
short_description: Manage LXD Storage pools
description:
  - Management of LXD storage pools
author: "Isawan Millican (@Isawan)"
options:
    name:
        description:
          - Name of a storage pool.
        required: true
    config:
        description:
          - 'The config for the storage pool (e.g. {"size": "20GB"}).
            See
            U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10storage-pools)'
          - If the container already exists and its "config" value in metadata
            obtained from
            GET /1.0/storage-pools/<name>
            U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10storage-pools)
            are different, they this module tries to apply the configurations.
          - Not all config values are supported to apply the existing container.
            Maybe you need to delete and recreate a container.
        required: false
    state:
        choices:
          - present
          - absent
        description:
          - Define the state of a container.
        required: false
        default: started
    timeout:
        description:
          - A timeout for changing the state of the container.
          - This is also used as a timeout for waiting until IPv4 addresses
            are set to the all network interfaces in the container after
            starting or restarting.
        required: false
        default: 30
    url:
        description:
          - The unix domain socket path or the https URL for the LXD server.
        required: false
        default: unix:/var/lib/lxd/unix.socket
    key_file:
        description:
          - The client certificate key file path.
        required: false
        default: '"{}/.config/lxc/client.key" .format(os.environ["HOME"])'
    cert_file:
        description:
          - The client certificate file path.
        required: false
        default: '"{}/.config/lxc/client.crt" .format(os.environ["HOME"])'
    trust_password:
        description:
          - The client trusted password.
          - You need to set this password on the LXD server before
            running this module using the following command.
            lxc config set core.trust_password <some random password>
            See U(https://www.stgraber.org/2016/04/18/lxd-api-direct-interaction/)
          - If trust_password is set, this module send a request for
            authentication before sending any requests.
        required: false
notes:
  - Storage pool must have a unique name. If you attempt to create a storage
    pool with a name that already existed in the users namespace the module
    will simply return as "unchanged".
"""

EXAMPLES = """

"""

RETURN = """

"""
import datetime
import os
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.lxd import LXDClient, LXDClientException


def _pool_exists(client, name):
    pools_present = client.do("GET", "/1.0/storage-pools")
    return any(name == os.path.basename(pool) for pool in pools_present)


def _create_new_pool(client, module):
    return


def main():
    """Ansible Main module"""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type=u"str", required=True),
            driver=dict(choices=[u"dir","lvm","btrfs","zfs","ceph"]),
            config=dict(type=u"dict"),
            state=dict(choices=[u"present", "absent"], default=u"present"),
            url=dict(type=u"str", default=u"unix:/var/lib/lxd/unix.socket"),
            key_file=dict(
                type=u"str",
                default=u"{}/.config/lxc/client.key".format(os.environ["HOME"]),
            ),
            cert_file=dict(
                type=u"str",
                default=u"{}/.config/lxc/client.crt".format(os.environ["HOME"]),
            ),
            trust_password=dict(type=u"str", no_log=True),
        ),
        supports_check_mode=True,
    )

    try:
        client = LXDClient(
            module.params[u"url"],
            key_file=module.params[u"key_file"],
            cert_file=module.params[u"cert_file"],
            debug=module._verbosity >= 4,
        )
        if module.params["trust_password"]:
            client.authenticate(module.params["trust_password"])
    except LXDClientException as e:
        self.module.fail_json(changed=False, msg=e.msg)

    if module.params[u"state"] == u"present":
        try:
            new_pool = client.do(
                "POST",
                u"/1.0/storage-pools",
                body_json=dict(
                    name=module.params["name"],
                    driver=module.params["driver"],
                    config=module.params["config"],
                ),
            )
            module.exit_json(changed=True)

        except LXDClientException as e:
            if e.msg == u"The storage pool already exists":
                module.exit_json(changed=False)
            else:
                module.fail_json(changed=False, msg=e.msg)

    elif module.params[u"state"] == u"absent":
        try:
            client.do("DELETE", u"/1.0/storage-pools/{0}".format(module.params["name"]))
            module.exit_json(changed=True)
        except LXDClientException as e:
            if e.msg == u"No such object":
                module.exit_json(changed=False)
            else:
                module.fail_json(changed=False, msg=e.msg)
    else:
        raise ValueError(u"Unexpected state name")


if __name__ == "__main__":
    main()
