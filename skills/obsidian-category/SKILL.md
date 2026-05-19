---
name: obsidian-category
description: Use this skill when the user wants to create a new category in their Obsidian vault (ankiv3)
---

# Obsidian Category Creator

This skill helps create new categories in the Obsidian vault at `/Users/liujingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/`.

## What is a Category?

A category in this vault consists of two files:
1. **Category file** (`categories/{Name}.md`) - A markdown file with metadata linking to the base
2. **Base file** (`templates/bases/{Name}.base`) - Defines filters for the category view

## How to Create a New Category

这个 skill **不依赖脚本**，直接创建两个文件即可。

Vault 路径：`/Users/liujingyi/Library/Mobile Documents/iCloud~md~obsidian/Documents/ankiv3/`

在以下两个位置分别创建同名文件（用 `Memory` 举例）：

1. `categories/Memory.md`
2. `templates/bases/Memory.base`

文件内容见下方模板。

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

创建 "Machine Learning" category：

在 `categories/Machine Learning.md` 写入：
```markdown
---
tags: categories
---
![[Machine Learning.base]]
```

在 `templates/bases/Machine Learning.base` 写入：
```yaml
filters:
  and:
    - category.contains(link("Machine Learning"))
    - '!file.name.contains("Template")'
views:
  - type: table
    name: Table
```

## Notes

- Category names can contain spaces
- 创建前检查同名文件是否已存在（避免覆盖）
