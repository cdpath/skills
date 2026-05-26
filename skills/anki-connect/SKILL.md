---
name: anki-connect
description: Use AnkiConnect to inspect, create, update, or automate Anki data through the local HTTP API. Trigger when the user asks to interact with Anki, cards, notes, decks, models, media, reviews, or Anki search via AnkiConnect, localhost:8765, or the Anki-Connect add-on; includes safety rules for mutating and destructive actions.
---

# AnkiConnect

Use AnkiConnect as a local JSON-over-HTTP API for Anki. Assume the user has Anki open with the Anki-Connect add-on installed unless they ask for setup help.

## Connection

Default endpoint: `http://127.0.0.1:8765`

Every modern request should include `version: 6` and receive:

```json
{"result": "...", "error": null}
```

If `error` is non-null, treat the action as failed even when HTTP returned 200. If the user configured an API key in AnkiConnect, include `"key": "<api-key>"` at the top level. Never print or persist the key.

Probe before doing useful work:

```bash
curl -sS http://127.0.0.1:8765 -X POST \
  -H 'Content-Type: application/json' \
  -d '{"action":"version","version":6}'
```

For browser-extension or permission-sensitive clients, call `requestPermission`; it reports whether an API key is required and what AnkiConnect version is available.

## Invocation Pattern

Prefer small explicit requests. Inspect first, then mutate only after the target IDs/names are known.

```bash
curl -sS http://127.0.0.1:8765 -X POST \
  -H 'Content-Type: application/json' \
  -d '{"action":"deckNames","version":6}'
```

Minimal Python helper:

```python
import json
import urllib.request

def invoke(action, params=None, key=None):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    if key:
        payload["key"] = key
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8765", data=data)
    resp = json.load(urllib.request.urlopen(req))
    if resp.get("error") is not None:
        raise RuntimeError(resp["error"])
    return resp.get("result")
```

## Read-First Workflow

1. Confirm AnkiConnect is reachable with `version` or `deckNames`.
2. Discover deck/model/field names before creating data:
   - Decks: `deckNames`, `deckNamesAndIds`, `getDecks`
   - Models: `modelNames`, `modelFieldNames`, `modelFieldsOnTemplates`, `modelTemplates`
   - Notes/cards: `findNotes`, `notesInfo`, `findCards`, `cardsInfo`, `cardsToNotes`
3. Use Anki search strings exactly as Anki expects them, e.g. `"deck:Default tag:todo"`.
4. For bulk work, first run a read-only search and show/count the matched IDs. Only then execute the write.
5. After a write, verify with a read action such as `notesInfo`, `cardsInfo`, `deckNames`, or `findNotes`.

## Common Tasks

Read decks and models:

```json
{"action":"deckNames","version":6}
{"action":"modelNames","version":6}
{"action":"modelFieldNames","version":6,"params":{"modelName":"Basic"}}
```

Find and inspect notes:

```json
{"action":"findNotes","version":6,"params":{"query":"deck:Default tag:example"}}
{"action":"notesInfo","version":6,"params":{"notes":[1234567890]}}
```

Create one note:

```json
{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Default",
      "modelName": "Basic",
      "fields": {"Front": "Question", "Back": "Answer"},
      "tags": ["codex"],
      "options": {"allowDuplicate": false},
      "audio": [],
      "picture": []
    }
  }
}
```

Before bulk creation, use `canAddNotes` with the exact notes payload. Then call `addNotes` only for notes that can be added, and verify the returned note IDs.

Media:

- `storeMediaFile` stores a media file from `data`, `path`, or `url`. Existing files with the same name are deleted/replaced by default; set `deleteExisting: false` unless replacement is intentional.
- `retrieveMediaFile`, `getMediaFilesNames`, and `getMediaDirPath` are read-oriented.
- `deleteMediaFile` is destructive.

GUI actions:

- Use `guiBrowse`, `guiEditNote`, `guiSelectedNotes`, and `guiCurrentCard` when the user wants Anki's visible UI involved.
- `guiImportFile` opens Anki's import dialog for user review.
- `guiAnswerCard`, `guiUndo`, `guiExitAnki`, and review navigation change UI/session state; do not call them during ordinary data inspection.

Batching:

- `multi` runs actions in order and returns per-action results.
- Do not hide destructive actions inside `multi`; list them explicitly in the user-facing warning first.
- For mixed read/write batches, split into separate read and write calls when possible.

## Mutating Action Warnings

Treat these as mutating. Confirm intent and show the target count/name before running when operating on existing user data:

- Card scheduling/state: `suspend`, `unsuspend`, `forgetCards`, `relearnCards`, `answerCards`, `setDueDate`, `setEaseFactors`, `setSpecificValueOfCard`
- Deck changes: `createDeck`, `changeDeck`, `saveDeckConfig`, `setDeckConfigId`, `cloneDeckConfigId`, `removeDeckConfigId`
- Note/model changes: `addNote`, `addNotes`, `updateNoteFields`, `updateNoteModel`, `updateNoteTags`, `addTags`, `removeTags`, model template/style/field update actions
- Media writes: `storeMediaFile`
- Collection/package changes: `sync`, `importPackage`, `reloadCollection`, `insertReviews`
- GUI state changes: `guiAddCards`, `guiAddNoteSetData`, `guiEditNote`, `guiAnswerCard`, `guiUndo`, `guiExitAnki`, `guiImportFile`

For `setSpecificValueOfCard`, upstream documentation warns that changing some card database values can damage the collection; require explicit user confirmation and preserve the required `warning_check: true` only when the user understands the risk.

## Destructive Actions

Warning: these can delete or overwrite user data. Do not run them unless the user explicitly asks for the destructive operation and the exact target has been checked with a read-only call immediately beforehand.

- `deleteDecks`: deletes decks; `cardsToo` must be specified. Confirm deck names and whether cards should be deleted.
- `deleteNotes`: deletes notes and their cards. Confirm note IDs/count from `findNotes` or `notesInfo`.
- `removeEmptyNotes`: deletes all empty notes for the current user. Confirm the user wants a global cleanup.
- `deleteMediaFile`: deletes a file from Anki media. Confirm the filename from `getMediaFilesNames`.
- `storeMediaFile` with existing filename and default replacement: overwrites/deletes the previous media file. Use `deleteExisting: false` by default.
- `removeDeckConfigId`: removes a deck configuration group. Confirm the config ID is not default and is intended.
- `importPackage`: may merge/overwrite imported content in the collection. Prefer `guiImportFile` when the user should review.
- `insertReviews`: writes directly into review history. Treat as database-level modification.

When warning the user, be concrete: name the action, the matched count, the exact deck/note/card/media IDs or names, and the verification command used to identify them.

## Failure Handling

- If connection is refused, ask the user to open Anki and confirm the Anki-Connect add-on is installed and enabled.
- If a request returns only a raw value instead of `{"result","error"}`, the caller may have omitted `version` and fallen back to old API behavior. Retry with `version: 6`.
- If network access is needed beyond localhost, AnkiConnect must be configured with a different `webBindAddress`; warn that exposing it beyond localhost should use an API key and trusted network only.
- If names fail unexpectedly, re-query `deckNames`, `modelNames`, and field names; Anki model and field names are exact and case-sensitive.
