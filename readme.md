# human-vs-llm-phishing-analyzer


A one page dashboard built on a dataset containing human phishing, human legitimate, LLM phishing, and LLM legitimate emails, with an analyzer that classifies a pasted email entirely in the browser: nothing is sent to a server.

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

The model does not generalize across sources. Trained on human email and tested on LLM email, or the reverse, it scores 47.6% / 57.4% balanced accuracy, approximately chance level. This suggests that the high within dataset accuracy is strongly influenced by differences in writing style and other characteristics of the individual sources, rather than representing general phishing detection ability.

## Project structure

```
site/             the website (the only folder deployed)
  index.html       page + dashboard + analyzer
  model.js         trained model (generated)
  stats.js         dashboard numbers (generated)
  predict.js       in-browser prediction; mirrors train.py
train.py         loads data, trains, exports model.js + stats.js
requirements.txt
dataset/         Kaggle CSVs 
```


## Data notes

- The class (phishing or legit) comes from the **file name**. The CSV `label` column marks human vs. LLM origin, not phishing vs. legit.
- The LLM phishing file isn't quoted, so `train.py` splits each line on its last comma.
- **800 duplicate rows are removed** (4,000 rows → 3,200 distinct emails). Human phishing has most emails twice.
- Text is normalized (Unicode and whitespace) so formatting differences between sources don't become features.

## Limitations

- The human legit emails are 2007–2008 mailing-list messages; the human phishing emails are from 2019–2022. Era and formatting differences inflate accuracy.
- Some top terms are artifacts of how each collection was built (e.g. "monkey" from the monkey.org mailbox, and names like "sarah" in the LLM emails).
- Results reflect this dataset only. **This is not a security tool** and shouldn't be used to judge real email.

## Sources

- **Dataset:** [Human-LLM Generated Phishing-Legitimate Emails](https://www.kaggle.com/datasets/francescogreco97/human-llm-generated-phishing-legitimate-emails) (Kaggle). Human-generated emails come from the Nazario and Nigerian Fraud collections; LLM-generated emails were produced with ChatGPT and WormGPT.
- **Paper:** F. Greco, G. Desolda, A. Esposito, A. Carelli, "David versus Goliath: Can Machine Learning Detect LLM-Generated Text? A Case Study in the Detection of Phishing Emails," *ITASEC 2024*.
- **Libraries:** pandas, scikit-learn, NumPy, SciPy.

