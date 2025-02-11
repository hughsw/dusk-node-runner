#!/usr/bin/env python3

# Quick and dirty simulation of Dusk compounding over three years of monthly rewards compounding with no topping up.

# Copyright:  20 Octaves, LLC
# License:    Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)

import math
import json
import requests



def make_dusk_tokenomics():
    class attrdict(dict):
        # Access dict entries with dot notation. Good enough for API JSON work, but doesn't play well with introspective tools, e.g. pydantic.
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

    provisioners_uri = 'https://nodes.dusk.network/on/node/provisioners'
    node_info_uri =  'https://nodes.dusk.network/on/node/info'
    block_height_uri = 'https://nodes.dusk.network/on/graphql/query'
    block_height_query = b'query { block(height: -1) { header { height } } }'


    #result = requests.post(provisioners_uri)

    # See: https://docs.dusk.network/learn/tokenomics/
    tokenomics = attrdict(
        tokenomics_uri = 'https://docs.dusk.network/learn/tokenomics/',
        # Staking Details
        emission_dusk_per_block = 19.8574,
        #chain_block_per_epoch = 2_160,
        #chain_block_per_period = 12_614_400,
        emission_year_per_period = 4,
        # First Emission Period

        # Non-staking duration when restaking: 0.5 for (expectation of) the fraction of
        # the ending epoch that is not staked plus 1 for the non-staking (maturity) of the
        # next epoch.  Obsessive provisioners will push this closer to 1.0
        #maturity_expected_epoch_count = 1.5,

        genesis_stake_dusk = 100_640_637.9746151,
        dusk_lux_per_dusk = 1_000_000_000,

        # Manifest constants
        manifest_month_per_year = 12, 
        manifest_day_per_year = 365,  # 365 gives whole numbers in Dusk tokenomics; 364.2425 does not
    )

    # Derived constants
    chain_block_emission_rates = attrdict(
        chain_block_per_epoch = 2_160,
        chain_block_per_period = 12_614_400,
    )
    chain_block_emission_rates.chain_block_per_year = chain_block_emission_rates.chain_block_per_period // tokenomics.emission_year_per_period
    chain_block_emission_rates.chain_block_per_month = chain_block_emission_rates.chain_block_per_year // tokenomics.manifest_month_per_year
    chain_block_emission_rates.chain_block_per_3_4_month = int(3 / 4 * chain_block_emission_rates.chain_block_per_month)
    chain_block_emission_rates.chain_block_per_21_day = 21 * chain_block_emission_rates.chain_block_per_year // tokenomics.manifest_day_per_year
    chain_block_emission_rates.chain_block_per_day = chain_block_emission_rates.chain_block_per_year // tokenomics.manifest_day_per_year

    tokenomics.chain_block_emission_rates = chain_block_emission_rates

    chain_block_index = attrdict.deep(requests.post(block_height_uri, data=block_height_query).json()).block.header.height
    chain_epoch_index = chain_block_index // chain_block_emission_rates.chain_block_per_epoch
    chain_active_stake_dusk = sum(provisioner.amount for provisioner in attrdict.deep(requests.post(provisioners_uri).json()) if provisioner.eligibility <= chain_block_index) * (1 / tokenomics.dusk_lux_per_dusk)

    variables = attrdict(
        chain_block_index = chain_block_index,
        chain_epoch_index = chain_epoch_index,
        chain_active_stake_dusk = chain_active_stake_dusk,
        #chain_active_stake_dusk = 122473987.0905285,
    )

    maturity_expected_epoch_range = attrdict(
        maturity_expected_epoch_count_min = 1,
        maturity_expected_epoch_count_max = 2,
        )
    maturity_expected_epoch_range.maturity_expected_epoch_count_mean = 0.5 * (maturity_expected_epoch_range.maturity_expected_epoch_count_min + maturity_expected_epoch_range.maturity_expected_epoch_count_max)
    maturity_expected_epoch_range.maturity_expected_epoch_count_deliberate = maturity_expected_epoch_range.maturity_expected_epoch_count_min + (maturity_expected_epoch_range.maturity_expected_epoch_count_max - maturity_expected_epoch_range.maturity_expected_epoch_count_min) / 16

    variables.maturity_expected_epoch_range = maturity_expected_epoch_range

    variables.emission_reward_rates = dict(
        # Provisioner rewards range from 80 to 90 percent of the emission "depending on the credits included in the certificate"
        emission_reward_80_percent_dusk_per_block = round(0.80 * tokenomics.emission_dusk_per_block, 4),
        emission_reward_85_percent_dusk_per_block = round(0.85 * tokenomics.emission_dusk_per_block, 4),
        emission_reward_90_percent_dusk_per_block = round(0.90 * tokenomics.emission_dusk_per_block, 4),
    )

    variables.ad_hoc_node_network_node_count = 100
    variables.ad_hoc_node_network_node_stake_dusk = 600_000
    variables.non_compounding_stakes = dict(
        non_compounding_stake_zero_dusk = 0,
        non_compounding_stake_ad_hoc_node_network_dusk = variables.ad_hoc_node_network_node_count * variables.ad_hoc_node_network_node_stake_dusk,
        non_compounding_stake_ad_hoc_empirical_dusk = 64_039_460,
        )

    variables.external_added_stakes = dict(
        external_added_stake_zero_dusk_per_epoch = 0,
        external_added_stake_ad_hoc_empirical_dusk_per_epoch = int((variables.chain_active_stake_dusk - tokenomics.genesis_stake_dusk) / variables.chain_epoch_index),
        )

    tokenomics.variables = variables

    return tokenomics

def run_year(tokenomics, non_compounding_stake_dusk, start_total_stake_dusk, run_month_count):

    # This can be any non-zero value because it cancels out in the apy calculation, but
    # it's helpful for readers to give it a Dusk name and familiar positive value
    node_start_stake_dusk = 1_000

    # Run each of the reward rates
    variables = tokenomics.variables
    for emission_reward_rate_name, emission_reward_dusk_per_block in variables.emission_reward_rates.items():
        emission_reward_dusk_per_month = emission_reward_dusk_per_block * tokenomics.chain_block_emission_rates.chain_block_per_month
        emission_reward_dusk_per_epoch = emission_reward_dusk_per_block * tokenomics.chain_block_emission_rates.chain_block_per_epoch

        print(f'start_total_stake_dusk: {start_total_stake_dusk:_.0f}, non_compounding_stake_dusk: {non_compounding_stake_dusk:_}, {emission_reward_rate_name}: {emission_reward_dusk_per_block:.2f}')

        node_stake_dusk = node_start_stake_dusk
        chain_stake_dusk = start_total_stake_dusk
        compound_growth = 1
        for month_number in range(1, run_month_count + 1):
            # average fraction of rewards that the node will get this month
            node_fraction = node_stake_dusk / chain_stake_dusk

            # restake the reward at end of the month, but overcounts the maturity epochs
            node_stake_dusk += emission_reward_dusk_per_month * node_fraction
            # fix overcount of maturity epochs

            node_stake_dusk -= variables.maturity_expected_epoch_range.maturity_expected_epoch_count_deliberate * emission_reward_dusk_per_epoch * node_fraction
            #node_stake_dusk -= tokenomics.maturity_expected_epoch_count * emission_reward_dusk_per_epoch * node_fraction

            # assumption of compounding optimality: long term, there's a fixed stake that
            # doesn't compound, while the rest of stake does compounding restakes
            non_compounding_fraction = non_compounding_stake_dusk / chain_stake_dusk
            chain_stake_dusk += emission_reward_dusk_per_month  * (1 - non_compounding_fraction)
                
            if month_number % tokenomics.manifest_month_per_year == 0:
                growth = node_stake_dusk / node_start_stake_dusk
                compound_growth *= growth
                # reset for per year apr 
                node_start_stake_dusk = node_stake_dusk

                per_year_apy = growth - 1
                print(f'  month: {month_number}, per_year_apy: {per_year_apy*100:.2f}%')
        
        APY = math.pow(compound_growth, tokenomics.manifest_month_per_year / run_month_count) - 1
        print(f'  compound APY: {APY*100:.2f}%')


if __name__ == '__main__':
    import sys

    start_total_stake_dusk = float(sys.argv[1])
    run_month_count = 36

    dusk_tokenomics = make_dusk_tokenomics()
    print(f'dusk_tokenomics:')
    print(f'{json.dumps(dusk_tokenomics)}')

    # Toying with the idea that the Dusk Node Network does not do compounding of its stake
    zero_non_compounding_stake_dusk = 0
    dusk_node_network_non_compounding_stake_dusk = 100 * 600_000
    empirical_non_compounding_stake_dusk = 64_039_460

    # TODO: clarify if the non_compounding_stake_dusk concept is reasonable for these long-term simulations
    for non_compounding_stake_dusk in (zero_non_compounding_stake_dusk, dusk_node_network_non_compounding_stake_dusk, empirical_non_compounding_stake_dusk):
        run_year(dusk_tokenomics, non_compounding_stake_dusk, start_total_stake_dusk, run_month_count)
