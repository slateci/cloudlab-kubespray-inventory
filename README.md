# cloudlab-kubespray-inventory
Generates a kubespray inventory file for experiments based off of the [30-cluster-bring-up](https://www.cloudlab.us/show-profile.php?uuid=bfb6a8ec-0361-11eb-b7c5-e4434b2381fc) CloudLab profile.

Creates 30 different inventory files to create single-node Kubernetes clusters. 
Each cluster is assigned a public IP for MetalLB.
These inventory files can then be used with [slate-ansible](https://github.com/slateci/slate-ansible) to register each cluster with SLATE.

## Use
`./generate-kubespray-inventory.py SLATE <EXPERIMENT-NAME>`

See `./generate-kubespray-inventory.py -h` for information.

## Example
```
❯ ./generate_kubespray_inventory.py SLATE emerso0-QV81656 --username emerso0 --key-path ./cloudlab.pem --slate-group-name 'foreman-test' --slate-org-name 'University of Utah'

❯ cat inventory/cluster0/hosts.yaml
all:
  children:
    calico-rr:
      hosts: {}
    etcd:
      hosts:
        node1:
    k8s-cluster:
      children:
        kube-master:
        kube-node:
      vars:
        kube_proxy_strict_arp: true
        metallb_enabled: true
        metallb_ip_range:
        - 128.110.155.128/32
        metallb_version: v0.9.3
        slate_cluster_name: cluster0
        slate_group_name: foreman-test
        slate_org_name: University of Utah
    kube-master:
      hosts:
        node1:
    kube-node:
      hosts:
        node1:
  hosts:
    node1:
      access_ip: 128.110.155.143
      ansible_host: 128.110.155.143
      ip: 128.110.155.143
```

Which can then be used with kubespray like so:
`cd ../kubespray && ansible-playbook -i ../cloudlab-kubespray-inventory/inventory/cluster0/hosts.yaml --become --become-user=root -u emerso0 cluster.yml`

Then registered with SLATE like so:
`cd ../slate-ansible && ansible-playbook -i ../cloudlab-kubespray-inventory/inventory/cluster0/hosts.yaml -u emerso0 -e 'slate_cli_token=TOKEN' -e 'slate_cli_endpoint=https://api.slateci.io:443' --become --become-user=root site.yml`

## Files
- `30-node-cluster.py`: generates the `30-cluster-bring-up` profile using `geni-lib`.
- `rpc.py`: library to communicate with CloudLab
