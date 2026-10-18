# Eval results

Run 2026-10-17 at commit 934e4e6 · parse claude-haiku-5-5 · match claude-sonnet-5-5 · documents `data/my_docs` · each posting run 3 times

**Verdict 12/14 · Stable 12/14 (x3) · Extraction 14/14 · Numbers 14/14 · Valid 14/14 · Dropped 0 · Injection pass · False alarms 0 · Budget 14/14 · avg $0.033 · avg 13 s**

| Posting | Expected | Got | Score | Extraction | Numbers | Flag | Injection | Dropped | Cost | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bsa_arcteryx.txt | partial | partial 3/3 | 42 (42/42/42) | ok | ok | ok | - | 0 | $0.035 | 14 s |
| bsa_assetwatch.txt | partial | partial 2/3 | 34 (42/42/18) | ok | ok | ok | - | 0 | $0.029 | 11 s |
| bsa_bevi.txt | partial | poor 3/3 FAIL | 30 (30/30/30) | ok | ok | ok | - | 0 | $0.035 | 13 s |
| bsa_commvault.txt | poor | poor 3/3 | 13 (10/14/14) | ok | ok | ok | - | 0 | $0.031 | 12 s |
| bsa_immiland.txt | poor | poor 3/3 | 15 (14/18/12) | ok | ok | ok | - | 0 | $0.038 | 14 s |
| da_1password_finance.txt | strong | partial 3/3 FAIL | 61 (66/55/62) | ok | ok | ok | - | 0 | $0.038 | 14 s |
| da_jane_senior.txt | partial | partial 3/3 | 49 (42/50/55) | ok | ok | ok | - | 0 | $0.033 | 14 s |
| da_jane_staff_product.txt | poor | poor 2/3 | 33 (42/30/28) | ok | ok | ok | - | 0 | $0.035 | 13 s |
| da_stackadapt.txt | partial | partial 3/3 | 53 (58/50/50) | ok | ok | ok | - | 0 | $0.036 | 15 s |
| dawson.txt | partial | partial 3/3 | 65 (66/62/66) | ok | ok | ok | - | 0 | $0.045 | 20 s |
| injection.txt | poor | poor 3/3 | 8 (8/8/8) | ok | ok | ok | ok | 0 | $0.026 | 9 s |
| poor_ios_senior.txt | poor | poor 3/3 | 5 (4/8/4) | ok | ok | ok | - | 0 | $0.026 | 9 s |
| poor_nurse.txt | poor | poor 3/3 | 6 (4/6/8) | ok | ok | ok | - | 0 | $0.024 | 9 s |
| poor_structural_engineer.txt | poor | poor 3/3 | 5 (5/4/6) | ok | ok | ok | - | 0 | $0.030 | 13 s |
