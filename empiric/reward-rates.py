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
