# cloudlab-kubespray-inventory
Generates a kubespray inventory file for experiments based off of the [30-cluster-bring-up](https://www.cloudlab.us/show-profile.php?uuid=bfb6a8ec-0361-11eb-b7c5-e4434b2381fc) CloudLab profile.

## Use
`./generate-kubespray-inventory.py SLATE <EXPERIMENT-NAME>`

See `./generate-kubespray-inventory.py -h` for information.

## Files
- `30-node-cluster.py`: generates the `30-cluster-bring-up` profile using `geni-lib`.
- `rpc.py`: library to communicate with CloudLab
