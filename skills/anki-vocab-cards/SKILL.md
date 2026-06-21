---
name: anki-vocab-cards
description: Create Anki vocabulary and phrase cards for the user's working-vocabulary workflow. Use when the user wants to add an English word, phrase, idiom, collocation, or expression to Anki; asks how to say something in English for writing; provides an entry and example sentence; or wants a Serendipity vocabulary/Phrase note generated with Chinese definitions, example translation, and Chrome tab source metadata.
---

# Anki Vocab Cards

Create source-backed Anki cards for active English writing vocabulary: words and
phrases the user wants available when asking "how do I say X in English?"

## Defaults

- Deck: `Serendipity`
- Word note type: `Vocabulary`
- Phrase note type: `Phrase`
- AnkiConnect endpoint: `http://127.0.0.1:8765`, API `version: 6`
- Chrome source helper: `scripts/chrome_source.py`

Use `Vocabulary` for a single lexical word or inflected word. Use `Phrase` for
multi-word expressions, idioms, collocations, named procedures, and chunks that
should be recalled as a unit. If the entry is ambiguous, infer from the entry
shape and say which model you chose.

## Workflow

1. Collect the entry and example sentence.
   - If either is missing, ask for the missing part unless the user clearly wants
     you to invent a natural example.
   - Preserve the user's original English sentence unless it contains an obvious
     typo that should be called out separately.
2. Generate the learning fields.
   - `definition`: concise natural Chinese answer to "how would I express this?"
   - `sentence`: the English example sentence.
   - `translation`: natural Chinese translation of the whole example sentence.
   - `source`: prefer the current Chrome tab as a Markdown link.
   - `note`, `synonym`, `antonym`, `mnemonic`, `definition_en`: fill only when
     useful for recall or disambiguation.
3. Preview the note before writing.
   - Show model, deck, tags, and non-empty fields.
   - Do not hide uncertainty; mark weak definitions as drafts.
4. Write to Anki only when the user explicitly asks to add/save/write the card.
   - Run `canAddNotes` with the exact payload first.
   - Then run `addNote`.
   - Verify with `notesInfo` on the returned note id.

## Field Mapping

For `Vocabulary`, include:

```json
{
  "uuid": "<new uuid4>",
  "entry": "<word>",
  "pos": "<part of speech when clear>",
  "definition": "<natural Chinese definition>",
  "sentence": "<English example>",
  "translation": "<Chinese sentence translation>",
  "source": "<Markdown source link>"
}
```

`uuid` is required for `Vocabulary` because it is the first field in the user's
model. Generate a fresh UUID for every new vocabulary note.

For `Phrase`, include:

```json
{
  "entry": "<phrase>",
  "definition": "<natural Chinese definition>",
  "sentence": "<English example>",
  "translation": "<Chinese sentence translation>",
  "source": "<Markdown source link>"
}
```

Leave `audio`, `image`, and `obsidian` empty unless the user provides those
assets or asks for them. Use tags sparingly: keep user-provided tags, and add at
most two obvious semantic tags when they help later retrieval.

## Chrome Source

When the user wants the current page as the card source, run:

```bash
python3 skills/anki-vocab-cards/scripts/chrome_source.py
```

The helper returns JSON:

```json
{"title": "...", "url": "...", "clean_title": "...", "markdown": "[...](...)"}
```

If Chrome or AppleScript access fails, continue with the card preview and leave
`source` empty or ask the user for the source. Do not block the vocabulary work
on source capture.

## AnkiConnect Calls

Probe first:

```json
{"action":"version","version":6}
```

Before writing, use `canAddNotes`:

```json
{
  "action": "canAddNotes",
  "version": 6,
  "params": {
    "notes": [
      {
        "deckName": "Serendipity",
        "modelName": "Vocabulary",
        "fields": {
          "uuid": "<new uuid4>",
          "entry": "...",
          "definition": "...",
          "sentence": "...",
          "translation": "...",
          "source": "..."
        },
        "tags": [],
        "options": {"allowDuplicate": false}
      }
    ]
  }
}
```

Then write with `addNote`, and verify:

```json
{"action":"notesInfo","version":6,"params":{"notes":[1234567890]}}
```

If deck/model/field errors occur, re-query `deckNames`, `modelNames`, and
`modelFieldNames`; names are exact and case-sensitive.

## Quality Bar

- Prefer active-writing usefulness over dictionary completeness.
- Make the Chinese definition short enough to be recalled quickly.
- Translate the example sentence naturally, not word by word.
- Keep `source` clean: remove browser/title noise and site suffixes where the
  remaining title still identifies the source.
- Avoid adding cards for vague entries. Ask for the intended meaning when one
  spelling has multiple common senses.
