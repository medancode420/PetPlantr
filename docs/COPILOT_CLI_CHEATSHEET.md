# GitHub Copilot CLI Cheat Sheet

Quick reference for using Copilot in your terminal.

## Install / Update

- Install extension:
  gh extension install github/gh-copilot
- Update extension:
  gh extension upgrade github/gh-copilot
- Verify:
  gh extension list | grep gh-copilot

## Explain a command

- Explain what a command does:
  gh copilot explain "sudo apt-get"

## Suggest commands

- Shell one-liner suggestion:
  gh copilot suggest -t shell "find Python processes and show their CPU/mem"
- GitHub CLI flow suggestion:
  gh copilot suggest -t gh "create a PR from feature-x into main with title and body"

## Commit message + PR text

- Generate a commit message from staged changes:
  gh copilot suggest -t commit "concise, conventional commit for staged diff"
- Draft a PR title/body from local changes:
  gh copilot suggest -t pr "summarize changes for PR with highlights and risks"

Tips:
- Copilot CLI may ask to copy to clipboard or display multiple options; pick one and paste.
- Always review generated commands/messages before running or committing.

## VS Code Copilot quick setup

- Enable `code` CLI on macOS:
  1) In VS Code: Command Palette → Shell Command: Install 'code' command in PATH
  2) Or symlink:
     sudo ln -s "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" /usr/local/bin/code
- Install extensions:
  code --install-extension GitHub.copilot
  code --install-extension GitHub.copilot-chat
- Sign in (VS Code Accounts) and check Output → "GitHub Copilot" for errors.

## Troubleshooting

- If gh prompts for credentials repeatedly: gh auth status, then gh auth refresh -h github.com -s repo
- Network checks are OK if TLS to *.github.com/*.githubusercontent.com succeeds; 404 on /_ping is expected.
- To disable Copilot CLI telemetry prompts: export GH_COPILOT_TELEMETRY=0
