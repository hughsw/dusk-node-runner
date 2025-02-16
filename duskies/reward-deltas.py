#!/usr/bin/env python3

import sys, os
import json
import collections

debug = True
debug = False

class attrdict(dict):
    # Access dict fields with dot notation.
    # Good enough for JSON work, but doesn't play well with introspective tools, e.g. pydantic.
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value): self[key] = value
    def __delattr__(self, key): del self[key]

    @staticmethod
    def deep(obj):
        def obj_recurse(obj):
            if isinstance(obj, tuple): return tuple(obj_recurse(item) for item in obj)
            if isinstance(obj, list): return list(obj_recurse(item) for item in obj)
            if isinstance(obj, dict): return attrdict((key, obj_recurse(value)) for key, value in obj.items())
            return obj
        return obj_recurse(obj)


dir = sys.argv[1]


class DeltaDude(object):
    bin_per_lux = 1/100_000_000
    dusk_per_bin = 1/10
    generator_lux = 13900180000
    def __init__(self):
        self.previous = None
        self.histogram = collections.Counter()

    def do_data(self, summary):
        #print(json.dumps(summary))

        try:
            summary = summary.dusk_provisioning_summary
            #dusk_provisioners_reward_dusk = data.dusk_provisioning_summary.dusk_provisioners_reward_dusk
        except KeyError:
            pass
            #dusk_provisioners_reward_dusk = data.dusk_provisioners_reward_dusk

        dusk_chain_block_index = summary.dusk_chain_block_index
        debug and print(f'dusk_chain_block_index: {dusk_chain_block_index}')
        dusk_provisioners_reward_dusk = summary.dusk_provisioners_reward_dusk
        debug and print(f'dusk_provisioners_reward_dusk: {dusk_provisioners_reward_dusk}')
        dusk_provisioners_reward_lux = int(dusk_provisioners_reward_dusk * 1_000_000_000)
        debug and print(f'dusk_provisioners_reward_lux: {dusk_provisioners_reward_lux}')

        # only work on adjacent blocks
        if self.previous is not None and self.previous.dusk_chain_block_index + 1 == dusk_chain_block_index:
            dusk_provisioners_reward_delta_lux = dusk_provisioners_reward_lux - self.previous.dusk_provisioners_reward_lux
            debug and print(f'dusk_provisioners_reward_delta_lux: {dusk_provisioners_reward_delta_lux}')

            discretionary_lux = dusk_provisioners_reward_delta_lux - self.generator_lux
            if True or discretionary_lux > 0:
                # binning
                discretionary_bin = int(discretionary_lux * self.bin_per_lux)
                #discretionary_bin = int(dusk_provisioners_reward_delta_lux * self.bin_per_lux)
                self.histogram[discretionary_bin] += 1

        self.previous = attrdict(
            dusk_chain_block_index = dusk_chain_block_index,
            dusk_provisioners_reward_lux = dusk_provisioners_reward_lux,
            )


for dirpath, dirnames, filenames in os.walk(dir, topdown=True, onerror=None, followlinks=False):
    debug and print(f'dirpath: {dirpath}, len(dirnames): {len(dirnames)}, len(filenames): {len(filenames)}')

    dude = DeltaDude()

    filenames.sort()
    for filename_index, filename in enumerate(filenames):
        debug and print(f'filename: {filename}')
        if not filename.endswith('.json'): continue

        with open(os.path.join(dirpath, filename), 'rt') as data_file:

            data = attrdict.deep(json.load(data_file))

        dude.do_data(data)

        if debug and filename_index > 100: break

    print(f'raw histogram')
    delkey = set()
    for key, value in sorted(dude.histogram.items()):
        print(f'{key}  {value}')
        if key <= 0:
            delkey.add(key)
    for key in delkey:
        del dude.histogram[key]

    #print(f'dude.histogram:')
    mass = DeltaDude.dusk_per_bin * sum(key*value for key, value in dude.histogram.items())
    count = sum(dude.histogram.values())
    count_recip = 1 / count
    average = round(mass * count_recip, 2)

    print()
    print(f'Distribution of Discretionary Dusk Rewards')
    print(f' Average: {average} per block, {count:_} blocks')
    print(f' Dusk  Blocks   Percent')

    def print_key_value(key, value):
        dusk = round(key*DeltaDude.dusk_per_bin, 1)
        pct = f'{value*count_recip*100:5.2f}' if value > 0 else '    0'
        print(f'  {dusk}   {value:5}    {pct}%')

    prev_key = None
    for key, value in sorted(dude.histogram.items()):
        if prev_key is not None:
            while prev_key + 1 < key:
                prev_key += 1
                print_key_value(prev_key, 0)
        prev_key = key
        print_key_value(key, value)
