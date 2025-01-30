#!/usr/bin/env python3

from datetime import datetime, timezone
import json
import requests
from itertools import count


provisioners_uri = 'https://nodes.dusk.network/on/node/provisioners'

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


# get dusk_tokenomics
block_per_epoch = 2160

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


provisioners = attrdict.deep(result.json())
print(f'{json.dumps(provisioners[0])}')


lux_factor = 1 / 1_000_000_000
Mdusk_factor = 1 / 1_000_000

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

genesis_provisioners = tuple(provisioner for provisioner in provisioners if provisioner.eligibility == 0)
num_genesis_provisioners = len(genesis_provisioners)
print(f'num_genesis_provisioners: {num_genesis_provisioners}')

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



#day_str = None
#epoch_fraction = 0.5
#epoch = None

print(f"""
# Dusk Compounding

It's {now_str}, day {mainnet_time_delta.days} of Dusk mainnet.  The chain height is {block_height:_} blocks.   Epoch {epoch:_} is underway and is {epoch_fraction*100:.2f}% complete, and the next epoch starts in about {next_epoch_minutes} minutes.

At this time {num_genesis_provisioners} of the current {num_provisioners} provisioners have rewards with block 0 maturity,  That is, {genesis_provisioners_fraction*100:.1f}% of provisioners have staked since genesis and have never unstaked, although they may have topped up.  

These {num_genesis_provisioners} provisioners are staking {genesis_stake_Mdusk:.1f}M Dusk. The unclaimed (unminted) rewards of these provisioners total {genesis_stake_rewards_Mdusk:.1f}M Dusk.  That is, their rewards are {genesis_rewards_per_stake*100:.2f}% of their stake, which compares with the 2.4% restaking threshold suggested by [x](https://y).

The total staked Dusk is {total_stake_Mdusk:.1f}M, so these {num_genesis_provisioners} provisioners hold {genesis_stake_fraction*100:.1f}% of the total stake, and these unclaimed rewards would increase the total stake by {genesis_stake_rewards_Mdusk / total_stake_Mdusk * 100:.2f}% if they were restaked or {genesis_stake_rewards_Mdusk / total_stake_Mdusk * 100 * 0.9:.2f}% if they were all used to top up.

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
