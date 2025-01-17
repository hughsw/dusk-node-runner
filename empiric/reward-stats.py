#!/usr/bin/env python3

import sys
import math
import json
import requests

class attrdict(dict):
    # attrdict = type('attrdict', (dict,), {'__getattr__': lambda self, key: self[key]})
    def __getattr__(self, key):
        return self[key]

my_stake_dusk = float(sys.argv[1])

# Hoping that GraphQL will let us query for all these constants and endpoints...

# see:
#   https://docs.dusk.network/developer/integrations/rues/
#   https://github.com/dusk-network/rusk/wiki/RUES-(Rusk-Universal-Event-System)
#   https://graphql.org/learn/queries/

# rusk/w3sper.js/src/network/components/node.js
# rusk/w3sper.js/src/network/components/blocks.js

"""
 curl -i -sSL -X POST 'http://localhost:8080/on/node/provisioners'
 curl -i -sSL -X POST 'http://localhost:8080/on/node/info'

 curl -i -sSL -X POST 'http://localhost:8080/on/blocks/gas-price'
 curl -i -sSL -X POST 'http://localhost:8080/on/network/peers_location'
 curl -i -sSL -X POST --data 500 http://localhost:8080/on/network/peers
 curl -i -sSL -X POST --data 500 https://nodes.dusk.network/on/network/peers
 curl -i -sSL -X POST https://nodes.dusk.network/on/node/crs  # careful, big response
 curl -i -sSL -X POST https://nodes.dusk.network/on/blocks/gas-price

 curl -i -sSL -H 'Content-Type: application/json' -X POST -d '' https://nodes.dusk.network/on/graphql/query
 curl -i -sSL -X POST --data-raw 'query { block(height: -1) { header { height hash } reward fees gasSpent } }' https://nodes.dusk.network/on/graphql/query
 curl -i -sSL -X POST --data-raw 'query { block(height: -1) { header { height json } reward fees gasSpent transactions {tx{json} id gasSpent raw } } }' https://nodes.dusk.network/on/graphql/query

 curl -i -sSL -H 'Content-Type: application/json' -X POST --data-raw \
    'query { transactions(last: 5) {id } }' \
    https://nodes.dusk.network/on/graphql/query

 curl -i -sSL -H 'Content-Type: application/json' -X POST --data-raw \
    'query { tx(hash:"4e7fc5e764edb911325ea60c12586b7e572d0f9a6889e1f412b898010dfdf21e") { gasSpent tx{json}}}' \
    http://localhost:8080/on/graphql/query
    https://nodes.dusk.network/on/graphql/query

 jq 'fromjson | .'

 curl -i -sSL -H 'Content-Type: application/json' -X POST --data-raw \
    'query { transaction(id:4e7fc5e764edb911325ea60c12586b7e572d0f9a6889e1f412b898010dfdf21e) {txType memo } }' \
    https://nodes.dusk.network/on/graphql/query


 curl -sSL -H 'Content-Type: application/json' -X POST --data-raw \
    'query { fullMoonlightHistory(address:"21mif6HvgdLoJtLzibs42LZDtnwkf3518yfhBsTfVim2WZa3j8H9E64JHK4KWdc7W5KMDvoMk7zdY9ddeE1VuNQsks1suJzWDNf5mL5yBqjzdkdfWPaJjyg4rvJ1GqREuDBq", ord:"asce") { json } }' \
    https://nodes.dusk.network/on/graphql/query \
    | jq .fullMoonlightHistory.json

 curl -sSL -H 'Content-Type: application/json' -X POST --data-raw \
    'query { fullMoonlightHistory(address:"t3hhgUWKSMJFrTHA9kHgCX7PkovZy5XS8LEFMm5wrSaADjD5kv6VWYsuEmYMhfwvdoxbL5cgfka6pPyNwKrWo33erV1zt1yb1ysJu6roX9JCFHSQ9mVButSAvvpCSSPfcE9", ord:"asc") { json } }' \
    https://nodes.dusk.network/on/graphql/query \
    | jq .fullMoonlightHistory.json

 curl -sSL -H 'Content-Type: application/json' -X POST --data-raw \
     'query { contractEvents(height: -1) { json } }' \
    https://nodes.dusk.network/on/graphql/query \
    | jq .

        "source": "0200000000000000000000000000000000000000000000000000000000000000",

 curl -sSL -H 'Content-Type: application/json' -X POST --data-raw \
     'query { finalizedEvents(contractId: "0200000000000000000000000000000000000000000000000000000000000000") { json } }' \
     *** HUGE ***
    https://nodes.dusk.network/on/graphql/query \
    | jq .



"""

url = 'https://nodes.dusk.network/on/node/provisioners'
dusk_point = 9  # log10 of LUX-per-DUSK
node_normal_dusk = 1_000

def native_to_dusk(native, to_dusk_factor=1/math.pow(10, dusk_point)):
    return native * to_dusk_factor

block_reward_dusk_total = 19.8574
# estimate based on limited understanding of the Incentive Structure in https://docs.dusk.network/learn/tokenomics/
block_reward_dusk = 0.8 * block_reward_dusk_total
block_reward_interval_sec = 10

print(f'{16/block_reward_dusk}')

SEC_PER_MIN = 60
MIN_PER_HOUR = 60
HOUR_PER_DAY = 24
DAY_PER_WEEK = 7
DAY_PER_YEAR = 365.2425
MONTH_PER_YEAR = 12
DAY_PER_MONTH = DAY_PER_YEAR / MONTH_PER_YEAR

block_per_day = (SEC_PER_MIN * MIN_PER_HOUR * HOUR_PER_DAY) / block_reward_interval_sec
print(f'block_per_day: {block_per_day:.5}')

block_reward_dusk_per_sec = block_reward_dusk * (1 / block_reward_interval_sec)

reward_per_day_dusk = block_reward_dusk_per_sec * SEC_PER_MIN * MIN_PER_HOUR * HOUR_PER_DAY
reward_per_week_dusk = reward_per_day_dusk * DAY_PER_WEEK
reward_per_month_dusk = reward_per_day_dusk * DAY_PER_MONTH
reward_per_year = reward_per_day_dusk * DAY_PER_YEAR
print(f"""block_reward_dusk_per_sec: {block_reward_dusk_per_sec:.6},
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
stake_sum_native = sum(provisioner.amount for provisioner in provisioners)
stake_sum_dusk = native_to_dusk(stake_sum_native)
minimal_provisioner_fraction = node_normal_dusk / stake_sum_dusk
print(f'minimal_provisioner_fraction: {minimal_provisioner_fraction}')
minimal_provisioner_once_per = 1 / minimal_provisioner_fraction
print(f'minimal_provisioner_once_per: {minimal_provisioner_once_per:.7}')
print(f'minimal_provisioner_day_per_block: {1/(block_per_day*minimal_provisioner_fraction)}')
my_fraction = my_stake_dusk / stake_sum_dusk
print(f'num_provisioners: {num_provisioners}, stake_sum_native: {stake_sum_native:_}, , stake_sum_dusk: {stake_sum_dusk:_}, my_stake_dusk: {my_stake_dusk:_}, my_fraction: {my_fraction} {my_fraction*100:.6}%')

my_block_per_day = block_per_day * my_fraction
my_minute_per_block = MIN_PER_HOUR * HOUR_PER_DAY / my_block_per_day
print(f'my_block_per_day: {my_block_per_day:.4}, my_minute_per_block: {my_minute_per_block:.4}')

reward_per_day_multiplier = stake_sum_dusk / reward_per_day_dusk
print(f'reward_per_day_multiplier: {reward_per_day_multiplier}')

# need to include growing stake_sum_dusk
# annual fraction
daily_growth_fraction = reward_per_day_dusk / stake_sum_dusk
print(f'daily_growth_fraction: {daily_growth_fraction*100:.6}%')
annual_fraction = daily_growth_fraction * DAY_PER_YEAR
apr = annual_fraction * 100
print(f'annual_fraction: {annual_fraction}, apr: {apr:.6}%')


my_reward_per_day_dusk = my_fraction * reward_per_day_dusk
#my_reward_per_day_dusk = my_stake_dusk / stake_sum_dusk * reward_per_day_dusk
my_reward_per_year = my_reward_per_day_dusk * DAY_PER_YEAR
my_apr = my_reward_per_year / my_stake_dusk * 100
print(f'my_reward_per_day_dusk: {my_reward_per_day_dusk}, my_reward_per_year: {my_reward_per_year:_}, my_apr: {my_apr:.3}%')

print()

print(f'growth:')
global_stake_dusk = stake_sum_dusk
growth_factor_prev = 1
week_index = 0
month_index = 0
years = 4
for day_index in range(int(years * DAY_PER_YEAR) + 11):
    growth_factor = global_stake_dusk / stake_sum_dusk
    daily_growth_factor = growth_factor / growth_factor_prev

    if day_index % DAY_PER_WEEK == 0 or day_index == 1:
        print(f'  day: {day_index}, week: {week_index}, growth_factor: {growth_factor:.7}, daily_growth_factor: {daily_growth_factor:.7}')
        week_index += 1

    if day_index >= month_index * DAY_PER_MONTH:
        print(f'  day: {day_index}, month: {month_index}, growth_factor: {growth_factor:.7}, daily_growth_factor: {daily_growth_factor:.7}')
        print()
        if month_index % MONTH_PER_YEAR == 0:
            print()
        month_index += 1

    global_stake_dusk += reward_per_day_dusk
    growth_factor_prev = growth_factor

print()
print()

# blocks per four-year period
block_per_four_year = 12_614_400
dusk_per_four_year = 250_480_000
dusk_per_block = dusk_per_four_year / block_per_four_year
print(f'dusk_per_block: {dusk_per_block:.6}, or {block_per_four_year * 19.8574:_}')
seconds = block_per_four_year * block_reward_interval_sec
days = seconds * 1 / (SEC_PER_MIN * MIN_PER_HOUR * HOUR_PER_DAY)
print(f'block_per_four_year: {block_per_four_year:_}, seconds: {seconds:_}, days: {days:_}')

for provisioner in provisioners:
    print(provisioner)
