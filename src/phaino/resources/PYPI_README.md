<div align="center">
  <a href="#donations">Donations</a> | 
  <a href="#about">About</a> | 
  <a href="#purpose">Purpose</a> | 
  <a href="#installation">Installation</a> | 
  <a href="#useful-information">Useful Information</a>
</div>

## Donations

[Ko-fi](https://ko-fi.com/melvinquick)  
[GitHub Sponsors](https://github.com/sponsors/melvinquick)

## About

You may be wondering to yourself where the name **Phaino** comes from. Phaino is short for **Phainopepla**, which is a small black bird with a striking appearance. It doesn't super closely relate to the application itself other than the intent behind the app to be as small as possible given what I want it to do.

If you feel so inclined, you can see an image of a Phainopepla, as well as more information about the bird by looking [here](https://en.wikipedia.org/wiki/Phainopepla)!

## Purpose

Every time I've tried to find a "lightweight IDE" for myself (kind of thinking file editor with some extra features), I was never able to find one that worked for me. Phaino was born out of a desire to finally have that editor for myself.

### Features

:white_check_mark: Keyboard driven file tree viewer  
:white_check_mark: Basic Git integration / source control  
:white_check_mark: Project saving  
:white_check_mark: Session restore  
:white_check_mark: Multiple themes for "all" people

## Installation

The installer sets up a dedicated venv and creates a desktop shortcut.

```
curl -s https://raw.githubusercontent.com/melvinquick/phaino/main/install.py | python3 -
```

### Supported Operating Systems

:white_check_mark: Linux  
:x: Mac  
:x: Windows

## Useful Information

[Project](https://github.com/users/melvinquick/projects/19)  
[Latest Release](https://pypi.org/project/phaino/)

### Running Scripts

Phaino runs files directly by executing them. For this to work, your script must have a **shebang line** at the top of the file and must be **executable** on your system.

For example, in a Python file:

```python
#!/usr/bin/env python3
print("Hello, Phaino!")
```

Then mark the file as executable:

```bash
chmod +x script.py
```

### Formatting

Phaino uses external formatters and does not bundle them. Format on save is optional and can be toggled per language under **Settings → Formatting**.

> I realize formatting/formatters are very opinionated, but these are what are on offer for Phaino right now. Installation is left to the user — Phaino only invokes formatters already on your `PATH`. If one isn't found, you'll get a one-time warning in the terminal panel.

| Language   | Extension       | Formatter |
| ---------- | --------------- | --------- |
| Python     | `.py`           | Ruff      |
| TOML       | `.toml`         | Taplo     |
| JSON       | `.json`         | Prettier  |
| YAML       | `.yaml`, `.yml` | Prettier  |
| Markdown   | `.md`           | Prettier  |
| HTML       | `.html`, `.htm` | Prettier  |
| JavaScript | `.js`           | Prettier  |
| TypeScript | `.ts`           | Prettier  |
| Rust       | `.rs`           | rustfmt   |
| Go         | `.go`           | gofmt     |
