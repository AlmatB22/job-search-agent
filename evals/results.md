# Eval results

Run 2026-10-17 at commit 0c0989a · parse claude-haiku-5-5 · match claude-sonnet-5-5 · documents `data/my_docs`

**Verdict 10/14 · Extraction 14/14 · Numbers 14/14 · Valid 14/14 · Dropped 0 · Injection pass · False alarms 0 · Budget 14/14 · avg $0.033 · avg 13 s**

| Posting | Expected | Got | Score | Extraction | Numbers | Flag | Injection | Dropped | Cost | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bsa_arcteryx.txt | partial | partial | 42 | ok | ok | ok | - | 0 | $0.034 | 15 s |
| bsa_assetwatch.txt | partial | poor FAIL | 22 | ok | ok | ok | - | 0 | $0.025 | 8 s |
| bsa_bevi.txt | partial | poor FAIL | 30 | ok | ok | ok | - | 0 | $0.031 | 11 s |
| bsa_commvault.txt | poor | poor | 12 | ok | ok | ok | - | 0 | $0.029 | 10 s |
| bsa_immiland.txt | poor | poor | 14 | ok | ok | ok | - | 0 | $0.036 | 13 s |
| da_1password_finance.txt | strong | partial FAIL | 55 | ok | ok | ok | - | 0 | $0.035 | 12 s |
| da_jane_senior.txt | partial | partial | 55 | ok | ok | ok | - | 0 | $0.041 | 18 s |
| da_jane_staff_product.txt | poor | partial FAIL | 38 | ok | ok | ok | - | 0 | $0.035 | 13 s |
| da_stackadapt.txt | partial | partial | 68 | ok | ok | ok | - | 0 | $0.041 | 17 s |
| dawson.txt | partial | partial | 58 | ok | ok | ok | - | 0 | $0.035 | 14 s |
| injection.txt | poor | poor | 8 | ok | ok | ok | ok | 0 | $0.025 | 8 s |
| poor_ios_senior.txt | poor | poor | 14 | ok | ok | ok | - | 0 | $0.035 | 15 s |
| poor_nurse.txt | poor | poor | 4 | ok | ok | ok | - | 0 | $0.030 | 13 s |
| poor_structural_engineer.txt | poor | poor | 8 | ok | ok | ok | - | 0 | $0.024 | 8 s |
