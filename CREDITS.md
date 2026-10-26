# Credits

PingPilot reimplements, in Python, a few tweaks and techniques that other open-source projects
documented first. **No script, executable or source file from these projects is shipped or run** by
PingPilot: the registry values and API calls were rewritten from scratch. Each tweak card in the app
shows where the idea came from (blue tag), and `pingpilot/tweaks.py` lists the source of every value.

| Project | Author | License | What PingPilot took from it |
|---|---|---|---|
| [WinUtil](https://github.com/ChrisTitusTech/winutil) | Chris Titus Tech | MIT | Game Mode, mouse acceleration, background apps, Delivery Optimization, prefer IPv4, Teredo, activity history, promoted apps, temp-file cleanup, restore point |
| [KOALA Gaming Optimizer](https://github.com/koalaaufpillen/koalaoptimizer) | koalaaufpillen | MIT (declared in its README) | Game DVR, MMCSS for games, SystemResponsiveness, Win32PrioritySeparation, High performance power plan, hardware GPU scheduling, Nagle (TcpAckFrequency / TCPNoDelay), NetworkThrottlingIndex |
| [WLANOptimizer](https://github.com/catid/WLANOptimizer) | Christopher A. Taylor | BSD-3-Clause | The technique of turning off Wi-Fi background scanning and turning on streaming mode (`WlanSetInterface`), rewritten with `ctypes` |
| HoneCTRL 2.7 | Auraside (Hone) | GNU AGPLv3 (as declared in that version) | The *ideas* behind network-card power saving, DNS failure cache, game QoS (DSCP 46) and standby-memory cleanup |

## Tweaks left out on purpose

Some tweaks from these projects are **not** included because the risk outweighs the benefit
(the full list with reasons is on the app's *About* page): disabling Spectre/Meltdown mitigations,
disabling display-driver recovery (TDR), disabling CPU C-states/core parking, changing the paging file,
disabling memory compression/Prefetch, disabling IPv6, disabling TCP autotuning/task offload,
forcing NewReno, forcing MSI mode, blocking Windows Update drivers / DDU, and removing Edge/OneDrive.

## A note about HoneCTRL

In January 2025 Auraside asked GitHub (DMCA) to take down a re-upload of HoneCTRL, saying it was the code
of their paid product. That is why PingPilot does not copy any HoneCTRL code or files, does not use the
Hone name or brand, and only keeps the general idea of each tweak (registry values and Windows settings are
technical facts, not creative code).

## License notices

WinUtil — MIT License, Copyright (c) 2022 CT Tech Group LLC.
KOALA Gaming Optimizer — MIT License (as declared by the project).

WLANOptimizer — BSD 3-Clause License:

```
Copyright (c) 2018 Christopher A. Taylor.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of WLAN Optimizer nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

Runtime libraries bundled in the Windows build: [pywebview](https://github.com/r0x0r/pywebview) (BSD-3-Clause),
[pystray](https://github.com/moses-palmer/pystray) (LGPL-3.0), [Pillow](https://github.com/python-pillow/Pillow) (MIT-CMU),
and the Python runtime via [PyInstaller](https://pyinstaller.org) (GPL with a bootloader exception that allows
bundling non-GPL apps).
