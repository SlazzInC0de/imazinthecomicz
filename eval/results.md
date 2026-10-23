# Retrieval benchmark

Catalog: 16276 titles, model `BAAI/bge-small-en-v1.5`, built 2026-10-23.
35 queries from [`eval/queries.json`](queries.json). Relevance = AniList genre/tag labels (descriptive queries) or the series name (title queries).

## All queries

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| random | 0.04 | 0.04 | n/a |
| keyword | 0.51 | 0.45 | 0.72 |
| semantic | 0.53 | 0.47 | 0.75 |
| **hybrid** | 0.59 | 0.50 | 0.81 |

## Descriptive queries

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| random | 0.05 | 0.05 | n/a |
| keyword | 0.47 | 0.44 | 0.67 |
| semantic | 0.49 | 0.45 | 0.71 |
| **hybrid** | 0.55 | 0.49 | 0.78 |

## Title queries

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| random | 0.00 | 0.00 | n/a |
| keyword | 0.76 | 0.54 | 1.00 |
| semantic | 0.76 | 0.56 | 1.00 |
| **hybrid** | 0.80 | 0.58 | 1.00 |

## Match label calibration

Cosine of relevant top-10 hits: median 0.610, 25th pct 0.581  
Cosine of irrelevant top-10 hits: median 0.607, 75th pct 0.638

## Per query (hybrid)

| Query | Type | Relevant titles | P@10 | MRR |
|---|---|---:|---:|---:|
| someone who solves murders by finding clues | descriptive | 1189 | 0.8 | 1.00 |
| spirits haunting an old house | descriptive | 1049 | 0.6 | 0.33 |
| teenagers piloting giant robots | descriptive | 135 | 0.6 | 0.50 |
| two classmates slowly falling for each other | descriptive | 8370 | 1.0 | 1.00 |
| cozy calm everyday life where nothing bad happens | descriptive | 3209 | 0.4 | 1.00 |
| an office worker dies and wakes up in another world | descriptive | 1441 | 0.3 | 0.50 |
| high school volleyball team chasing the national title | descriptive | 415 | 1.0 | 1.00 |
| a rock band chasing their dream of playing live | descriptive | 181 | 0.8 | 1.00 |
| players stuck inside an online game | descriptive | 247 | 0.4 | 0.50 |
| fighters training for a fighting tournament | descriptive | 364 | 0.5 | 0.33 |
| ancient deities and legends walking among humans | descriptive | 341 | 0.3 | 0.50 |
| two geniuses outsmarting each other with mind games | descriptive | 1184 | 0.1 | 1.00 |
| students learning spells at an academy | descriptive | 1325 | 0.4 | 0.33 |
| a chef making delicious dishes for customers | descriptive | 305 | 0.9 | 1.00 |
| survivors after the dead rise and the world ends | descriptive | 295 | 0.6 | 1.00 |
| blood drinking creatures of the night | descriptive | 232 | 0.7 | 1.00 |
| reborn as the evil noble lady of a romance novel | descriptive | 204 | 0.3 | 1.00 |
| swordsmen in feudal era japan | descriptive | 82 | 0.3 | 1.00 |
| training the body and soul to reach immortality | descriptive | 182 | 0.4 | 1.00 |
| fleets of starships at war across the galaxy | descriptive | 237 | 0.7 | 1.00 |
| people forced into a game where losers die | descriptive | 347 | 0.7 | 1.00 |
| romance between coworkers at a company | descriptive | 186 | 0.6 | 0.50 |
| people born with special abilities protecting the city | descriptive | 567 | 0.3 | 1.00 |
| a heartbreaking story that ends in loss | descriptive | 495 | 0.2 | 1.00 |
| he returns to make those who betrayed him pay | descriptive | 362 | 0.4 | 1.00 |
| a young girl transforms to fight evil with magic | descriptive | 106 | 0.3 | 0.50 |
| slaying demons with a blade | descriptive | 624 | 0.0 | 0.06 |
| going back in time to change what happened | descriptive | 427 | 0.5 | 1.00 |
| street gangs and tough guys fighting for respect | descriptive | 267 | 0.4 | 1.00 |
| prodigies playing go, shogi or chess | descriptive | 5 | 0.1 | 0.25 |
| One Piece | title | 11 | 0.9 | 1.00 |
| solo leveling | title | 2 | 0.2 | 1.00 |
| berserk | title | 7 | 0.7 | 1.00 |
| attack on titan | title | 8 | 0.8 | 1.00 |
| chainsaw man | title | 3 | 0.3 | 1.00 |
