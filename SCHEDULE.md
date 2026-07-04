# Posting Schedule

| Day | Time (PKT) | Target Audience | Template |
|---|---|---|---|
| Tuesday | 8:30 AM | Pakistan morning | How I Built / Data & Numbers |
| Wednesday | 3:00 PM | UK morning + US AM | Hot Take / Progress Journey |
| Thursday | 8:30 AM | Pakistan morning | Lesson Learned / How I Built |

## Schedule Change: Kya Karna Hai

Jab live karna ho:
1. `scripts/config.py` mein `DRY_RUN` ko `False` karo
2. Push karo
3. Workflow automatically chalega

## Token Expiry

Access token ~60 days mein expire hoga. Phir se generate karna hoga:
1. Access https://haris.primevoai.com/callback after authorizing again
2. New token ko GitHub Secrets mein update karo
