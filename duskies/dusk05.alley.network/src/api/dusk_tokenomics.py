#!/app/pyvenv/bin/python3

import time
import asyncio
import json
import functools

import requests

from utils import attrdict, printio, getio, postio, caching

async def getio_supply_dusk(*, circulating_supply_uri = 'https://supply.dusk.network/'):
    try:
        supply_response = await getio(circulating_supply_uri)
        circulating_supply_dusk = float(supply_response.text)
        circulating_supply_timestamp_sec = int(time.time())

        return dict(
            circulating_supply_uri = circulating_supply_uri,
            circulating_supply_dusk = circulating_supply_dusk,
            circulating_supply_timestamp_sec = circulating_supply_timestamp_sec,
            )

    except:
        return None

async def make_dusk_tokenomics():
    dusk_tokenomics = dict(
        # Dusk Tokenomics
        tokenomics_uri = 'https://docs.dusk.network/learn/tokenomics/',
        token_name = 'Dusk',
        token_symbol = 'DUSK',
        initial_supply_dusk = 500_000_000,  # comprising both ERC-20, BEP-20. These will be migrated to native DUSK tokens after the mainnet launch using a burner contract.
        total_emitted_supply_dusk = 500_000_000,  # will be emitted over 36 years to reward stakers on the mainnet, following the Token Emission Schedule.
        maximum_supply_dusk = 1_000_000_000,  # combining the 500M initial supply and 500M emitted over time.
        circulating_supply = await getio_supply_dusk(), # Available on [this page](https://supply.dusk.network/). The circulating supply reflects the initial supply minus the DUSK held by the Dusk deployer. Post-mainnet, this value will increase as additional tokens are emitted.

        ico_uri = 'https://icodrops.com/dusk/',
        ico_raised_dollar = 8_000_000,  # Raised $8 million in November 2018, with tokens priced at $0.0404. Private sale tokens account for 50% of the total supply, split between 10% DUSK BEP20 and 40% DUSK ERC20.
        ico_dollar_per_dusk = 0.0404,  # Raised $8 million in November 2018, with tokens priced at $0.0404. Private sale tokens account for 50% of the total supply, split between 10% DUSK BEP20 and 40% DUSK ERC20.
        ico_date_year = 2018,   # Raised $8 million in November 2018, with tokens priced at $0.0404. Private sale tokens account for 50% of the total supply, split between 10% DUSK BEP20 and 40% DUSK ERC20.
        ico_date_month = 11,   # Raised $8 million in November 2018, with tokens priced at $0.0404. Private sale tokens account for 50% of the total supply, split between 10% DUSK BEP20 and 40% DUSK ERC20.

        # Dusk Contracts
        dusk_contracts = [
            dict(
                contract_name = 'Ethereum',
                contract_chain = 'ERC20',
                contract_id = '0x940a2db1b7008b6c776d4faaca729d6d4a4aa551',
                contract_uri = 'https://etherscan.io/token/0x940a2db1b7008b6c776d4faaca729d6d4a4aa551',
            ),
            dict (
                contract_name = 'Binance Smart Chain',
                contract_chain = 'BEP20',
                contract_id = '0xb2bd0749dbe21f623d9baba856d3b0f0e1bfec9c',
                contract_uri = 'https://bscscan.com/token/0xb2bd0749dbe21f623d9baba856d3b0f0e1bfec9c',
            ),
        ],

        # Dusk Markets
        dusk_markets = [
            dict(
                market_name = 'Coinmarketcap',
                market_uri = 'https://coinmarketcap.com/currencies/dusk/',
                ),
            dict(
                market_name = 'Coingecko',
                market_uri = 'https://www.coingecko.com/en/coins/dusk',
                ),
            ],

        # Token Allocation and Vesting
        token_allocation_and_vesting_start_year = 2019,
        token_allocation_and_vesting_start_month = 5,
        token_allocation_and_vesting_end_year = 2022,
        token_allocation_and_vesting_end_month = 4,
        token_allocation_and_vesting_table = [
            dict(
                allocation_category_name = 'Token Sale',
                allocation_percentage = 50,
                allocation_tokens_dusk = 250000000,
                allocation_vested_tokens_dusk = 250000000,
                ),
            dict(
                allocation_category_name = 'Team',
                allocation_percentage = 6.4,
                allocation_tokens_dusk = 32000000,
                allocation_vested_tokens_dusk = 32000000,
                ),
            dict(
                allocation_category_name = 'Advisors',
                allocation_percentage = 6.4,
                allocation_tokens_dusk = 32000000,
                allocation_vested_tokens_dusk = 32000000,
                ),
            dict(
                allocation_category_name = 'Development',
                allocation_percentage = 18.1,
                allocation_tokens_dusk = 90500000,
                allocation_vested_tokens_dusk = 90500000,
                ),
            dict(
                allocation_category_name = 'Exchange',
                allocation_percentage = 11.8,
                allocation_tokens_dusk = 59000000,
                allocation_vested_tokens_dusk = 59000000,
                ),
            dict(
                allocation_category_name = 'Marketing',
                allocation_percentage = 7.3,
                allocation_tokens_dusk = 36500000,
                allocation_vested_tokens_dusk = 36500000,
                ),
            dict(
                allocation_category_name = 'Total',
                allocation_percentage = 100,
                allocation_tokens_dusk = 500000000,
                allocation_vested_tokens_dusk = 500000000,
                ),
            ],

        staking_min_dusk = 1000,
        staking_max_dusk = 'unbounded',
        staking_maturity_period_epochs = 2,
        staking_maturity_period_blocks = 4320,
        unstaking_penalty_dusk = 0,
        unstaking_wait_period_blocks = 0,

        emission_period_years = 4,
        emission_periods = [
            dict(
                emission_period_index_one_based = 1,
                emission_period_year_range_zero_based = (0, 4),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 19.8574,
                ),
            dict(
                emission_period_index_one_based = 2,
                emission_period_year_range_zero_based = (4, 8),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 9.9287,
                ),
            dict(
                emission_period_index_one_based = 3,
                emission_period_year_range_zero_based = (8, 12),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 4.9644,
                ),
            dict(
                emission_period_index_one_based = 4,
                emission_period_year_range_zero_based = (12, 16),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 2.4822,
                ),

            dict(
                emission_period_index_one_based = 5,
                emission_period_year_range_zero_based = (16, 20),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 1.2411,
                ),
            dict(
                emission_period_index_one_based = 6,
                emission_period_year_range_zero_based = (20, 24),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 0.6206,
                ),
            dict(
                emission_period_index_one_based = 7,
                emission_period_year_range_zero_based = (24, 28),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 0.3103,
                ),
            dict(
                emission_period_index_one_based = 8,
                emission_period_year_range_zero_based = (28, 32),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 0.1551,
                ),
            dict(
                emission_period_index_one_based = 9,
                emission_period_year_range_zero_based = (32, 36),
                emission_period_duration_blocks = 12_614_400,
                emission_period_dusk_per_block = 0.0776,
                ),
            ],

        incentive_block_generator_fraction = 0.7,
        incentive_block_generator_credits_fraction_min = 0.0,
        incentive_block_generator_credits_fraction_max = 0.1,
        incentive_development_fund_fraction = 0.1,
        incentive_validation_committee_fraction = 0.05,
        incentive_ratification_committee_fraction = 0.05,


    zzz = """
    Incentive Structure
    To ensure network security, economic sustainability, and consensus efficiency, the following reward distribution structure is applied:

    70% to the Block Generator (proposal step) and an extra 10% depending on the credits included in the certificate. Any undistributed rewards from this 10% are burned as part of the gas-burning mechanism.
    10% to the Dusk Development Fund
    5% to the Validation Committee (validation step)
    5% to the Ratification Committee (ratification step)


    Key aspects of the DUSK token emission schedule include:

    36-Year Emission Duration: The token emission is distributed across 36 years, divided into 9 periods of 4 years each.
    Emission Reduction Every 4 Years: Token emission decreases every 4 years by a fixed reduction rate, ensuring gradual reduction in token issuance, similar to Bitcoin’s halving model.
    Token Emission
    The emission rate starts with a reduction rate r = 0.5, meaning the token emission halves every 4 years. This strategy is designed to rapidly build network participation by providing strong early incentives.

    Period (Years)	Period Duration (Blocks)	Total Emission (DUSK)	Total Supply (Cumulative)	Emission Per Block	Reduction Rate (r)
    1 (0-4)	12,614,400	250.48M	250.48M	19.8574 DUSK/block	N/A
    2 (4-8)	12,614,400	125.24M	375.72M	9.9287 DUSK/block	0.5
    3 (8-12)	12,614,400	62.62M	438.34M	4.9644 DUSK/block	0.5
    4 (12-16)	12,614,400	31.31M	469.65M	2.4822 DUSK/block	0.5
    5 (16-20)	12,614,400	15.65M	485.30M	1.2411 DUSK/block	0.5
    6 (20-24)	12,614,400	7.83M	493.13M	0.6206 DUSK/block	0.5
    7 (24-28)	12,614,400	3.91M	497.04M	0.3103 DUSK/block	0.5
    8 (28-32)	12,614,400	1.95M	498.99M	0.1551 DUSK/block	0.5
    9 (32-36)	12,614,400	0.98M	499.97M	0.0776 DUSK/block	0.5
    """

    )

    # simple attribute lookup for JSON-ready structures
    dusk_tokenomics = attrdict.deep(dusk_tokenomics)

    # cleanup
    del dusk_tokenomics.zzz

    # derived values
    dusk_tokenomics.block_per_epoch = dusk_tokenomics.staking_maturity_period_blocks // dusk_tokenomics.staking_maturity_period_epochs
    dusk_tokenomics.emission_periods_count = len(dusk_tokenomics.emission_periods)

    emission_period_cummulative_dusk = 0
    one_million_recip = 1 / 1_000_000
    for emission_period in dusk_tokenomics.emission_periods:
        emission_period.emission_period_total_dusk = emission_period.emission_period_duration_blocks * emission_period.emission_period_dusk_per_block
        emission_period_cummulative_dusk += emission_period.emission_period_total_dusk
        emission_period.emission_period_cummulative_dusk = emission_period_cummulative_dusk

        emission_period.emission_period_total_dusk_human_readable = f'{emission_period.emission_period_total_dusk * one_million_recip:.2f}M'
        emission_period.emission_period_cummulative_dusk_human_readable = f'{emission_period.emission_period_cummulative_dusk * one_million_recip:.2f}M'


    # round trip validation, and removes attrdict which doesn't play well with pydantic
    dusk_tokenomics_json = json.dumps(dusk_tokenomics, separators=(",",":"))
    dusk_tokenomics = json.loads(dusk_tokenomics_json)

    return dusk_tokenomics


@caching(10)
async def dusk_tokenomics():
    return await make_dusk_tokenomics()
