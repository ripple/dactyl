---
parent: usage.html
targets: [everything]
---
# Style Checking

The style checker is experimental. It is only suitable for English text. It reports several details about document contents that may be helpful for identifying documents whose readability you could improve. These details are:

- Discouraged words and phrases.
- Page length details.
- Readability scores.
- Spell-checking.

Example usage:

```sh
$ dactyl_style_checker
```

The style checker re-generates contents in-memory (never writing it out), unlike the link checker which requires you to run `dactyl_build` first. It only checks contents that come from Markdown, not from HTML templates.

The style checker uses the first target in the config file unless you specify another target with `-t`. You can check just one file by passing its HTML path in the `--only` parameter.

The exit code of the command is 0 (success) if it found no discouraged words, the spell checker found no unknown words, and no pages failed their configured readability goals. Otherwise, the exit code of the command is 1 (failure).


## Discouraged Words and Phrases

You can suggest specific words or phrases to discourage. The style checker checks for instances of these words and phrases in documents' content, and suggests alternatives based on the phrase file. Dactyl does not check text in `<code>`, `<pre>`, and `<tt>` elements since those are intended to be code samples.

To configure lists of discouraged words and phrases, add the following config options:

| Field                       | Value  | Description                           |
|:----------------------------|:-------|:--------------------------------------|
| `word_substitutions_file`   | String | The path to a YAML file with a single top-level map. The keys are the words to discourage and the values are suggestions of words to replace them with. |
| `phrase_substitutions_file` | String | The path to a YAML file with a single top-level map. The keys are phrases to discourage and the values are suggestions of phrases to replace them with. |

You can add an exemption to a specific discouraged word/phrase rule with an HTML comment. The exemption applies to the whole output (HTML) file in which it appears.

```html
Maybe the word "will" is a discouraged word, but you really want to use it here without flagging it as a violation? Adding a comment like this <!-- STYLE_OVERRIDE: will --> makes it so.
```

## Spell Checking

Dactyl uses [pyspellchecker](https://pyspellchecker.readthedocs.io/en/latest/) to report possible spelling errors and suggest corrections. The built-in dictionary is not very thorough; you can extend it by providing a dictionary file with more words. Spell checking is case-insensitive.

If you want the spell checker to skip a page, put `skip_spell_checker: true` in the page definition.

If you want to ignore one or more words on a single page only, add a comment such as the following anywhere in the page:

```html
<!-- IGNORE_SPELLING: affectednodes, creatednode, deletednode, modifiednode -->
```

To extend the built-in dictionary used for all files, add the following field to the config. (You cannot remove words from the built-in dictionary.)

| Field           | Value  | Description                                       |
|:----------------|:-------|:--------------------------------------------------|
| `spelling_file` | String | Path to a text file with words to add to the dictionary. Each line of the file should contain a single word (case-insensitive). |


## Length Metrics

Dactyl reports the number of characters of text, number of sentences, and number of words in each document. These counts only include text contents (the parts generated from Markdown). They do not include code samples (not even inlined code words), or images/figures. The sentence counts are estimates. Headings, list items, and table cells each count as one sentence in these metrics. The summary includes the averages across all pages, and the stats for the three longest and shortest pages.

These metrics are intended to be helpful for choosing documents that would be better off combined or split up. They can also be useful for interpreting readability scores, which tend to be less reliable for very short documents.


## Readability Scores

The style checker reports readability scores based on several formulas implemented in the [textstat library](https://github.com/shivam5992/textstat). These can help you identify documents with a high proportion of big words and long sentences.

> **Caution:** Readability formulas are not very smart. Trying to get a high readability score can actually decrease the clarity of your writing if you aren't mindful of other factors. Things readability formulas usually don't take into account include: brevity; complexity of the high-level structure; logical connections such as cause and effect; and precise use of language. They tend to score tables and bulleted lists badly even though those structure are very helpful for actual readability.

By default, Dactyl prints the readability scores for each page as it analyzes them. The `-q` option hides this output. The summary at the end lists the average scores for all pages analyzed and the three pages with the worst Flesch Reading Ease scores.

### Readability Goals

You can set readability goals for individual pages or an entire target by adding the `readability_goals` field. This field should contain a map of readability metrics to target scores. Goals defined for individual pages override goals set for the entire target. Dactyl compares a page's readability scores to any goals set and reports a list of pages that failed their goals in the summary. The goal passes if the page's score is equal better (easier to read) than the stated goal value, and fails otherwise. For Flesch Reading Ease, higher scores represent better readability; for the other tests, _lower_ scores represent better readability.

**Note:** Since very short pages tend to have inconsistent and unreliable readability scores, Dactyl does not calculate readability scores for pages with fewer than 10 "sentences". (Bullet points, headings, and table cells each count as separate "sentences" for this purpose.)

Example configuration:

```yaml
targets:

  - name: my-target
    display_name: Example Target
    readability_goals:
        flesch_reading_ease: 50
        automated_readability_index: 12
```

The available readability tests are:

| Field Name                     | Details                                     |
|:-------------------------------|:--------------------------------------------|
| `flesch_reading_ease`          | [Flesch reading ease](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests#Flesch_reading_ease). Maximum score 121.22; no limit on how negative the score can be. |
| `smog_index`                   | [SMOG grade](https://en.wikipedia.org/wiki/SMOG). Gives an estimated grade level. |
| `coleman_liau_index`           | [Coleman-Liau index](https://en.wikipedia.org/wiki/Coleman%E2%80%93Liau_index). Gives an estimated grade level. |
| `automated_readability_index`  | [Automated readability index](https://en.wikipedia.org/wiki/Automated_readability_index). Gives an estimated grade level. |
| `dale_chall_readability_score` | [Dale-Chall readability formula](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula). Decimal representing difficulty; lower values map to lower grade levels. |
| `linsear_write_formula`        | [Linsear Write formula](https://en.wikipedia.org/wiki/Linsear_Write). Gives an estimated grade level. |
| `gunning_fog`                  | [Gunning fog index](https://en.wikipedia.org/wiki/Gunning_fog_index). Gives an estimated grade level. |

Estimated grade levels are based on the United States school system and are given as decimal approximations. For example, `11.5` represents somewhere between 11th and 12th grade (high school junior to senior).
