# Practical DUSK tokenomics

TL;DR Rational Dusk provisioners will, from time to time, execute a three-transaction compounding event (unstake, withdraw rewards, stake with increased balance) in order to achieve better than linear-in-time growth of their Dusk balances.  Given numerous, mostly mild assumptions, at present (2025-Q1) optimal growth is realized if the compounding event is executed whenever the unclaimed rewards exceed 2.4% of the provisioner's stake, which occurs some 80 or so epochs after the previous compounding event.

Caveats:
- A large increase in the overall DUSK stake will reduce the percentage threshold (and overall growth), but will extend the number epochs between compounding events.  E.g. once DUSK coin can be redemed for other coins or fiat currency there may be a large influx of stakes from new provisioners seeking to realize the generous early growth of the Dusk emission schedule.
- Daily or weekly swings in the value of DUSK compared to other coins or fiat currency are likely to routinely exceed the gains in DUSK assets due to implementing the above compounding strategy.
