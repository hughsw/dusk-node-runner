#!/usr/bin/env python3

import sys
import math
import json
import requests

class attrdict(dict):
    # attrdict = type('attrdict', (dict,), {'__getattr__': lambda self, key: self[key]})
    def __getattr__(self, key):
        return self[key]

url = 'https://nodes.dusk.network/on/node/provisioners'
dusk_point = 9  # log10 of LUX-per-DUSK
minimum_stake_dusk = 1_000

def lux_to_dusk(lux, to_dusk_factor=1/math.pow(10, dusk_point)):
    return lux * to_dusk_factor

block_reward_total_dusk = 19.8574
# estimate based on limited understanding of the Incentive Structure in https://docs.dusk.network/learn/tokenomics/
block_reward_effective_dusk = 0.8 * block_reward_total_dusk
block_reward_interval_sec = 10

print(f'block_reward_total_dusk: {block_reward_total_dusk}, block_reward_effective_dusk: {block_reward_effective_dusk:.6}')

SEC_PER_MIN = 60
MIN_PER_HOUR = 60
HOUR_PER_DAY = 24
DAY_PER_WEEK = 7
DAY_PER_YEAR = 365.2425
MONTH_PER_YEAR = 12
DAY_PER_MONTH = DAY_PER_YEAR / MONTH_PER_YEAR

block_per_day = (SEC_PER_MIN * MIN_PER_HOUR * HOUR_PER_DAY) / block_reward_interval_sec
print(f'block_per_day: {block_per_day:.5}')

block_reward_effective_dusk_per_sec = block_reward_effective_dusk * (1 / block_reward_interval_sec)

reward_per_day_dusk = block_reward_effective_dusk_per_sec * SEC_PER_MIN * MIN_PER_HOUR * HOUR_PER_DAY
reward_per_week_dusk = reward_per_day_dusk * DAY_PER_WEEK
reward_per_month_dusk = reward_per_day_dusk * DAY_PER_MONTH
reward_per_year = reward_per_day_dusk * DAY_PER_YEAR
print(f"""block_reward_effective_dusk_per_sec: {block_reward_effective_dusk_per_sec:.6},
reward_per_day_dusk: {reward_per_day_dusk:_}  {0.7*reward_per_day_dusk:_}  {0.8*reward_per_day_dusk:_},
reward_per_week_dusk: {reward_per_week_dusk:_},
reward_per_month_dusk: {reward_per_month_dusk:_},
reward_per_year: {reward_per_year:_},""")

r = requests.post(url)
#print(f'r.text: {r.text}')

provisioners = r.json()
#print(f'provisioners: {provisioners}')
provisioners = tuple(map(attrdict, provisioners))
print(f'provisioners[0]: {provisioners[0]}')
print(f'provisioners[0]: {json.dumps(provisioners[0])}')

num_provisioners = len(provisioners)
stake_sum_lux = sum(provisioner.amount for provisioner in provisioners)
stake_sum_dusk = lux_to_dusk(stake_sum_lux)
minimum_stake_fraction = minimum_stake_dusk / stake_sum_dusk
print(f'minimum_stake_fraction: {minimum_stake_fraction:.3}  {100*minimum_stake_fraction:.3}%')
minimal_provisioner_once_per = 1 / minimum_stake_fraction
print(f'minimal_provisioner_once_per: {minimal_provisioner_once_per:.7}')
print(f'minimal_provisioner_day_per_block: {1/(block_per_day*minimum_stake_fraction)}')
print(f'num_provisioners: {num_provisioners}, stake_sum_lux: {stake_sum_lux:_}, , stake_sum_dusk: {stake_sum_dusk:_}')

if False:
    print()
    for provisioner in provisioners:
        print(provisioner)

total_lux = sum(provisioner.amount for provisioner in provisioners)
amount_max_lux = max(provisioner.amount for provisioner in provisioners)
amount_min_pos_lux = min(provisioner.amount for provisioner in provisioners if provisioner.amount > 0)
reward_total_lux = sum(provisioner.reward for provisioner in provisioners)
range = amount_max_lux * (1/amount_min_pos_lux)
print(f'total_lux: {total_lux:_}, reward_total_lux: {reward_total_lux:_}, amount_max_lux: {amount_max_lux:_}, amount_min_pos_lux: {amount_min_pos_lux:_}, range: {range:.5}')
print(f'range: {range:.5}, sqrt: {math.sqrt(range):.5}, qbrt: {math.pow(range,1/3):.5}')
for provisioner in provisioners:
    provisioner.tag = provisioner.key[:7]
    provisioner.imspecial = provisioner.owner['Account'] != provisioner.key and provisioner.owner['Account'][:7]
    provisioner.fraction = provisioner.amount * (1 / total_lux)
    provisioner.qb = int(math.ceil(math.pow(provisioner.amount * (1 / amount_min_pos_lux), 1/3)))

provisioners_sorted = sorted(provisioners, key=lambda p: p.amount, reverse=True)

for provisioner in provisioners_sorted:
    print(f'  tag: {provisioner.tag}, qb: {provisioner.qb}, percent: {100*provisioner.fraction:.4}%  fraction: {provisioner.fraction}, imspecial: {provisioner.imspecial or ""}')
