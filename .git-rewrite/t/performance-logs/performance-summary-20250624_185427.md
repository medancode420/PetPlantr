# PetPlantr System Performance Summary

**Monitoring Session:** 20250624_185427
**Duration:** Tue Jun 24 18:54:54 EDT 2025

## System Information
=== System Information ===
Date: Tue Jun 24 18:54:27 EDT 2025
OS: Darwin Daniels-MBP 24.6.0 Darwin Kernel Version 24.6.0: Wed Jun 11 21:22:41 PDT 2025; root:xnu-11417.140.62.501.1~2/RELEASE_ARM64_T6031 arm64

CPU Information:
Apple M3 Max
16

Memory Information:
Total Memory: 128 GB
Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                             4393232.
Pages active:                           1755651.
Pages inactive:                         1474925.
Pages speculative:                       321795.
Pages throttled:                              0.
Pages wired down:                        320233.
Pages purgeable:                         260924.
"Translation faults":                 394659244.
Pages copy-on-write:                   23322471.
Pages zero filled:                    211394397.
Pages reactivated:                       133199.
Pages purged:                            707654.
File-backed pages:                      1299001.
Anonymous pages:                        2253370.
Pages stored in compressor:                   0.
Pages occupied by compressor:                 0.
Decompressions:                               0.
Compressions:                                 0.
Pageins:                                8257682.
Pageouts:                                     0.
Swapins:                                      0.
Swapouts:                                     0.

## Monitoring Files Generated
- **CPU Monitor:** cpu-monitor-20250624_185427.log
- **Memory Monitor:** memory-monitor-20250624_185427.log
- **Process Monitor:** process-monitor-20250624_185427.log
- **Disk Monitor:** disk-monitor-20250624_185427.log
- **Network Monitor:** network-monitor-20250624_185427.log

## Quick Analysis

### CPU Usage Peaks
```

```

### Memory Usage Summary
```
Tue Jun 24 18:54:52 EDT 2025: Pages free:                             4371285.
Pages active:                           1790035.
Pages inactive:                         1481465.
Pages speculative:                       321564.
Pages wired down:                        301269.
```

### Active Processes
```
medan            55985   1.0  0.5 1868612832 682768   ??  S     6:30PM   0:16.23 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) --type=utility --utility-sub-type=node.mojom.NodeService --lang=en-US --service-sandbox-type=none --dns-result-order=ipv4first --experimental-network-inspection --inspect-port=0 --user-data-dir=/Users/medan/Library/Application Support/Code --standard-schemes=vscode-webview,vscode-file --enable-sandbox --secure-schemes=vscode-webview,vscode-file --cors-schemes=vscode-webview,vscode-file --fetch-schemes=vscode-webview,vscode-file --service-worker-schemes=vscode-webview --code-cache-schemes=vscode-webview,vscode-file --shared-files --field-trial-handle=1718379636,r,17594751671404466591,10743566637155694635,262144 --enable-features=DocumentPolicyIncludeJSCallStacksInCrashReports,EarlyEstablishGpuChannel,EstablishGpuChannelAsync,ScreenCaptureKitPickerScreen,ScreenCaptureKitStreamPickerSonoma --disable-features=CalculateNativeWinOcclusion,MacWebContentsOcclusion,SpareRendererForSitePerProcess,TimeoutHangingVideoCaptureStarts --variations-seed-version
medan            55934   0.0  0.2 1866895488 235712   ??  S     6:30PM   0:05.79 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper.app/Contents/MacOS/Code Helper --type=utility --utility-sub-type=node.mojom.NodeService --lang=en-US --service-sandbox-type=none --user-data-dir=/Users/medan/Library/Application Support/Code --standard-schemes=vscode-webview,vscode-file --enable-sandbox --secure-schemes=vscode-webview,vscode-file --cors-schemes=vscode-webview,vscode-file --fetch-schemes=vscode-webview,vscode-file --service-worker-schemes=vscode-webview --code-cache-schemes=vscode-webview,vscode-file --shared-files --field-trial-handle=1718379636,r,17594751671404466591,10743566637155694635,262144 --enable-features=DocumentPolicyIncludeJSCallStacksInCrashReports,EarlyEstablishGpuChannel,EstablishGpuChannelAsync,ScreenCaptureKitPickerScreen,ScreenCaptureKitStreamPickerSonoma --disable-features=CalculateNativeWinOcclusion,MacWebContentsOcclusion,SpareRendererForSitePerProcess,TimeoutHangingVideoCaptureStarts --variations-seed-version
medan            41924   0.0  0.1 412010176  69392   ??  S     6:01PM   0:00.37 /Users/medan/Downloads/PetPlantr/.venv/bin/python -m ipykernel_launcher --f=/Users/medan/Library/Jupyter/runtime/kernel-v3bd0a1439550c05205da3a8d74651820c8bada2a5.json
medan            10288   0.0  0.1 412142272  69760   ??  S     5:10PM   0:00.41 /Users/medan/Downloads/PetPlantr/.venv/bin/python -m ipykernel_launcher --f=/Users/medan/Library/Jupyter/runtime/kernel-v32bc38fd392de41f0ff31b382592f3ba7a1dca6c8.json
medan            86126   0.0  0.1 412281536  69696   ??  S     4:58PM   0:00.50 /Users/medan/Downloads/PetPlantr/.venv/bin/python -m ipykernel_launcher --f=/Users/medan/Library/Jupyter/runtime/kernel-v330ca7eeed8418221e650d517c1cae2c37242c2ae.json
medan            50840   0.0  0.1 412541632  70080   ??  S    12:13PM   0:00.88 /Users/medan/Downloads/PetPlantr/.venv/bin/python -m ipykernel_launcher --f=/Users/medan/Library/Jupyter/runtime/kernel-v3ca62db3f7da608eaf644333e5e90e143c1448681.json
medan            60702   0.0  0.1 1865154240  88560   ??  S     6:52PM   0:00.13 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Applications/Visual Studio Code.app/Contents/Resources/app/extensions/markdown-language-features/dist/serverWorkerMain --node-ipc --clientProcessId=56333
medan            57537   0.0  0.1 1865137088  91280   ??  S     6:39PM   0:00.18 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Applications/Visual Studio Code.app/Contents/Resources/app/extensions/markdown-language-features/dist/serverWorkerMain --node-ipc --clientProcessId=57147
medan            57520   0.0  0.1 1865135808  82304   ??  S     6:39PM   0:00.15 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Applications/Visual Studio Code.app/Contents/Resources/app/extensions/json-language-features/server/dist/node/jsonServerMain --node-ipc --clientProcessId=56333
medan            57148   0.0  0.1 1865135808  89392   ??  S     6:38PM   0:00.18 /Applications/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Applications/Visual Studio Code.app/Contents/Resources/app/extensions/json-language-features/server/dist/node/jsonServerMain --node-ipc --clientProcessId=57147
```

## Recommendations
- Review log files for detailed performance analysis
- Check for memory leaks in high-usage processes
- Monitor CPU spikes during build/compilation phases
- Optimize processes showing consistently high resource usage

