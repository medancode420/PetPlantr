## GitHub Copilot Chat

- Extension Version: 0.28.3 (prod)
- VS Code: vscode/1.103.0
- OS: Mac

## Network

User Settings:
```json
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to https://api.github.com:
- DNS ipv4 Lookup: 140.82.112.6 (13 ms)
- DNS ipv6 Lookup: ::ffff:140.82.112.6 (1 ms)
- Proxy URL: None (33 ms)
- Electron fetch (configured): HTTP 200 (82 ms)
- Node.js https: HTTP 200 (75 ms)
- Node.js fetch: HTTP 200 (74 ms)
- Helix fetch: HTTP 200 (140 ms)

Connecting to https://api.individual.githubcopilot.com/_ping:
- DNS ipv4 Lookup: 140.82.112.22 (16 ms)
- DNS ipv6 Lookup: ::ffff:140.82.112.22 (2 ms)
- Proxy URL: None (1 ms)
- Electron fetch (configured): HTTP 200 (20 ms)
- Node.js https: HTTP 200 (86 ms)
- Node.js fetch: HTTP 200 (77 ms)
- Helix fetch: HTTP 200 (84 ms)

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).