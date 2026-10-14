# Retrieval evaluation

20 queries over 10,000 titles. Relevance is defined by catalog metadata (see `eval/queries.json`); paraphrase queries deliberately avoid the genre words.
Sliders are left neutral (0.5) for the semantic engine.

## All queries (20)

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| Random (expected) | 0.08 | 0.08 | n/a |
| TF-IDF keywords | 0.34 | 0.34 | 0.41 |
| Semantic engine | 0.45 | 0.41 | 0.58 |

## Paraphrase queries only (17)

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| Random (expected) | 0.07 | 0.07 | n/a |
| TF-IDF keywords | 0.22 | 0.22 | 0.31 |
| Semantic engine | 0.39 | 0.35 | 0.51 |

## Explicit queries only (3)

| Ranker | P@5 | P@10 | MRR |
|---|---:|---:|---:|
| Random (expected) | 0.16 | 0.16 | n/a |
| TF-IDF keywords | 1.00 | 1.00 | 1.00 |
| Semantic engine | 0.80 | 0.77 | 1.00 |

## Per query (P@5)

| Query | Type | Relevant titles | Random | TF-IDF | Semantic |
|---|---|---:|---:|---:|---:|
| spooky ghost and monster stories | paraphrase | 1,123 | 0.11 | 0.20 | 0.40 |
| giant robots fighting in outer space | paraphrase | 977 | 0.10 | 0.60 | 0.20 |
| a sweet love story between classmates | paraphrase | 1,318 | 0.13 | 0.20 | 0.80 |
| a detective solving murders | paraphrase | 761 | 0.08 | 0.00 | 0.60 |
| lighthearted funny stories about everyday life | paraphrase | 977 | 0.10 | 1.00 | 0.60 |
| costumed heroes protecting the city | paraphrase | 1,962 | 0.20 | 0.80 | 0.00 |
| an ordinary person transported to another world | paraphrase | 250 | 0.03 | 0.00 | 0.00 |
| samurai and warriors in feudal times | paraphrase | 569 | 0.06 | 0.00 | 0.00 |
| athletes competing to win the championship | paraphrase | 255 | 0.03 | 0.00 | 1.00 |
| a rock band chasing their musical dreams | paraphrase | 129 | 0.01 | 0.00 | 0.80 |
| players trapped inside a video game | paraphrase | 134 | 0.01 | 0.00 | 0.20 |
| kung fu masters and fighting tournaments | paraphrase | 187 | 0.02 | 0.00 | 0.80 |
| ancient gods and legendary myths | paraphrase | 209 | 0.02 | 0.00 | 0.00 |
| a dark mind-bending thriller | paraphrase | 1,062 | 0.11 | 1.00 | 0.60 |
| wizards, dragons and magical quests | paraphrase | 1,405 | 0.14 | 0.00 | 0.40 |
| growing up and finding yourself as a teenager | paraphrase | 130 | 0.01 | 0.00 | 0.00 |
| heroes caught up in government conspiracies | paraphrase | 399 | 0.04 | 0.00 | 0.20 |
| Marvel superhero comics | explicit | 1,240 | 0.12 | 1.00 | 1.00 |
| manga drawn in black and white | explicit | 3,143 | 0.31 | 1.00 | 1.00 |
| comics painted in watercolor | explicit | 289 | 0.03 | 1.00 | 0.40 |
