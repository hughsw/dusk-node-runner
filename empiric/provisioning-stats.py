#!/usr/bin/env python3

from datetime import datetime, timezone
from collections import namedtuple
import json
import requests
from itertools import count


provisioners_uri = 'https://nodes.dusk.network/on/node/provisioners'
node_info_uri =  'https://nodes.dusk.network/on/node/info'
block_height_uri = 'https://nodes.dusk.network/on/graphql/query'
block_height_query = b'query { block(height: -1) { header { height } } }'


class attrdict(dict):
    # Access dict entries with dot notation.
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

class Provisioners(namedtuple('Provisioners', (
        'timestamp_sec',
        'timestamp_hr',

        'chain_name',
        'chain_id',
        'chain_block_index',
        'chain_epoch_index',
        'chain_epoch_fraction',
        'chain_epoch_next_minute',

        'provisioner_active_count',
        'provisioner_pending_count',
        'provisioner_inactive_count',
        'provisioner_total_count',
        'provisioner_same_owner_count',
        'provisioner_different_owner_count',

        'total_active_stake_dusk',
        'total_pending_stake_dusk',

        'total_stake_dusk',
        'total_reward_dusk',
        'total_locked_dusk',

        #'total_inactive_dusk',
        'total_provisioner_dusk', 

        #'total_pending_stake_reward_fraction',
        'total_reward_fraction',
        'total_locked_fraction',
        'total_ad_hoc_effective_reward_fraction',

        #'total_non_stake_fraction',
        'non_stake_boost_rate',
        'non_stake_boost_rate_hr',

        'ad_hoc_guidances',

        'provisioners',
        ))):
    __slots__ = ()

    def to_json(self):
        return json.dumps(self._asdict())

class Provisioner(namedtuple('Provisioner', 'timestamp_sec, amount, eligibility, locked_amt, reward')):
    __slots__ = ()
    @staticmethod
    def from_provisioners(provisioners, provisioners_datetime, chain_block_index):
        #now = datetime.now(timezone.utc).replace(microsecond=0)
        timestamp_hr = provisioners_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')
        timestamp_sec = int(provisioners_datetime.timestamp())
        print(f'timestamp_sec: {timestamp_sec}')
        print(f'timestamp_hr: {timestamp_hr}')
        genesis_datetime = datetime(2025, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
        print(f'genesis_datetime: {genesis_datetime}')
        mainnet_time_delta = provisioners_datetime - genesis_datetime
        print(f'mainnet_time_delta: {mainnet_time_delta}')

        chain_epoch_index = chain_block_index // block_per_epoch
        chain_epoch_fraction = round((chain_block_index % block_per_epoch) / block_per_epoch, 3)
        chain_epoch_next_minute = int((1 - chain_epoch_fraction) * block_per_epoch * 10 / 60)

        # based on simulations with total stake around 122M dusk
        ad_hoc_minimum_staking_epoch_count = 60
        ad_hoc_maximum_staking_epoch_count = 80
        ad_hoc_restake_effective_reward_threshold = 0.019
        ad_hoc_meh_reward_threshold =  0.04

        provisioners_raw = attrdict.deep(provisioners)
        provisioners = list(attrdict(
            #timestamp_sec = timestamp_sec,
            #timestamp_hr = timestamp_hr,

            provisioner_key_dotted = key_dotted(provisioner.key),
            provisioner_key_full = provisioner.key,
            owner_key_dotted = key_dotted(provisioner.owner.Account),
            owner_key_full = provisioner.owner.Account,

            maturity_block = provisioner.eligibility,
            maturity_epoch = block_to_epoch(provisioner.eligibility),
            staking_epoch_count = max(0, chain_epoch_index - block_to_epoch(provisioner.eligibility)),

            active_stake_dusk = lux_to_dusk(provisioner.amount) if chain_block_index >= provisioner.eligibility else 0,
            pending_stake_dusk = lux_to_dusk(provisioner.amount) if chain_block_index < provisioner.eligibility else 0,
            stake_dusk = lux_to_dusk(provisioner.amount),

            #original_stake_dusk = lux_to_dusk(provisioner.amount - 9 * provisioner.locked_amt),
            #top_up_stake_dusk = lux_to_dusk(9 * provisioner.locked_amt),
            #top_up_dusk = lux_to_dusk(10 * provisioner.locked_amt),
            reward_dusk = lux_to_dusk(provisioner.reward),
            locked_dusk = lux_to_dusk(provisioner.locked_amt),
        ) for provisioner in provisioners_raw)

        total_active_stake_dusk = 0
        total_pending_stake_dusk = 0
        total_stake_dusk = 0
        total_locked_dusk = 0
        total_reward_dusk = 0
        for provisioner in provisioners:
            provisioner.provisioner_dusk = round(provisioner.stake_dusk + provisioner.locked_dusk + provisioner.reward_dusk, 9)
            provisioner.reward_fraction = round(provisioner.reward_dusk * (1 / provisioner.stake_dusk), 6) if provisioner.stake_dusk > 0 else None
            provisioner.locked_fraction = round(provisioner.locked_dusk * (1 / provisioner.stake_dusk), 6) if provisioner.stake_dusk > 0 else None
            #provisioner.non_stake_total_fraction = round((provisioner.reward_dusk + provisioner.locked_dusk) * (1 / provisioner.stake_dusk), 6) if provisioner.stake_dusk > 0 else None
            provisioner.ad_hoc_effective_reward_fraction = round((provisioner.reward_dusk + 10 * provisioner.locked_dusk) * (1 / provisioner.stake_dusk), 6) if provisioner.stake_dusk > 0 else None

            # rules for ad-hoc guidance
            if provisioner.reward_dusk + provisioner.locked_dusk > 0 and provisioner.stake_dusk == 0:
                # strange special case we have observed
                provisioner.ad_hoc_restaking_guidance = 'restake, overdue, oversight?'
            elif provisioner.staking_epoch_count <= ad_hoc_minimum_staking_epoch_count:
                provisioner.ad_hoc_restaking_guidance = 'wait'
            elif provisioner.ad_hoc_effective_reward_fraction is not None and provisioner.ad_hoc_effective_reward_fraction > ad_hoc_restake_effective_reward_threshold:
                if provisioner.ad_hoc_effective_reward_fraction > ad_hoc_meh_reward_threshold:
                    # TODO: base this on backwards calculation of stake larger than existing stake
                    provisioner.ad_hoc_restaking_guidance = 'restake, meh'
                elif provisioner.staking_epoch_count >= ad_hoc_maximum_staking_epoch_count:
                    provisioner.ad_hoc_restaking_guidance = 'restake, overdue'
                else:
                    provisioner.ad_hoc_restaking_guidance = 'restake'
            else:
                # anything outside our simple model of (isolated) provisioner incentivised behavior
                provisioner.ad_hoc_restaking_guidance = 'meh'

            total_active_stake_dusk += provisioner.active_stake_dusk
            total_pending_stake_dusk += provisioner.pending_stake_dusk
            total_stake_dusk += provisioner.stake_dusk
            total_reward_dusk += provisioner.reward_dusk
            total_locked_dusk += provisioner.locked_dusk

        #total_inactive_dusk = total_pending_stake_dusk + total_locked_dusk + total_reward_dusk
        #total_provisioner_dusk = total_active_stake_dusk + total_inactive_dusk
        total_provisioner_dusk = total_stake_dusk + total_reward_dusk + total_locked_dusk

        provisioner_active_count = sum(provisioner.active_stake_dusk > 0 for provisioner in provisioners)
        provisioner_pending_count = sum(provisioner.pending_stake_dusk > 0 for provisioner in provisioners)
        provisioner_inactive_count = sum(provisioner.active_stake_dusk == provisioner.pending_stake_dusk == 0 for provisioner in provisioners)
        provisioner_total_count = provisioner_active_count + provisioner_pending_count + provisioner_inactive_count
        provisioner_same_owner_count = sum(provisioner.owner_key_full == provisioner.provisioner_key_full for provisioner in provisioners)
        provisioner_different_owner_count = sum(provisioner.owner_key_full != provisioner.provisioner_key_full for provisioner in provisioners)


        total_active_stake_dusk_recip = 1 / total_active_stake_dusk
        #total_pending_stake_reward_fraction = total_pending_stake_dusk * total_active_stake_dusk_recip
        total_reward_fraction = total_reward_dusk * total_active_stake_dusk_recip
        total_locked_fraction = total_locked_dusk * total_active_stake_dusk_recip
        total_ad_hoc_effective_reward_fraction = (total_reward_dusk + 10 * total_locked_dusk) * total_active_stake_dusk_recip
        #total_non_stake_fraction = (total_pending_stake_dusk + total_reward_dusk + total_locked_dusk) * total_active_stake_dusk_recip

        non_stake_boost_rate = total_provisioner_dusk / total_active_stake_dusk - 1
        #non_stake_boost_rate = (total_active_stake_dusk + 85 * 16 * 2160) / total_active_stake_dusk - 1
        non_stake_boost_rate_hr = f'{non_stake_boost_rate * 100:.2f}%'

        guidances = (
            'wait',
            'meh',
            'restake',
            'restake, meh',
            'restake, overdue',
            'restake, overdue, oversight?',
            )

        ad_hoc_guidances = attrdict()
        for guidance in guidances:
            reward_locked = tuple(provisioner.reward_dusk + provisioner.locked_dusk for provisioner in provisioners if provisioner.ad_hoc_restaking_guidance == guidance)
            provisioners_reward_locked_dusk = round(sum(reward_locked), 9)
            provisioners_reward_locked_fraction = round(provisioners_reward_locked_dusk / total_stake_dusk, 6)
            provisioners_reward_locked_fraction_hr = f'{provisioners_reward_locked_fraction*100:.4f}%'
            ad_hoc_guidances[guidance] = attrdict(
                ad_hoc_restaking_guidance = guidance,
                provisioners_count = len(reward_locked),
                provisioners_reward_locked_dusk = provisioners_reward_locked_dusk,
                provisioners_reward_locked_fraction = provisioners_reward_locked_fraction, 
                provisioners_reward_locked_fraction_hr = provisioners_reward_locked_fraction_hr,
                )
        
        for provisioner in provisioners:
            assert provisioner.staking_epoch_count >= 0, str((provisioner.staking_epoch_count, provisioner))
            assert provisioner.active_stake_dusk == 0 or provisioner.pending_stake_dusk == 0, str((provisioner.active_stake_dusk, provisioner.pending_stake_dusk, provisioner.provisioner_key_dotted))
            assert provisioner.active_stake_dusk >= 0, str(( provisioner.active_stake_dusk,))
            assert provisioner.pending_stake_dusk >= 0, str(( provisioner.pending_stake_dusk,))
            #assert provisioner.top_up_stake_dusk >= 0, str(( provisioner.top_up_stake_dusk,))
            #assert provisioner.top_up_dusk >= 0, str(( provisioner.top_up_dusk,))
            assert provisioner.reward_dusk >= 0, str(( provisioner.reward_dusk,))
            assert provisioner.locked_dusk >= 0, str(( provisioner.locked_dusk,))
            assert provisioner.provisioner_dusk >= 0, str((provisioner.provisioner_dusk,))
            assert provisioner.reward_fraction is None or provisioner.reward_fraction >= 0, str((provisioner.reward_fraction,))
            assert provisioner.locked_fraction is None or provisioner.locked_fraction >= 0, str((provisioner.locked_fraction,))
            assert provisioner.ad_hoc_effective_reward_fraction is None or provisioner.ad_hoc_effective_reward_fraction >= 0, str((provisioner.ad_hoc_effective_reward_fraction,))
            #assert provisioner.non_stake_total_fraction is None or provisioner.non_stake_total_fraction >= 0, str((provisioner.non_stake_total_fraction,))

        #provisioners.sort(key=lambda provisioner: (1-provisioner.active_stake_dusk, provisioner.provisioner_key_dotted))
        #provisioners.sort(key=lambda provisioner: (1-provisioner.original_stake_dusk, provisioner.provisioner_key_dotted))
        provisioners.sort(key=lambda provisioner: (1-provisioner.provisioner_dusk, provisioner.provisioner_key_dotted))
        #provisioners.sort(reverse=True, key=lambda provisioner: (provisioner.total_dusk, provisioner.provisioner_key_dotted))

        provisioners = Provisioners(
            timestamp_sec = timestamp_sec,
            timestamp_hr = timestamp_hr,

            chain_name = 'DUSK',
            chain_id = chain_id,
            chain_block_index = chain_block_index,
            chain_epoch_index = chain_epoch_index,
            chain_epoch_fraction = chain_epoch_fraction,
            chain_epoch_next_minute = chain_epoch_next_minute,

            provisioner_active_count = provisioner_active_count,
            provisioner_pending_count = provisioner_pending_count,
            provisioner_inactive_count = provisioner_inactive_count,
            provisioner_total_count = provisioner_total_count,
            provisioner_same_owner_count = provisioner_same_owner_count,
            provisioner_different_owner_count = provisioner_different_owner_count,

            total_active_stake_dusk = round(total_active_stake_dusk, 9),
            total_pending_stake_dusk = round(total_pending_stake_dusk, 9),
            total_stake_dusk = round(total_stake_dusk, 9),
            total_reward_dusk = round(total_reward_dusk, 9),
            total_locked_dusk = round(total_locked_dusk, 9),
            #total_inactive_dusk = round(total_inactive_dusk, 9),
            total_provisioner_dusk = round(total_provisioner_dusk, 9),

            #total_pending_stake_reward_fraction = round(total_pending_stake_reward_fraction, 6),
            total_reward_fraction = round(total_reward_fraction, 6),
            total_locked_fraction = round(total_locked_fraction, 6),
            total_ad_hoc_effective_reward_fraction = round(total_ad_hoc_effective_reward_fraction, 6),

            #total_non_stake_fraction = round(total_non_stake_fraction, 6),
            non_stake_boost_rate = round(non_stake_boost_rate, 6),
            non_stake_boost_rate_hr = non_stake_boost_rate_hr,

            ad_hoc_guidances = ad_hoc_guidances,

            provisioners = tuple(provisioners),
        )

        return provisioners
    
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

# get dusk_tokenomics
block_per_epoch = 2160
epoch_per_block = 1 / block_per_epoch


lux_factor = 1 / 1_000_000_000
Mdusk_factor = 1 / 1_000_000

def lux_to_dusk(lux, *, _lux_to_dusk_factor=1 / 1_000_000_000):
    return round(lux * _lux_to_dusk_factor, 9)

def key_dotted(key, *, num_chars=5):
    return f'{key[:num_chars]}...{key[-num_chars:]}'

def block_to_epoch(block):
    return int(block * epoch_per_block)


chain_info = attrdict.deep(requests.post(node_info_uri).json())
print(f'chain_info: {chain_info}')
chain_id = chain_info.chain_id
print(f'chain_id: {chain_id}')

block_height = attrdict.deep(requests.post(block_height_uri, data=block_height_query).json()).block.header.height
#block_height = 2159
print(f'block_height: {block_height:_}')
epoch = block_height // block_per_epoch
epoch_fraction = (block_height % block_per_epoch) / block_per_epoch
next_epoch_minutes = int((1 - epoch_fraction) * block_per_epoch * 10 / 60)

result = requests.post(provisioners_uri)

now = datetime.now(timezone.utc).replace(microsecond=0)
now_str = now.strftime('%Y-%m-%d %H:%M:%S %Z')
print(f'now: {now},  now_str: {now_str}')
genesis_datetime = datetime(2025, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
print(f'genesis_datetime: {genesis_datetime}')
mainnet_time_delta = now - genesis_datetime
print(f'mainnet_time_delta: {mainnet_time_delta}')


result_json = result.json()
provisioners = attrdict.deep(result_json)

#print(f'{json.dumps(provisioners[0])}')
print(f'{json.dumps(provisioners)}')

xxx = Provisioner.from_provisioners(result_json, now, block_height)
print('Provisioner.from_provisioners:')
print(f'{xxx.to_json()}')


total_stake_lux = sum(provisioner.amount for provisioner in provisioners)
print(f'total_stake_lux: {total_stake_lux:_}')
total_stake_dusk = total_stake_lux * lux_factor
per_total_stake_dusk = 1 / total_stake_dusk
total_stake_Mdusk = total_stake_dusk * Mdusk_factor
print(f'total_stake_dusk: {total_stake_dusk:_}  {total_stake_Mdusk:.1f}M')

total_stake_rewards_lux = sum(provisioner.reward for provisioner in provisioners)
print(f'total_stake_rewards_lux: {total_stake_rewards_lux:_}')
total_stake_rewards_dusk = total_stake_rewards_lux * lux_factor
total_stake_rewards_Mdusk = total_stake_rewards_dusk * Mdusk_factor
print(f'total_stake_rewards_dusk: {total_stake_rewards_dusk:_}  {total_stake_rewards_Mdusk:.1f}M')

total_rewards_per_stake = total_stake_rewards_dusk * per_total_stake_dusk
print(f'total_rewards_per_stake: {total_rewards_per_stake*100:.2f}%')


num_provisioners = len(provisioners)
print(f'num_provisioners: {num_provisioners}')

# still have block 0 maturity
genesis_provisioners = tuple(provisioner for provisioner in provisioners if provisioner.eligibility == 0)
num_genesis_provisioners = len(genesis_provisioners)
print(f'num_genesis_provisioners: {num_genesis_provisioners}')

genesis_provisioners_no_top_up = tuple(provisioner for provisioner in genesis_provisioners if provisioner.locked_amt == 0)
num_genesis_provisioners_no_top_up = len(genesis_provisioners_no_top_up)
num_genesis_provisioners_top_up = num_genesis_provisioners - num_genesis_provisioners_no_top_up
print(f'num_genesis_provisioners_no_top_up: {num_genesis_provisioners_no_top_up}')
print(f'num_genesis_provisioners_top_up: {num_genesis_provisioners_top_up}')

non_genesis_provisioners = tuple(provisioner for provisioner in provisioners if provisioner.eligibility != 0)
num_non_genesis_provisioners = len(non_genesis_provisioners)
print(f'num_non_genesis_provisioners: {num_non_genesis_provisioners}')


genesis_stake_lux = sum(provisioner.amount for provisioner in genesis_provisioners)
print(f'genesis_stake_lux: {genesis_stake_lux:_}')
genesis_stake_dusk = genesis_stake_lux * lux_factor
genesis_stake_Mdusk = genesis_stake_dusk * Mdusk_factor
print(f'genesis_stake_dusk: {genesis_stake_dusk:_}  {genesis_stake_Mdusk:.1f}M')

genesis_stake_rewards_lux = sum(provisioner.reward for provisioner in genesis_provisioners)
print(f'genesis_stake_rewards_lux: {genesis_stake_rewards_lux:_}')
genesis_stake_rewards_dusk = genesis_stake_rewards_lux * lux_factor
genesis_stake_rewards_Mdusk = genesis_stake_rewards_dusk * Mdusk_factor
print(f'genesis_stake_rewards_dusk: {genesis_stake_rewards_dusk:_}  {genesis_stake_rewards_Mdusk:.1f}M')

genesis_rewards_per_stake = genesis_stake_rewards_dusk / genesis_stake_dusk
print(f'genesis_rewards_per_stake: {genesis_rewards_per_stake*100:.2f}%')

genesis_provisioners_fraction = num_genesis_provisioners / num_provisioners
print(f'genesis_provisioners_percent: {genesis_provisioners_fraction*100:.1f}%')

genesis_stake_fraction = genesis_stake_dusk * per_total_stake_dusk
print(f'genesis_stake_fraction: {genesis_stake_fraction*100:.1f}%')


non_genesis_stake_lux = sum(provisioner.amount for provisioner in non_genesis_provisioners)
print(f'non_genesis_stake_lux: {non_genesis_stake_lux:_}')
non_genesis_stake_dusk = non_genesis_stake_lux * lux_factor
non_genesis_stake_Mdusk = non_genesis_stake_dusk * Mdusk_factor
print(f'non_genesis_stake_dusk: {non_genesis_stake_dusk:_}  {non_genesis_stake_Mdusk:.1f}M')

non_genesis_stake_rewards_lux = sum(provisioner.reward for provisioner in non_genesis_provisioners)
print(f'non_genesis_stake_rewards_lux: {non_genesis_stake_rewards_lux:_}')
non_genesis_stake_rewards_dusk = non_genesis_stake_rewards_lux * lux_factor
non_genesis_stake_rewards_Mdusk = non_genesis_stake_rewards_dusk * Mdusk_factor
print(f'non_genesis_stake_rewards_dusk: {non_genesis_stake_rewards_dusk:_}  {non_genesis_stake_rewards_Mdusk:.1f}M')

non_genesis_rewards_per_stake = non_genesis_stake_rewards_dusk / non_genesis_stake_dusk
print(f'non_genesis_rewards_per_stake: {non_genesis_rewards_per_stake*100:.2f}%')

non_genesis_provisioners_fraction = num_non_genesis_provisioners / num_provisioners
print(f'non_genesis_provisioners_percent: {non_genesis_provisioners_fraction*100:.1f}%')

non_genesis_stake_fraction = non_genesis_stake_dusk * per_total_stake_dusk
print(f'non_genesis_stake_fraction: {non_genesis_stake_fraction*100:.1f}%')


print()
# get these from tokenomics
provisioner_reward_dusk_per_block = 16
epoch_per_year = 4 * 365  

print(f'block_per_epoch: {block_per_epoch:_}')
print(f'epoch_per_year: {epoch_per_year:_}')
print(f'provisioner_reward_dusk_per_block: {provisioner_reward_dusk_per_block}')
provisioner_reward_dusk_per_epoch = provisioner_reward_dusk_per_block * block_per_epoch
print(f'provisioner_reward_dusk_per_epoch: {provisioner_reward_dusk_per_epoch:_}')
provisioner_reward_dusk_per_year = provisioner_reward_dusk_per_epoch * epoch_per_year
print(f'provisioner_reward_dusk_per_year: {provisioner_reward_dusk_per_year:_}')

print()
print(f'now_str: {now_str}')
print(f'total_stake_dusk: {total_stake_dusk:_}')
provisioner_reward_fraction_per_block = provisioner_reward_dusk_per_block * per_total_stake_dusk
print(f'provisioner_reward_fraction_per_block: {provisioner_reward_fraction_per_block}')

provisioner_reward_fraction_per_epoch = provisioner_reward_dusk_per_epoch * per_total_stake_dusk
print(f'provisioner_reward_fraction_per_epoch: {provisioner_reward_fraction_per_epoch}  {provisioner_reward_fraction_per_epoch*100:.6f}%')
provisioner_reward_fraction_per_year = provisioner_reward_dusk_per_year * per_total_stake_dusk
print(f'provisioner_reward_fraction_per_year: {provisioner_reward_fraction_per_year}  {provisioner_reward_fraction_per_year*100:.6f}%')


def best_epoch_N(total_stake, *, verbose=False, growth_model='average', dusk_per_epoch=provisioner_reward_dusk_per_epoch):
    growth_models = ('start', '1/5', 'middle', 'end')
    assert growth_model in growth_models, str((growth_model, growth_models))

    N_max = 0
    compound_rate_max = 0
    #compound_return_max = 0
    compound_return_per_epoch_max = 0
    for N in count(1):

        if growth_model == 'start':
            epoch_rate = dusk_per_epoch / total_stake
        elif growth_model == '1/5':
            epoch_rate = dusk_per_epoch / (total_stake + N * dusk_per_epoch / 5)
        elif growth_model == 'middle':
            epoch_rate = dusk_per_epoch / (total_stake + N * dusk_per_epoch / 2)
        elif growth_model == 'end':
            epoch_rate = dusk_per_epoch / (total_stake + N * dusk_per_epoch)
        else:
            assert False, str(('unhandled growth_model', growth_model, growth_models))

        compound_rate = (N - 1) * epoch_rate
        compound_return = 1 + compound_rate
        # normalize to an effective compounding per-epoch return
        compound_return_per_epoch = pow(compound_return, 1 / N)
        compound_rate_per_epoch = compound_return_per_epoch - 1
        verbose and print(f'N: {N}, compound_rate_per_epoch: {compound_rate_per_epoch:.12f}  {compound_rate_per_epoch*100:.9f}%')
        if compound_return_per_epoch <= compound_return_per_epoch_max:
            compound_rate_per_year = pow(compound_return_per_epoch_max, epoch_per_year) - 1
            return compound_return_per_epoch_max - 1, compound_rate_max, compound_rate_per_year, N_max
            #return compound_return_per_epoch_max, compound_rate_max, compound_return_max, N_max
        N_max = N
        compound_rate_max = compound_rate
        #compound_return_max = compound_return
        compound_return_per_epoch_max = compound_return_per_epoch
        #total_stake *= compound_return

print()
#total_stake_growth_model = 'start'
total_stake_growth_model = '1/5'
#total_stake_growth_model = 'middle'
#total_stake_growth_model = 'end'
best_N = best_epoch_N(total_stake_dusk, growth_model=total_stake_growth_model, verbose=False)
print(f'best_N: {best_N}')

num_years = 1
#num_years = 3.9
total_stake_walk_dusk = total_stake_dusk
n = 0
my_return = 1
while n < num_years * epoch_per_year:
    compound_rate_per_epoch, compound_rate, compound_rate_per_year, N = best_epoch_N(total_stake_walk_dusk, growth_model=total_stake_growth_model)
    print(f'N: {N}, compound_rate_per_epoch: {compound_rate_per_epoch*100:.6f}%, compound_rate_per_N: {compound_rate*100:.2f}%, compound_rate_per_year: {compound_rate_per_year*100:.2f}')
    compound_return = 1 + compound_rate
    my_return *= compound_return
    if n > 0:
    #if True or n > 0:
        total_stake_walk_dusk *= compound_return
    n += N

years = n / epoch_per_year
my_return_per_epoch = pow(my_return, 1 / n)
my_return_per_year = pow(my_return, 1 / years)
print(f'epochs: {n:_}, years: {years:.2f}, my_return: {my_return:.3f}, my_return_per_epoch: {my_return_per_epoch:.8f}, my_return_per_year: {my_return_per_year:.4f}')


#best_N = best_epoch_N(total_stake_dusk)[-1]
#one_year_return = math.pow(

def when_to_compound(my_stake, my_reward):
    # should there be provisioner_reward_epoch_per_fraction
    my_reward_fraction = my_reward * (1 / my_stake)
    my_reward_dusk_per_epoch = my_stake * provisioner_reward_fraction_per_epoch
    my_epochs = my_reward * (1 / my_reward_dusk_per_epoch)

    #print(f'my_stake: {my_stake}, my_reward: {my_reward},  my_epochs: {my_epochs:.2f}')

    total_stake = total_stake_dusk - provisioner_reward_dusk_per_epoch * my_epochs
    compound_rate_per_epoch, compound_rate, compound_rate_per_year, N = best_epoch_N(total_stake, growth_model=total_stake_growth_model)

    print(f'when_to_compound: my_stake: {my_stake}, my_reward: {my_reward}, my_reward_fraction: {my_reward_fraction*100:.2f}%, compound_rate: {compound_rate*100:.3f}%, epochs from now: {int(N-my_epochs)}')

print()
when_to_compound(1010, 14)
when_to_compound(1010, 24)
when_to_compound(1010, 50)
when_to_compound(41, .73)
when_to_compound(411, 7.3)
when_to_compound(4114, 73)
when_to_compound(41140, 730)
when_to_compound(411400, 7300)
when_to_compound(4114000, 73000)
when_to_compound(4114, 53)
when_to_compound(4114, 0)


simulate_epoch = namedtuple('simulate_epoch', (
    'block_index',
    'chain_stake_dusk',
    'my_stake',
    'my_reward',
    'my_locked',
    'my_top_up',
    'my_locked_fraction',
    'my_performance',
    'my_apr',
    'my_apr_hr',
    ))

simulate_epoch = attrdict

def simulate_term(chain_reward_dusk_per_epoch, chain_reward_fraction, chain_stake_dusk, top_up_fraction, *, apr_mode_fraction = 0.0105):
    # state
    my_stake = 1
    my_reward = 0
    #my_stake_top_up = 0
    my_locked = 0
    my_top_up = 0
    my_reward_fraction = 0
    my_locked_fraction = 0

    # state capture
    history = list()
    def history_append():
        history.append(simulate_epoch(
            top_up_fraction = top_up_fraction,
            epoch_index = epoch_index,
            chain_stake_dusk = round(chain_stake_dusk, 9),

            my_stake = round(my_stake, 9),
            my_reward = round(my_reward, 9),
            #my_stake_top_up = round(my_stake_top_up, 9),
            my_locked = round(my_locked, 9),
            my_top_up = round(my_top_up, 9),

            my_reward_fraction = round(my_reward_fraction, 6),
            my_locked_fraction = round(my_locked_fraction, 9),

            #compounding_strategy = compounding_strategy,

            my_performance = round(my_performance, 6),
            my_apr = round(my_apr, 6),

            my_reward_fraction_hr = f'{my_reward_fraction*100:.2f}%',
            my_locked_fraction_hr = f'{my_locked_fraction*100:.4f}%',
            my_combined_fraction_hr = f'{(my_reward_fraction + 10*my_locked_fraction)*100:.2f}%',
            my_apr_hr = f'{my_apr*100:.2f}%'

            ))

    max_apr = 0
    max_index = None
    for epoch_index in count():
        # epoch_index == 0 is maturity epoch

        if epoch_index > 0:
            # decreases because chain_stake_dusk grows
            chain_reward_rate_per_epoch = chain_reward_dusk_per_epoch / chain_stake_dusk

            this_reward = my_stake * chain_reward_rate_per_epoch
            this_top_up = top_up_fraction * this_reward

            my_top_up += this_top_up
            this_stake_top_up = 0.9 * this_top_up
            this_locked = 0.1 * this_top_up

            my_stake += this_stake_top_up
            #my_stake_top_up += this_stake_top_up

            my_locked += this_locked

            my_reward += this_reward - this_top_up


            if True:
                pass
            elif compounding_strategy == 'top-up':
                this_top_up = 1.0 * this_reward
                this_stake_top_up = 0.9 * this_top_up
                my_stake += this_stake_top_up
                my_stake_top_up += this_stake_top_up
                #my_stake += 0.9 * this_top_up
                my_locked += 0.1 * this_top_up
                my_top_up += this_top_up
                my_reward -= this_top_up
            elif compounding_strategy == 'alternate':
                if epoch_index % 2 == 0:
                    # alternating "hack"
                    this_top_up = 1.0 * this_reward
                    this_stake_top_up = 0.9 * this_top_up
                    my_stake += this_stake_top_up
                    my_stake_top_up += this_stake_top_up
                    my_locked += 0.1 * this_top_up
                    my_top_up += this_top_up
                    my_reward -= this_top_up
            elif compounding_strategy == 'reward':
                pass
            else:
                assert False, str(('unhandled compounding_strategy', compounding_strategy, ))

        my_reward_fraction = my_reward / my_stake
        my_locked_fraction = my_locked / my_stake
        my_performance = my_stake + my_reward + my_locked

        # epoch percentage rate
        #my_epr = pow(my_performance, 1 / (epoch_index + 1))
        my_apr = pow(my_performance, epoch_per_year / (epoch_index + 1)) - 1
        assert my_apr > 0 or my_stake == 1, str((my_apr, my_stake, my_reward, my_locked, epoch_index))

        if my_apr > max_apr:
            max_apr = my_apr
            max_index = epoch_index

        history_append()

        # assumes there's only a single mode
        if my_apr < max_apr - apr_mode_fraction: break

        # no infinite loop
        assert epoch_index < 1_000, str((epoch_index, history[-1]))

        # update total stake as per chain_reward_fraction "rationality" factor
        chain_stake_dusk += chain_reward_fraction * chain_reward_dusk_per_epoch


    mode = tuple(item for item in history if item.my_apr >= max_apr - apr_mode_fraction)

    # TODO: abstract this choice
    #peak = mode[0]
    #peak = history[max_index]
    peak = mode[len(mode)//2]
    #peak = mode[-1]

    term_threshold_reward_per_stake = peak.my_reward_fraction
    term_threshold_locked_per_stake = peak.my_locked_fraction
    term_threshold_reward_plus_10_locked_per_stake = peak.my_reward_fraction + 10 * peak.my_locked_fraction

    return attrdict(
        tldr = attrdict(
            top_up_fraction = top_up_fraction,
            term_threshold_epoch_count = peak.epoch_index + 1,
            term_threshold_performance = peak.my_performance,

            term_threshold_reward_per_stake = term_threshold_reward_per_stake,
            term_threshold_locked_per_stake = term_threshold_locked_per_stake,
            term_threshold_reward_plus_10_locked_per_stake = term_threshold_reward_plus_10_locked_per_stake,

            term_threshold_reward_per_stake_hr = f'{term_threshold_reward_per_stake*100:.2f}%',
            term_threshold_locked_per_stake_hr = f'{term_threshold_locked_per_stake*100:.3f}%',
            term_threshold_reward_plus_10_locked_per_stake_hr = f'{term_threshold_reward_plus_10_locked_per_stake*100:.2f}%',

            chain_stake_dusk = peak.chain_stake_dusk,
        ),
        peak = peak,
        mode = mode,
    )

#chain_reward_fraction = 0.65
chain_reward_fraction = 1

top_up_fraction = 0
#top_up_fraction = 0.49999999
#top_up_fraction = 0.5
#top_up_fraction = 1

apr_mode_fraction = 0.0025
#apr_mode_fraction = 0.0055
#apr_mode_fraction = 0.0105
#apr_mode_fraction = 0.0205

run0 = simulate_term(provisioner_reward_dusk_per_epoch, chain_reward_fraction, xxx.total_active_stake_dusk, top_up_fraction, apr_mode_fraction=apr_mode_fraction)

tldr = run0.tldr
tldr.epoch_count_cummulative = tldr.term_threshold_epoch_count
tldr.performance_cummulative = tldr.term_threshold_performance

print(f'run0:')
print(f'{json.dumps(run0)}')        

for top_up_fraction in (0, 0.5, 1):

    # first time only
    #chain_reward_fraction = 0.4
    chain_reward_fraction = 1

    #tldr.term_threshold_performance
    #chain_stake_dusk = tldr.chain_stake_dusk
    tldr = attrdict(
        top_up_fraction = top_up_fraction,
        epoch_count_cummulative = 0,
        performance_cummulative = 1,
        #chain_stake_dusk = 120_000_000,
        #chain_stake_dusk = 121131303.4623197,
        chain_stake_dusk = xxx.total_active_stake_dusk,
        )
    """
    {"timestamp": "2025-01-29-0620-55", "provisioner_count": 265, "total_dusk": 121131303.4623197, "total_dusk_hr": "121.1M"}
    {"timestamp": "2025-01-29-0627-07", "provisioner_count": 265, "total_dusk": 121131303.4623197, "total_dusk_hr": "121.1M"}
    {"timestamp": "2025-01-30-2257-02", "provisioner_count": 266, "total_dusk": 121352459.1815225, "total_dusk_hr": "121.4M"}
    {"timestamp": "2025-01-31-2126-12", "provisioner_count": 268, "total_dusk": 121438207.9244244, "total_dusk_hr": "121.4M"}
    {"timestamp": "2025-02-01-1519-07", "provisioner_count": 267, "total_dusk": 121468811.12788671, "total_dusk_hr": "121.5M"}
    {"timestamp": "2025-02-02-1630-15", "provisioner_count": 268, "total_dusk": 121554758.61284117, "total_dusk_hr": "121.6M"}
    {"timestamp": "2025-02-03-1656-16", "provisioner_count": 268, "total_dusk": 121755804.95168017, "total_dusk_hr": "121.8M"}
    {"timestamp": "2025-02-05-1346-15", "provisioner_count": 268, "total_dusk": 122138511.78983888, "total_dusk_hr": "122.1M"}
    {"timestamp": "2025-02-05-1411-49", "provisioner_count": 268, "total_dusk": 122140266.78983888, "total_dusk_hr": "122.1M"}
    """

    terms = list()
    terms.append(tldr)

    while tldr.epoch_count_cummulative < epoch_per_year:
        run = simulate_term(provisioner_reward_dusk_per_epoch, chain_reward_fraction, tldr.chain_stake_dusk, top_up_fraction, apr_mode_fraction=apr_mode_fraction)
        tldr = run.tldr

        tldr.epoch_count_cummulative = terms[-1].epoch_count_cummulative + tldr.term_threshold_epoch_count
        tldr.year_count_cummulative = round(tldr.epoch_count_cummulative / epoch_per_year, 3)
        tldr.performance_cummulative = terms[-1].performance_cummulative * tldr.term_threshold_performance

        tldr.performance_apr = pow(tldr.performance_cummulative, epoch_per_year / tldr.epoch_count_cummulative) - 1
        tldr.performance_apr_hr = f'{tldr.performance_apr*100:.2f}%'

        #chain_stake_dusk = tldr.chain_stake_dusk

        terms.append(tldr)

        chain_reward_fraction = 1

    return_apr = pow(tldr.performance_cummulative, epoch_per_year / tldr.epoch_count_cummulative) - 1
    return_apr_hr = f'{return_apr*100:.2f}%'
    #print(f'return_apr: {return_apr:.4f}')
    #print(f'return_apr_hr: {return_apr_hr}')
    #print(f'terms:')
    print(f'{json.dumps([terms[1], terms[-2], terms[-1]])}')        




#day_str = None
#epoch_fraction = 0.5
#epoch = None

print(f"""
# Dusk Provisionomics

It's {now_str}, day {mainnet_time_delta.days+1} of Dusk mainnet.  The chain height is {block_height:_} blocks.
Epoch {epoch:_} is underway and is {epoch_fraction*100:.2f}% complete, and the next epoch starts in about {next_epoch_minutes} minutes.

At this time {num_genesis_provisioners} of the current {num_provisioners} provisioners have rewards with block 0 maturity.
That is, these {genesis_provisioners_fraction*100:.1f}% of provisioners were staked in the genesis block and have never unstaked.
Only {num_genesis_provisioners_top_up} of them have topped up, so {num_genesis_provisioners_no_top_up} have never topped up.

These {num_genesis_provisioners} provisioners are staking {genesis_stake_Mdusk:.1f}M Dusk.  The unclaimed (unminted) rewards of these provisioners total {genesis_stake_rewards_Mdusk:.1f}M Dusk.
That is, their rewards are {genesis_rewards_per_stake*100:.2f}% of their stake, which compares with the 2.40% restaking threshold suggested by [x](https://y).

The total staked Dusk is {total_stake_Mdusk:.1f}M, so these {num_genesis_provisioners} provisioners hold {genesis_stake_fraction*100:.1f}% of the total stake.
These unclaimed rewards would increase the total stake by {genesis_stake_rewards_Mdusk / total_stake_Mdusk * 100:.2f}% if they were all restaked.
These unclaimed rewards would increase the total stake by {genesis_stake_rewards_Mdusk / total_stake_Mdusk * 100 * 0.9:.2f}% if they were all used to top up.

""")

"""
Heh, 150 of the present 265 provisioners still have rewards with block 0 maturity (haven't restaked) with unclaimed rewards of 94.7M Dusk out of the 121.1M total staked Dusk.  That is, 56.8% of provisioners have not claimed rewards since genesis, and they hold 78.2% of the total stake.

As of 2025-01-29 07:05:56 UTC, 

150 of the present 265 provisioners still have rewards with block 0 maturity,  That is, 56.6% of provisioners have staked since genesis and have not withdrawn their rewards.

These 150 provisioners are staking 94.7M Dusk. The (unminted) rewards of these provisioners total 2.0M Dusk.  That is, their rewards are 2.2% of their stake, which is below the 2.4% optimum I suggested a couple of days ago.

The total staked Dusk is 120.5M, so these 150 provisioners hold 78.5% of the total stake.

I'm working on codifying my simulations.  I'll probably put the above analysis on an endpoint when I have a few moments.

 are unclaimed rewards of 94.7M Dusk out of the 121.1M total staked Dusk.  That is, 56.8% of provisioners have not claimed rewards since genesis, and they hold 78.2% of the total stake.
"""

stakes = sorted(provisioner.active_stake_dusk for provisioner in xxx.provisioners)
print(f'')
