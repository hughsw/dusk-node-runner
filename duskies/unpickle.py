#!/usr/bin/env python3

import os
import pickle
import json

top = '/home/hugh/bc/dusk-node-runner/duskies/duskies-api-data/provisioning-records'
epoch = 'epoch-0160'
filename = 'dusk-provisioning_block-0346542_epoch-0160_epochblock-0942_2025-02-16-1457-37.pkl'

filename_abs = os.path.join(top, epoch, filename)

# Load dictionary from a file'dusk-provisioning_block-0346542_epoch-0160_epochblock-0942_2025-02-16-1457-37.pkl'
with open(filename_abs, 'rb') as file:
#with open('/home/hugh/bc/dusk-node-runner/duskies/duskies-api-data/provisioning-records/dusk-provisioning_block-0324545_epoch-0150_epochblock-0545_2025-02-14-0148-50.pkl', 'rb') as file:
#with open('/home/hugh/bc/dusk-node-runner/duskies/duskies-api-data/provisioning-records/dusk-provisioning_block-0324545_epoch-0150_epochblock-0545_2025-02-14-0148-50.pkl', 'rb') as file:
    loaded_dict = pickle.load(file)

print(json.dumps(loaded_dict))
