# human-vs-llm-phishing-analyzer

A one-page dashboard built on a dataset containing human phishing, human legitimate, LLM phishing, and LLM legitimate emails, with an analyzer that classifies a pasted email entirely in the browser: nothing is sent to a server.

## What it does

- **Dashboard:** email counts, length, URLs, urgency words, common terms, and a human vs. LLM comparison across 4 groups (human phishing, human legit, LLM phishing, LLM legit).
- **Model:** TF-IDF (words + word pairs) and 6 numeric features (length, URL count, urgency words, calls to action, capitalization, `!`/`?` rate), fed into a Logistic Regression.
- **Analyzer:** paste an email to get a verdict, a confidence score, and the words and signals that drove the result.

## Results

| | Accuracy (5-fold CV) |
|---|---|
| Overall | 98.8% ± 0.6 |
| Human phishing | 97.4% |
| Human legit | 99.1% |
| LLM phishing | 99.5% |
| LLM legit | 98.4% |

The model does not generalize across sources. Trained on human email and tested on LLM email, or the reverse, it scores 47.6% / 57.4% balanced accuracy, approximately chance level. This suggests that the high within-dataset accuracy is strongly influenced by differences in writing style and other characteristics of the individual sources, rather than representing general phishing detection ability.

## Project structure

```
site/                 the website (the only folder deployed)
  index.html            page + dashboard + analyzer
  model.js              trained model (generated)
  stats.js              dashboard numbers (generated)
  predict.js            in-browser prediction; mirrors train.py
train.py              loads data, removes duplicates, trains, exports model.js + stats.js
check_duplicates.py   reports duplicate rows and duplicate email text per file
requirements.txt
dataset/              Kaggle CSVs
```

## Data notes

- The class (phishing or legit) comes from the **file name**. The CSV `label` column marks human vs. LLM origin, not phishing vs. legit.
- The LLM phishing file isn't quoted, so `train.py` splits each line on its last comma.
- Text is normalized (Unicode and whitespace) so formatting differences between sources don't become features.

### Duplicates

The dataset has 4,000 rows but only **3,200 distinct emails**. Duplicates are removed before training so the same email can't appear in both the training and test sets.

| File | Rows | Identical rows (all columns) | Identical text | Unique text | After normalization |
|---|---|---|---|---|---|
| Human phishing | 1,000 | 496 | 496 | 504 | 500 |
| Human legit | 1,000 | 0 | 274 | 726 | 702 |
| LLM phishing | 1,000 | 0 | 0 | 1,000 | 1,000 |
| LLM legit | 1,000 | 2 | 2 | 998 | 998 |

- **Human phishing** has 496 rows identical in every field: sender, receiver, date down to the second, subject, and body.
- **Human legit** has no fully identical rows, but 274 repeat the same subject and body under a different sender or date (mostly automated mailing-list notices).
- The last column is what `train.py` uses. Normalization also merges emails that differ only in spacing, invisible characters, or encoded subject lines.

To reproduce these counts, run `python check_duplicates.py`.

## Limitations

- The human legit emails are 2007–2008 mailing-list messages; the human phishing emails are from 2019–2022. Era and formatting differences inflate accuracy.
- Some top terms are artifacts of how each collection was built (e.g. "monkey" from the monkey.org mailbox, and names like "sarah" in the LLM emails).
- After removing duplicates, the human phishing group has only 500 emails, the smallest of the four groups.
- Results reflect this dataset only. **This is not a security tool** and shouldn't be used to judge real email.

## Sources

- **Dataset:** [Human-LLM Generated Phishing-Legitimate Emails](https://www.kaggle.com/datasets/francescogreco97/human-llm-generated-phishing-legitimate-emails) (Kaggle). Human-generated emails come from the Nazario and Nigerian Fraud collections; LLM-generated emails were produced with ChatGPT and WormGPT.
- **Paper:** F. Greco, G. Desolda, A. Esposito, A. Carelli, "David versus Goliath: Can Machine Learning Detect LLM-Generated Text? A Case Study in the Detection of Phishing Emails," *ITASEC 2024*.
- **Libraries:** pandas, scikit-learn, NumPy, SciPy.