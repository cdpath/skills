---
name: obsidian-category
description: Use this skill when the user wants to create a new category in their Obsidian vault (ankiv3)
---

# Obsidian Category Creator

This skill helps create new categories in the Obsidian vault at `/Users/jingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/`.

## What is a Category?

A category in this vault consists of two files:
1. **Category file** (`categories/{Name}.md`) - A markdown file with metadata linking to the base
2. **Base file** (`templates/bases/{Name}.base`) - Defines filters for the category view

## How to Create a New Category

Run the Python script:

```bash
python ~/.claude/skills/obsidian-category/scripts/create_category.py "CategoryName"
```

Or with a custom vault path:

```bash
python ~/.claude/skills/obsidian-category/scripts/create_category.py "CategoryName" --vault /path/to/vault
```

## File Templates

### Category File (`categories/{Name}.md`)

```markdown
---
tags: categories
---
![[{Name}.base]]
```

### Base File (`templates/bases/{Name}.base`)

```yaml
filters:
  and:
    - category.contains(link("categories/{Name}"))
    - '!file.name.contains("Template")'
views:
  - type: table
    name: Table
```

## Examples

Create a "Machine Learning" category:
```bash
python ~/.claude/skills/obsidian-category/scripts/create_category.py "Machine Learning"
```

This creates:
- `/Users/jingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/categories/Machine Learning.md`
- `/Users/jingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/templates/bases/Machine Learning.base`

## Notes

- Category names can contain spaces
- The script will fail if the category already exists (to prevent overwriting)
- Default vault path: `/Users/jingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/`
