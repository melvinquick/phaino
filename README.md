<p align="center">
  <img src="https://raw.githubusercontent.com/melvinquick/phaino/main/src/phaino/resources/images/phaino_bg_256.png" alt="Phaino Logo" />
</p>

<div align="center">
  <a href="https://github.com/melvinquick/phaino#about">About</a> | 
  <a href="https://github.com/melvinquick/phaino#purpose">Purpose</a> | 
  <a href="https://github.com/melvinquick/phaino#installation">Installation</a> | 
  <a href="https://github.com/melvinquick/phaino#useful-information">Useful Information</a>
</div>

<br>

<p align="center"><a href="https://pypi.org/project/phaino/"><img src="https://img.shields.io/pypi/v/phaino?style=for-the-badge&labelColor=F85149&color=F85149&logo=pypi&logoColor=FFFFFF&label=PyPI" alt="PyPI Version"></a>&nbsp;&nbsp;<a href="https://alternativeto.net/software/phaino/about/"><img src="https://img.shields.io/badge/AlternativeTo-58A6FF?style=for-the-badge&labelColor=58A6FF&logo=alternativeto&logoColor=FFFFFF&color=58A6FF" alt="AlternativeTo"></a>&nbsp;&nbsp;<a href="https://github.com/melvinquick/phaino"><img src="https://img.shields.io/badge/GitHub-21262D?style=for-the-badge&labelColor=21262D&logo=github&logoColor=FFFFFF&color=21262D" alt="GitHub"></a></p>

<p align="center"><a href="https://ko-fi.com/melvinquick"><img src="https://img.shields.io/badge/Ko--fi-FFA657?style=for-the-badge&labelColor=FFA657&logo=kofi&logoColor=FFFFFF&color=FFA657" alt="Ko-fi"></a>&nbsp;&nbsp;<a href="https://github.com/sponsors/melvinquick"><img src="https://img.shields.io/badge/GitHub%20Sponsors-D2A8FF?style=for-the-badge&labelColor=D2A8FF&logo=githubsponsors&logoColor=FFFFFF&color=D2A8FF" alt="GitHub Sponsors"></a></p>

<br>

## About

You may be wondering to yourself where the name **Phaino** comes from. Phaino is short for **Phainopepla**, which is a small black bird with a striking appearance. It doesn't super closely relate to the application itself other than the intent behind the app to be as small as possible given what I want it to do.

If you feel so inclined, you can see an image of a Phainopepla, as well as more information about the bird by looking [here](https://en.wikipedia.org/wiki/Phainopepla)!

## Purpose

Every time I've tried to find a "lightweight IDE" for myself (kind of thinking file editor with some extra features), I was never able to find one that worked for me. Phaino was born out of a desire to finally have that editor for myself.

### Features

✅ Search and replace across files with per-file review  
✅ Integrated "terminal" for running scripts  
✅ Basic Git integration with diff viewer  
✅ Project saving and session restore  
✅ Syntax highlighting for various languages  
✅ Formatting for various languages (see [Formatting](#formatting) below)  
✅ Multiple themes for accessibility  
✅ Quick Open (`Ctrl+P`) for fast file navigation  
✅ "Better Comments" highlighting for TODOs, alerts, and queries  
✅ External file change detection with reload prompt

## Installation

The installer sets up a dedicated venv and creates a desktop shortcut.

```
curl -s https://raw.githubusercontent.com/melvinquick/phaino/main/install.py | python3 -
```

### Supported Operating Systems

✅ Linux  
❌ Mac  
❌ Windows

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

### Terminal

Phaino includes a built-in "terminal" panel for viewing the output of scripts
you run from within the app. It is **not** a full terminal emulator. It
captures the output of the process Phaino launches and displays it, and it
relays standard input back to that process. Interactive shell sessions (like
`vim`, `htop`, or a raw `bash` prompt) are not supported inside this panel.

If you need a real terminal in your project, right-click any folder in the
Explorer and choose **Open in Terminal** to launch your system's default
terminal emulator in that directory.

### Formatting

Phaino uses external formatters and does not bundle them. Format on save is optional and can be toggled per language under **Preferences > Formatting**.

> I realize formatting/formatters are very opinionated, but these are what are on offer for Phaino right now. Installation is left to the user (Phaino only invokes formatters already on your `PATH`). If one isn't found, you'll get a one-time warning in the terminal panel.

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
