#!/usr/bin/env python3
"""A test profile with 30 VM nodes (2 core, 8gb ram each, with a routable IP) to test mass single-node Kubernetes cluster bring up for SLATE.

Each VM will automatically be added to the CHPC Foreman/Puppet infrastructure.

A pool of 30 public (independent of the VMs IP addresses) will be allocated as well for MetalLB load balancing."""

import geni.portal as portal
import geni.rspec.emulab as emulab
import geni.rspec.igext as igext
import geni.rspec.pg as pg

SITES_COUNT_DICT = {
    "Site 0": {
        "site_name": "utah.cloudlab.us",
        "node_type": "xl170",
        "node_count": 15,
    },
    "Site 1": {
        "site_name": "clemson.cloudlab.us",
        "node_count": 15,
    },
}

DISK_IMAGE = "urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD"

request = portal.context.makeRequestRSpec()
node_count = 0

for k, v in SITES_COUNT_DICT.items():
    for i in range(v["node_count"]):
        node = request.XenVM("node-" + str(node_count))
        node.cores = 2
        node.ram = 8 * 1024
        node.routable_control_ip = True
        node.exclusive = True
        node.disk_image = DISK_IMAGE
        node.addService(
            pg.Execute(
                "/bin/sh",
                "/bin/curl -sSL https://raw.githubusercontent.com/slateci/slate-puppet/master/scripts/bootstrap_puppet.sh | sudo /bin/bash",
            )
        )

        if "site_name" in v:
            node.component_manager_id = (
                "urn:publicid:IDN+" + v["site_name"] + "+authority+cm"
            )

            if "node_type" in v:
                node.xen_ptype = v["node_type"] + "-vm"

        else:
            node.Site(k)

        node_count += 1

    if "site_name" in v:
        addr_pool = igext.AddressPool("metallb_ips_" + v["site_name"], v["node_count"])
        addr_pool.component_manager_id = (
            "urn:publicid:IDN+" + v["site_name"] + "+authority+cm"
        )
        request.addResource(addr_pool)

    else:
        addr_pool = igext.AddressPool(
            "metallb_ips_" + k.replace(" ", "_"), v["node_count"]
        )
        addr_pool.Site(k)
        request.addResource(addr_pool)


portal.context.printRequestRSpec()
