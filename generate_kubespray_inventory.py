#!/usr/bin/env python3

import argparse
import json
import os
from getpass import getpass
from xml.dom import minidom

import yaml

import rpc

parser = argparse.ArgumentParser(
    description="Generate a kubespray inventory from a Cloudlab experiment."
)
parser.add_argument(
    "project_name",
    type=str,
    help="name of the project experiment_name is in",
)
parser.add_argument(
    "experiment_name",
    type=str,
    help="name of experiment to generate an inventory from",
)

parser.add_argument(
    "--username",
    type=str,
    default=None,
    help="username used to login to Cloudlab",
)
parser.add_argument(
    "--key-path",
    type=str,
    default=None,
    help="path to cloudlab.pem",
)
parser.add_argument(
    "--slate-group-name",
    type=str,
    default=None,
    help="group name to register this cluster under for SLATE, must also specify slate-org-name",
)
parser.add_argument(
    "--slate-org-name",
    type=str,
    default=None,
    help="org name to register this cluster under for SLATE, must also specify slate-group-name",
)
parser.add_argument(
    "--cluster-name-prefix",
    type=str,
    default="cluster",
    help="string to prefix cluster names, e.g. 'cluster' creates cluster names 'cluster0', 'cluster1', etc. defaults to 'cluster'",
)


def configure_rpc(username, key_path):
    if username is None:
        username = input("CloudLab Username: ")

    password = getpass("CloudLab Password: ")

    if key_path is None:
        key_path = input("Path to cloudlab.pem: ")

    rpc.LOGIN_ID = username
    rpc.PEM_PWORD = password
    rpc.CERT_PATH = key_path


def make_inventory_file(
    cluster_name, metallb_ips, host_ip, slate_group_name=None, slate_org_name=None
):
    host_yaml = {
        "all": {
            "hosts": {
                "node1": {"ansible_host": host_ip, "ip": host_ip, "access_ip": host_ip}
            },
            "children": {
                "kube-master": {"hosts": {"node1": None}},
                "kube-node": {"hosts": {"node1": None}},
                "etcd": {"hosts": {"node1": None}},
                "k8s-cluster": {
                    "children": {"kube-master": None, "kube-node": None},
                    "vars": {
                        "metallb_enabled": True,
                        "metallb_ip_range": ["{}/32".format(x) for x in metallb_ips],
                        "metallb_version": "v0.9.3",
                        "kube_proxy_strict_arp": True,
                    },
                },
                "calico-rr": {"hosts": {}},
            },
        }
    }

    if slate_group_name and slate_org_name:
        host_yaml["all"]["children"]["k8s-cluster"]["vars"].update(
            {
                "slate_group_name": slate_group_name,
                "slate_org_name": slate_org_name,
                "slate_cluster_name": cluster_name,
            }
        )

    filename = "inventory/{}/hosts.yaml".format(cluster_name)
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as f:
        yaml_output = yaml.dump(host_yaml)
        yaml_output = yaml_output.replace("null", "")
        f.write(yaml_output)


def main(args):
    configure_rpc(
        args.username if args.username else None,
        args.key_path if args.key_path else None,
    )

    project_name = args.project_name
    experiment_name = args.experiment_name
    cluster_name_prefix = args.cluster_name_prefix
    slate_group_name = args.slate_group_name if args.slate_group_name else None
    slate_org_name = args.slate_org_name if args.slate_org_name else None

    rval, response = rpc.get_experiment_manifests(project_name, experiment_name)

    if response["code"] != rpc.RESPONSE_SUCCESS:
        print("Failed to get manifest: \n", response["output"])
        return

    cluster_count = 0

    manifest_xmls = json.loads(response["output"])
    for k, v in manifest_xmls.items():
        manifest = minidom.parseString(v)
        ips = [
            item.attributes["address"].value
            for item in manifest.getElementsByTagName("emulab:ipv4")
        ]
        hosts = [
            (item.attributes["name"].value, item.attributes["ipv4"].value)
            for item in manifest.getElementsByTagName("host")
        ]

        num_pub_ips_per_host = len(ips) // len(hosts)
        if num_pub_ips_per_host == 0:
            raise RuntimeError(
                "Got {} public IPs in pool {}, need at least {} public IPs.".format(
                    len(ips), k, len(hosts)
                )
            )

        ip_list_start = 0
        for ip in hosts:
            make_inventory_file(
                "{}{}".format(cluster_name_prefix, cluster_count),
                ips[ip_list_start : (ip_list_start + num_pub_ips_per_host)],
                ip[1],
                slate_group_name=slate_group_name,
                slate_org_name=slate_org_name,
            )
            ip_list_start += num_pub_ips_per_host
            cluster_count += 1


if __name__ == "__main__":
    main(parser.parse_args())
