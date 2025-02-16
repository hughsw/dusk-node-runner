#!/usr/bin/env python3

import sys, os
import json
import collections


class Provisioner(object):

    provisioner_count = 0

    @staticmethod
    def rounded(value):
        return round(value, 9)


    def __init__(self, *, balance=0, stake=0):
        assert balance >= 0 and stake >= 0, str((balance, stake))

        self.key = f'0x{Provisioner.provisioner_count:04x}'
        Provisioner.provisioner_count += 1

        self.balance = balance
        self.stake = stake
        self.reward = 0
        self.locked = 0

    def __str__(self):
        return json.dumps(dict(
            key = self.key,
            balance = self.rounded(self.balance),
            stake = self.rounded(self.stake),
            reward = self.rounded(self.reward),
            locked = self.rounded(self.locked),
            ))

    @property
    def fortune(self):
        return self.rounded(self.balance + self.stake + self.reward + self.locked)


    def unstake(self):
        assert self.stake > 0, str((self.stake,))
        self.balance += self.stake + self.locked
        self.stake = 0
        self.locked = 0

    def withdraw(self):
        self.balance += self.reward
        self.reward = 0

    # who's concern is this logic?
    def do_stake(self, amount):
        assert 0 <= amount <= self.balance, str((amount, self.balance))
        if self.stake == 0:
            self.stake = amount
        else:
            assert self.stake > 0, str((self.stake,))
            self.stake += 0.9 * amount
            self.locked += 0.1 * amount
        self.balance -= amount

    # who's concern is this logic?  block generator, not the provisioner
    def do_reward(self, total_reward, total_stake_recip):
        assert total_reward >= 0, str((total_reward,))
        assert total_stake_recip > 0, str((total_stake_recip,))
        self.reward += self.stake * total_stake_recip * total_reward



print(Provisioner())
print(Provisioner(stake=1_000))
print(Provisioner(balance=1_500))
print(Provisioner(stake=500, balance=1_500))
for i in range(20):
    p = Provisioner(stake=i, balance=i*i)

for i in range(6):
    p = Provisioner(stake=i, balance=i*i)
    initial_fortune = p.fortune
    print(initial_fortune, p)
    if p.stake > 0:
        p.do_reward(5, 1/1_000)
        print(' ', p)
        p.withdraw()
        print(' ', p)
        p.do_stake(p.balance)
        print(' ', p)
        p.do_reward(5, 1/1_000)
        print(' ', p)
        p.unstake()
        print(' ', p)
        p.withdraw()
        print(' ', p.fortune, f'{p.fortune / initial_fortune*100:.2f}%', p)
