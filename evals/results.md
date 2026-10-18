# Eval results

Run 2026-10-17 at commit fb2f45e · parse claude-haiku-5-5 · match claude-sonnet-5-5 · documents `data/my_docs` · each posting run 3 times

**Verdict 10/14 · Stable 10/14 (x3) · Extraction 13/14 · Numbers 14/14 · Valid 14/14 · Dropped 0 · Injection pass · False alarms 0 · Budget 14/14 · avg $0.034 · avg 14 s**

| Posting | Expected | Got | Score | Extraction | Numbers | Flag | Injection | Dropped | Cost | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bsa_arcteryx.txt | partial | partial 2/3 | 38 (30/42/42) | ok | ok | ok | - | 0 | $0.035 | 16 s |
| bsa_assetwatch.txt | partial | poor 2/3 FAIL | 29 (22/22/42) | ok | ok | ok | - | 0 | $0.028 | 11 s |
| bsa_bevi.txt | partial | poor 3/3 FAIL | 30 (30/30/30) | ok | ok | ok | - | 0 | $0.032 | 12 s |
| bsa_commvault.txt | poor | poor 3/3 | 14 (14/14/14) | ok | ok | ok | - | 0 | $0.030 | 11 s |
| bsa_immiland.txt | poor | poor 2/3 | 30 (12/40/38) | FAIL | ok | ok | - | 0 | $0.046 | 20 s |
| da_1password_finance.txt | strong | partial 3/3 FAIL | 62 (66/58/62) | ok | ok | ok | - | 0 | $0.046 | 19 s |
| da_jane_senior.txt | partial | partial 3/3 | 42 (42/42/42) | ok | ok | ok | - | 0 | $0.028 | 10 s |
| da_jane_staff_product.txt | poor | partial 2/3 FAIL | 38 (45/42/28) | ok | ok | ok | - | 0 | $0.038 | 16 s |
| da_stackadapt.txt | partial | partial 3/3 | 57 (55/60/55) | ok | ok | ok | - | 0 | $0.035 | 14 s |
| dawson.txt | strong | strong 3/3 | 78 (76/80/78) | ok | ok | ok | - | 0 | $0.050 | 22 s |
| injection.txt | poor | poor 3/3 | 8 (8/8/8) | ok | ok | ok | ok | 0 | $0.026 | 9 s |
| poor_ios_senior.txt | poor | poor 3/3 | 5 (8/4/4) | ok | ok | ok | - | 0 | $0.030 | 12 s |
| poor_nurse.txt | poor | poor 3/3 | 3 (4/2/3) | ok | ok | ok | - | 0 | $0.024 | 9 s |
| poor_structural_engineer.txt | poor | poor 3/3 | 4 (4/4/4) | ok | ok | ok | - | 0 | $0.024 | 9 s |

## Failures

- bsa_immiland.txt: missing must-have: integration
