#!/usr/bin/env python3

rewards_12hour = (
    14.009513895 / 1000,
    35.683665284 / 50000,
    158.924947804 /150000,
    )

for reward_rate in sorted(rewards_12hour):
    print(f'{reward_rate * 100:.4}%')

reward_range = sorted(rewards_12hour)[-1] / sorted(rewards_12hour)[0]
print(f'reward_range: {reward_range:.3}')


BPS = 1_000_000_000

per_month = BPS * 60 * 60 * 24 * 31 / 8
print(f'per_month: {per_month:_}, {3* per_month:_}, {4 * per_month:_}, ')

kbps = 100
per_month = kbps * 60 * 60 * 24 * 31
print(f'per_month: {per_month:_}, {3* per_month:_}, {4 * per_month:_}, ')
