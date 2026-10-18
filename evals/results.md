# Eval results

Run 2026-10-17 at commit 36fd41b · parse claude-haiku-5-5 · match claude-sonnet-5-5 · documents `data/my_docs` · each posting run 3 times

**Verdict 11/14 · Stable 13/14 (x3) · Extraction 14/14 · Numbers 14/14 · Valid 14/14 · Dropped 0 · Injection pass · False alarms 0 · Budget 14/14 · avg $0.034 · avg 14 s**

| Posting | Expected | Got | Score | Extraction | Numbers | Flag | Injection | Dropped | Cost | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bsa_arcteryx.txt | partial | partial 3/3 | 42 (42/42/42) | ok | ok | ok | - | 0 | $0.036 | 15 s |
| bsa_assetwatch.txt | partial | partial 2/3 | 36 (42/45/22) | ok | ok | ok | - | 0 | $0.032 | 13 s |
| bsa_bevi.txt | partial | poor 3/3 FAIL | 30 (30/30/30) | ok | ok | ok | - | 0 | $0.034 | 12 s |
| bsa_commvault.txt | poor | poor 3/3 | 17 (22/15/14) | ok | ok | ok | - | 0 | $0.031 | 12 s |
| bsa_immiland.txt | poor | poor 3/3 | 22 (22/22/22) | ok | ok | ok | - | 0 | $0.035 | 12 s |
| da_1password_finance.txt | strong | partial 3/3 FAIL | 64 (66/58/68) | ok | ok | ok | - | 0 | $0.044 | 18 s |
| da_jane_senior.txt | partial | partial 3/3 | 52 (50/55/52) | ok | ok | ok | - | 0 | $0.034 | 14 s |
| da_jane_staff_product.txt | poor | partial 3/3 FAIL | 47 (42/50/50) | ok | ok | ok | - | 0 | $0.041 | 17 s |
| da_stackadapt.txt | partial | partial 3/3 | 60 (62/55/62) | ok | ok | ok | - | 0 | $0.038 | 16 s |
| dawson.txt | partial | partial 3/3 | 69 (72/68/68) | ok | ok | ok | - | 0 | $0.045 | 20 s |
| injection.txt | poor | poor 3/3 | 9 (12/8/8) | ok | ok | ok | ok | 0 | $0.027 | 10 s |
| poor_ios_senior.txt | poor | poor 3/3 | 9 (12/8/8) | ok | ok | ok | - | 0 | $0.028 | 11 s |
| poor_nurse.txt | poor | poor 3/3 | 6 (4/8/6) | ok | ok | ok | - | 0 | $0.027 | 11 s |
| poor_structural_engineer.txt | poor | poor 3/3 | 6 (8/6/4) | ok | ok | ok | - | 0 | $0.025 | 9 s |
