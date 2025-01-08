#!/usr/bin/env python3

# "timestamp":"2025-01-08T12:53:49.434175Z","level":"INFO","event":"block accepted","height":8957
# so, 8957 blocks in 24 hours, 53 minutes, 49 seconds

num_blocks = 8957
num_hours = 24 + 53/60 + 49/3600

block_per_hour = num_blocks / num_hours
second_per_block = 3600 / block_per_hour

print(f'block_per_hour: {block_per_hour:.6}, second_per_block: {second_per_block:.6}')
