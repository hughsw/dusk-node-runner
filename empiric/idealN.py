#!/usr/bin/env python3

import requests
from functools import partial
from math import pow
from itertools import count

def eqn(r, k, n):
    rate = (n-1) * r
    return pow(1 + rate, 1 / n), rate
    return pow(1 + rate, k * (1 / n)), rate


def bestn(r):
    assert r > 0, str((r,))
    n_max = 0
    rate_max = 0
    ret_max = 0
    for n in count(1):
        rate = (n-1) * r
        ret = pow(1 + rate, 1 / n)
        if ret <= ret_max:
            return ret_max, rate_max, n_max, n_max/4
        n_max = n
        rate_max = rate
        ret_max = ret
    

#provisioners = requests.post

r = 0.00028661443024968964
#r = 0.0002867
#r = 0.00025
#r = 0.0002

# r is reward factor per epoch, it's the reward factor per block times 2160
# reward factor per block is 16 / total stake
for r in (
        0.0002867,
        0.00028661443024968964,
        0.000286,
        0.00028,
        0.00025,
        0.0002,
        ):
  print(f'r: {r}, bestn(r): {bestn(r)}')

print()
for k in range(50, 4 * 365 + 1, 50):
    e = partial(eqn, r, k)

    vals = list((e(n), n) for n in range(1, 200))

    #print(f'unsorted: r: {r}, k: {k}, vals[0]: {vals[0]}, vals[-1]: {vals[-1]}')
    vals.sort()
    print(f'sorted:   r: {r}, k: {k}, vals[0]: {vals[0]}, vals[-1]: {vals[-1]}')

