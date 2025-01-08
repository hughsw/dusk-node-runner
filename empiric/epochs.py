#!/usr/bin/env python3

num_epochs = 100

print(f'DUSK -- first {num_epochs} epochs')
BLOCK_PER_EPOCH = 4320 // 2
print(f'BLOCK_PER_EPOCH: {BLOCK_PER_EPOCH}')

print()
for epoch in range(100):
    print(f'epoch: {epoch}, block: {epoch * BLOCK_PER_EPOCH}')
