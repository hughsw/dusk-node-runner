#!/usr/bin/env python3

# TODO: what about [[phoenix_balance]] notes amount ?

genesis_block_filename = 'genesis-block_mainnet.toml'

genesis_stake_lux = 0
genesis_balance_lux = 0
with open(genesis_block_filename, 'rt') as genesis_file:
    for line in genesis_file:
        if line.startswith('balance') or line.startswith('amount'):
            parts = line.split()
            assert len(parts) == 3, str((parts, line))
            amount_lux = int(parts[-1])
            if line.startswith('balance'):
                genesis_balance_lux += amount_lux
            elif line.startswith('amount'):
                genesis_stake_lux += amount_lux
            else:
                assert False, str(('unhandled', parts, line))

total_lux = genesis_stake_lux + genesis_balance_lux

print(f'genesis_stake_lux: {genesis_stake_lux:_}')
print(f'genesis_balance_lux: {genesis_balance_lux:_}')
print(f'total_lux: {total_lux:_}')

dusk_per_lux = 1 / 1_000_000_000

genesis_stake_dusk = genesis_stake_lux * dusk_per_lux
genesis_balance_dusk = genesis_balance_lux * dusk_per_lux
total_dusk = total_lux * dusk_per_lux
print(f'genesis_stake_dusk: {genesis_stake_dusk:_}')
print(f'genesis_balance_dusk: {genesis_balance_dusk:_}')
print(f'total_dusk: {total_dusk:_}')
