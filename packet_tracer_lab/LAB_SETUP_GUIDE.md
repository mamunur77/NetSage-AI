# Packet Tracer Lab Setup Guide
## NetSage AI — Demo Lab with 5 Deliberate Bugs

This guide walks you through building a Packet Tracer lab that contains
**5 real network faults** from the project's case database. You will then
use NetSage AI's scripts to diagnose them.

---

## Topology Diagram

```
                    ┌──────────────┐
                    │     R1       │
                    │  (Router)    │
                    │              │
                    │  G0/0 ──────┤── Trunk (dot1Q)
                    └──────┬───────┘
                           │ Gi0/1 (trunk)
                    ┌──────┴───────┐
                    │     SW1      │
                    │  (Switch)    │
                    │              │
          ┌─────────┼──────────────┼─────────────┐
          │         │              │              │
     Fa0/2-5    Fa0/6-10      Fa0/11-15      Fa0/16
     VLAN 10    VLAN 20       VLAN 30        VLAN 1 ← BUG
     (Sales)    (Engineering) (Guest)        (should be 20)
          │         │              │              │
        PC-A      PC-B          PC-C           PC-D
```

---

## Step-by-Step Build in Packet Tracer

### 1. Place the Devices
1. Open Cisco Packet Tracer.
2. Drag and drop:
   - **1x Router** (2911 or 1941) — name it `R1`
   - **1x Switch** (2960) — name it `SW1`
   - **4x PCs** — name them `PC-A`, `PC-B`, `PC-C`, `PC-D`

### 2. Cable the Devices
| From | Interface | To | Interface | Cable |
|---|---|---|---|---|
| R1 | G0/0 | SW1 | Gi0/1 | Straight-through |
| SW1 | Fa0/2 | PC-A | Fa0 | Straight-through |
| SW1 | Fa0/6 | PC-B | Fa0 | Straight-through |
| SW1 | Fa0/11 | PC-C | Fa0 | Straight-through |
| SW1 | Fa0/16 | PC-D | Fa0 | Straight-through |

### 3. Configure SW1
1. Click on **SW1** → CLI tab.
2. Copy-paste everything from `SW1_Config.txt` into the CLI.

### 4. Configure R1
1. Click on **R1** → CLI tab.
2. Copy-paste everything from `R1_Config_Broken.txt` into the CLI.

### 5. Configure PCs
All PCs should be set to **DHCP** (automatic IP):
1. Click on each PC → Desktop → IP Configuration.
2. Select **DHCP**.

**EXCEPT for PC-A** (to demonstrate Bug 5 — the gateway mismatch):
- PC-A: Set to **Static**
  - IP: `192.168.10.50`
  - Subnet Mask: `255.255.255.0`
  - Default Gateway: `192.168.10.1`

---

## The 5 Embedded Bugs

| Bug # | Case | Device | What's Wrong | How to Observe |
|---|---|---|---|---|
| 1 | C006 | R1 | G0/0.40 is `shutdown` | PC in VLAN 40 can't ping 192.168.40.1 |
| 2 | C010 | R1 | DHCP pool ENG uses /25 instead of /24 | PC-B gets wrong subnet mask (255.255.255.128) |
| 3 | C013 | R1 | DNS server set to 172.16.1.99 (wrong) | PC-C can't resolve domain names |
| 4 | C002 | SW1 | Fa0/16 left in VLAN 1 (should be 20) | PC-D can't get IP / can't reach gateway |
| 5 | C001 | SW1 | VLAN 10 NOT in trunk allowed list | PC-A can ping locally but not across switch |

---

## Demo Workflow (for your video)

### Phase 1: Show the Problem (1–2 min)
1. Open Packet Tracer and show the topology.
2. Try pinging from PC-A → R1 gateway (192.168.10.1) — **FAILS** (Bug 5).
3. Check PC-B's IP config → shows wrong mask (Bug 2).
4. Show PC-D has no IP or wrong IP (Bug 4).

### Phase 2: Gather Evidence (1 min)
Run these commands in Packet Tracer CLI and copy the output:

**On R1:**
```ios
show ip interface brief
show ip dhcp pool
show run | section dhcp
```

**On SW1:**
```ios
show vlan brief
show interfaces trunk
show interfaces fa0/16 switchport
```

### Phase 3: Run NetSage AI (2 min)
Open your terminal and run:
```bash
python scripts/rule_checker.py
python scripts/ai_diagnose.py
```
Show the terminal output — the AI identifies each bug with root cause,
evidence, confidence, and fix steps.

### Phase 4: Apply the Fixes (2 min)
Go back to Packet Tracer CLI and apply the fixes suggested by the AI:

**Fix Bug 1 (C006) — Enable VLAN 40 gateway:**
```ios
R1(config)# interface g0/0.40
R1(config-subif)# no shutdown
```

**Fix Bug 2 (C010) — Correct DHCP mask:**
```ios
R1(config)# no ip dhcp pool ENGINEERING
R1(config)# ip dhcp pool ENGINEERING
R1(dhcp-config)# network 192.168.20.0 255.255.255.0
R1(dhcp-config)# default-router 192.168.20.1
R1(dhcp-config)# dns-server 8.8.8.8
```

**Fix Bug 3 (C013) — Correct DNS server:**
```ios
R1(config)# no ip dhcp pool GUEST
R1(config)# ip dhcp pool GUEST
R1(dhcp-config)# network 192.168.30.0 255.255.255.0
R1(dhcp-config)# default-router 192.168.30.1
R1(dhcp-config)# dns-server 8.8.8.8
```

**Fix Bug 4 (C002) — Move port to correct VLAN:**
```ios
SW1(config)# interface fa0/16
SW1(config-if)# switchport access vlan 20
```

**Fix Bug 5 (C001) — Add VLAN 10 to trunk:**
```ios
SW1(config)# interface gi0/1
SW1(config-if)# switchport trunk allowed vlan add 10
```

### Phase 5: Verify (1 min)
1. Renew DHCP on all PCs (disconnect/reconnect cable in Packet Tracer).
2. Ping from PC-A → 192.168.10.1 → **SUCCESS** ✅
3. Check PC-B IP → 255.255.255.0 → **CORRECT** ✅
4. Check PC-D IP → 192.168.20.x → **CORRECT** ✅

### Phase 6: Show the Dashboard (30 sec)
```bash
python scripts/build_dashboard.py
```
Open `outputs/dashboard.xlsx` and show the charts.

---

## Files in this Folder

| File | Purpose |
|---|---|
| `SW1_Config.txt` | Switch config with 2 bugs (paste into SW1 CLI) |
| `R1_Config_Broken.txt` | Router config with 3 bugs (paste into R1 CLI) |
| `R1_Config_Working.txt` | Clean router config (no bugs, for reference) |
| `LAB_SETUP_GUIDE.md` | This file |
