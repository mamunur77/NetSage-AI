#!/usr/bin/env python3
"""
Generates data/cases.csv for NetSage AI.
Columns: case_id, category, symptom, topology_note, show_output,
         expected_fault, osi_layer, concept_tag, severity

Usage:
    python scripts/generate_cases.py
"""
import csv
from pathlib import Path

ROOT      = Path(__file__).parent.parent
OUTPUT    = ROOT / "data" / "cases.csv"

cases = []

def add(cid, category, symptom, topo, show, fault, osi, concept, severity):
    cases.append({
        "case_id": cid,
        "category": category,
        "symptom": symptom,
        "topology_note": topo,
        "show_output": show.strip("\n"),
        "expected_fault": fault,
        "osi_layer": osi,
        "concept_tag": concept,
        "severity": severity,
    })

# ---------------- VLAN (4) ----------------
add("C001", "VLAN", "PC in VLAN 10 cannot reach PC in VLAN 10 on the next switch; both are in the same subnet.",
    "SW1 access port Fa0/1 (VLAN10) -- trunk Gi0/1 -- SW2 trunk Gi0/1 -- SW2 access port Fa0/2 (VLAN10)",
    """
SW1# show interfaces trunk
Port      Mode    Encapsulation  Status        Native vlan
Gi0/1     on      802.1q         trunking      1
Port      Vlans allowed on trunk
Gi0/1     1-9,11-4094

SW1# show vlan brief
VLAN Name       Status    Ports
10   Sales      active    Fa0/1
""",
    "VLAN 10 is missing from the allowed-vlan list on the SW1 trunk (Gi0/1 allows 1-9,11-4094, excluding 10), so VLAN 10 traffic is dropped at the trunk.",
    "Layer 2", "vlan-trunk-pruning", "High")

add("C002", "VLAN", "New PC plugged into Fa0/3 on SW1 gets no response from DHCP server and cannot ping anything, including its own gateway.",
    "SW1 Fa0/3 should be an access port in VLAN 20 (Engineering); DHCP server is on VLAN 20 subnet reachable via SW1 uplink.",
    """
SW1# show interfaces fa0/3 switchport
Name: Fa0/3
Administrative Mode: dynamic auto
Operational Mode: static access
Access Mode VLAN: 1 (default)
Voice VLAN: none

SW1# show vlan brief
VLAN Name        Status    Ports
1    default      active    Fa0/3
20   Engineering  active    Fa0/4, Fa0/5
""",
    "Fa0/3 was never assigned to VLAN 20; it is still sitting in the default VLAN 1, so the PC is on the wrong broadcast domain and cannot reach the VLAN 20 DHCP scope or gateway.",
    "Layer 2", "vlan-access-port-assignment", "High")

add("C003", "VLAN", "Phones and PCs on the same switch intermittently lose connectivity to the file server; packet captures show occasional untagged frames arriving on the wrong VLAN.",
    "SW1 trunk to core: Gi0/1. Voice VLAN 15, Data VLAN 10.",
    """
SW1# show interfaces gi0/1 trunk
Port     Mode  Native vlan  Status
Gi0/1    on    15           trunking

Core# show interfaces gi0/3 trunk
Port     Mode  Native vlan  Status
Gi0/3    on    1            trunking
""",
    "Native VLAN mismatch on the trunk: SW1 uses native VLAN 15 while the core switch uses native VLAN 1, causing VLAN leaking/tag corruption for untagged frames.",
    "Layer 2", "native-vlan-mismatch", "Medium")

add("C004", "VLAN", "A PC moved from the Sales VLAN to the Guest VLAN still shows up with a Sales-subnet IP address after reboot.",
    "SW1 Fa0/8 reassigned from VLAN 10 (Sales) to VLAN 30 (Guest) in the running config.",
    """
SW1# show run interface fa0/8
interface FastEthernet0/8
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast

SW1# show vlan brief
30   Guest   active   Fa0/8

PC> ipconfig
IP Address: 192.168.10.55
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.10.1
""",
    "The port is correctly in VLAN 30, but the PC never released/renewed its old VLAN 10 (192.168.10.x) DHCP lease, so a stale lease is the likely cause rather than a switchport misconfig -- confirm with 'ipconfig /release && ipconfig /renew' before assuming a VLAN fault.",
    "Layer 2/3", "vlan-stale-dhcp-lease", "Low")

# ---------------- Gateway (4) ----------------
add("C005", "Gateway", "PC has a valid IP in the correct subnet but cannot ping anything outside its own subnet, including the gateway.",
    "PC 192.168.1.50/24, Router G0/0 configured as gateway.",
    """
PC> ipconfig
IP Address: 192.168.1.50
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.1.254

R1# show ip interface brief
Interface   IP-Address     Status   Protocol
G0/0        192.168.1.1    up       up
""",
    "Default gateway configured on the PC (192.168.1.254) does not match the router's actual interface IP (192.168.1.1); the PC is pointing at a nonexistent gateway.",
    "Layer 3", "gateway-mismatch", "High")

add("C006", "Gateway", "All PCs on VLAN 40 lost internet access at the same time; local VLAN 40 traffic still works fine.",
    "R1 has a router-on-a-stick subinterface G0/1.40 acting as the gateway for VLAN 40.",
    """
R1# show ip interface brief
Interface        IP-Address      Status                  Protocol
GigabitEthernet0/1.40   192.168.40.1   administratively down   down

R1# show run interface g0/1.40
interface GigabitEthernet0/1.40
 encapsulation dot1Q 40
 ip address 192.168.40.1 255.255.255.0
 shutdown
""",
    "Subinterface G0/1.40, which acts as the VLAN 40 gateway, is administratively shut down.",
    "Layer 3", "gateway-interface-down", "Critical")

add("C007", "Gateway", "Two PCs on the same subnet can reach each other but only one of them can reach the internet.",
    "192.168.5.0/24 subnet; expected gateway 192.168.5.1 on R1 G0/0.",
    """
PC-A> ipconfig
Default Gateway: 192.168.5.1

PC-B> ipconfig
Default Gateway: 192.168.5.2

R1# show ip interface brief
G0/0    192.168.5.1   up   up
""",
    "PC-B has the wrong default gateway (192.168.5.2) manually configured; 192.168.5.1 is the real router interface, so PC-B's traffic to other subnets has nowhere to go.",
    "Layer 3", "gateway-misconfig-endpoint", "Medium")

add("C008", "Gateway", "After a switch replacement, an entire VLAN lost gateway reachability even though the router config was untouched.",
    "R1 G0/0 (gateway 10.0.0.1) connects to SW1 Fa0/1 access port in VLAN 5; new switch's Fa0/1 was accidentally left in VLAN 1.",
    """
SW1# show interfaces fa0/1 switchport
Access Mode VLAN: 1 (default)

R1# show ip interface brief
G0/0   10.0.0.1   up   up
""",
    "The router interface itself is fine, but the switch port connecting the router to VLAN 5 was provisioned in VLAN 1 on the replacement switch, isolating the gateway from the rest of VLAN 5 -- a VLAN issue masquerading as a gateway issue.",
    "Layer 2/3", "gateway-unreachable-vlan-port", "High")

# ---------------- DHCP (4) ----------------
add("C009", "DHCP", "New devices stop receiving IP addresses during busy hours; existing leases still work.",
    "DHCP pool 'SALES' serves 192.168.10.0/24.",
    """
R1# show ip dhcp pool SALES
Pool SALES :
 Utilization mark (high/low) : 100 / 0
 Total addresses              : 254
 Leased addresses             : 254
 Excluded addresses           : 10
 Pending event                : none
""",
    "DHCP pool SALES is fully exhausted (254 leased of 254 total addresses), so new clients cannot obtain a lease.",
    "Layer 3/7", "dhcp-pool-exhaustion", "High")

add("C010", "DHCP", "New PCs get an IP address but it does not match the rest of the subnet and they cannot communicate with anyone.",
    "DHCP pool should hand out 192.168.20.0/24.",
    """
R1# show run | section dhcp pool ENG
ip dhcp pool ENG
 network 192.168.20.0 255.255.255.128
 default-router 192.168.20.1
 dns-server 8.8.8.8

PC> ipconfig
IP Address: 192.168.20.130
Subnet Mask: 255.255.255.128
""",
    "The DHCP pool is configured with a /25 mask (255.255.255.128) instead of the intended /24, so some clients receive addresses in the second /25 half (192.168.20.130) that cannot reach hosts or the gateway in the first half.",
    "Layer 3", "dhcp-wrong-subnet-mask", "Medium")

add("C011", "DHCP", "PCs on a remote VLAN reachable only through the router never receive an IP address from the central DHCP server; local VLAN clients are fine.",
    "DHCP server lives on VLAN 1; remote clients are on VLAN 50 across R1, different broadcast domain.",
    """
R1# show run interface vlan50
interface Vlan50
 ip address 192.168.50.1 255.255.255.0
 (no ip helper-address configured)

R1# show ip dhcp binding
(only VLAN 1 addresses listed)
""",
    "No 'ip helper-address' is configured on the VLAN 50 interface, so DHCP broadcasts from that subnet are never relayed to the central DHCP server across the router boundary.",
    "Layer 3", "dhcp-relay-missing", "High")

add("C012", "DHCP", "A handful of specific addresses that should be reserved for printers keep getting handed out to laptops.",
    "Printers are statically expected to use 192.168.30.240-192.168.30.250.",
    """
R1# show run | section dhcp
ip dhcp excluded-address 192.168.30.1 192.168.30.10
ip dhcp pool PRINTERS
 network 192.168.30.0 255.255.255.0
 default-router 192.168.30.1
""",
    "The excluded-address range only covers 192.168.30.1-10; the printer range 192.168.30.240-250 was never excluded, so the DHCP pool is free to lease those addresses to any client.",
    "Layer 3", "dhcp-excluded-range-incomplete", "Low")

# ---------------- DNS (4) ----------------
add("C013", "DNS", "Users can ping IP addresses on the internet but cannot browse to any website by name.",
    "PCs on 172.16.1.0/24, expected DNS server 172.16.1.5 (internal) or 8.8.8.8 (external).",
    """
PC> ipconfig /all
IPv4 Address: 172.16.1.50
Default Gateway: 172.16.1.1
DNS Servers: 172.16.1.99

PC> ping 172.16.1.99
Request timed out.
""",
    "The configured DNS server (172.16.1.99) does not respond to ping/queries -- it is either the wrong address or the DNS service is down; name resolution fails while IP connectivity works fine (classic Layer 7 symptom on top of working Layer 3).",
    "Layer 7", "dns-server-unreachable", "Medium")

add("C014", "DNS", "One department can resolve internal hostnames but gets 'server not found' for external websites.",
    "Internal DNS server 10.10.1.10 only hosts the internal zone; PCs point only to it with no forwarder.",
    """
DNS-Server# show run | section forward
(no forwarders configured)

PC> nslookup www.example.com
Server: 10.10.1.10
*** 10.10.1.10 can't find www.example.com: Non-existent domain
""",
    "The internal DNS server has no forwarder configured for external queries, so it can resolve internal records but returns NXDOMAIN for anything outside its own zone.",
    "Layer 7", "dns-missing-forwarder", "Medium")

add("C015", "DNS", "Employees report the intranet site loads a completely different (old) server's content since yesterday's migration.",
    "Intranet was migrated from 10.1.1.50 to 10.1.1.80; internal DNS record for intranet.company.local was supposed to be updated.",
    """
PC> nslookup intranet.company.local
Server: 10.10.1.10
Address: 10.10.1.10
Name: intranet.company.local
Address: 10.1.1.50
""",
    "The DNS A record for intranet.company.local still points to the old server IP (10.1.1.50) instead of the migrated server (10.1.1.80); the record was never updated after the migration.",
    "Layer 7", "dns-stale-record", "Medium")

add("C016", "DNS", "Half the office can reach the ERP system by name, the other half gets 'page not found' even though both groups are on the same VLAN.",
    "PCs are split between two manually configured DNS servers, only one of which is authoritative for the internal zone.",
    """
PC-A> ipconfig /all
DNS Servers: 10.10.1.10

PC-B> ipconfig /all
DNS Servers: 10.10.1.11

nslookup erp.company.local 10.10.1.11
*** 10.10.1.11 can't find erp.company.local: Non-existent domain
""",
    "PC-B is pointed at 10.10.1.11, a DNS server that is not authoritative for (and has no record of) the internal zone, while PC-A's server 10.10.1.10 does -- inconsistent client DNS configuration, not a server-wide outage.",
    "Layer 7", "dns-inconsistent-client-config", "Low")

# ---------------- Routing (4) ----------------
add("C017", "Routing", "Two directly-connected LANs on the same router can reach each other, but neither can reach a third LAN one router further away.",
    "R1 connects LAN A and LAN B directly; LAN C is behind R2, reachable via R1-R2 link 10.0.0.0/30.",
    """
R1# show ip route
C   192.168.1.0/24 is directly connected, G0/0
C   192.168.2.0/24 is directly connected, G0/1
C   10.0.0.0/30 is directly connected, S0/0/0
(no route to 192.168.3.0/24)
""",
    "R1 has no route (static or dynamic) to the remote LAN C subnet 192.168.3.0/24; only directly connected networks appear in the routing table.",
    "Layer 3", "missing-static-route", "High")

add("C018", "Routing", "A newly added remote branch subnet is unreachable from HQ, even though the branch router shows the interface up and its own LAN working fine.",
    "HQ router R1 has a static route to the branch subnet configured pointing at the wrong next-hop.",
    """
R1# show run | include ip route
ip route 192.168.99.0 255.255.255.0 10.0.0.6

R1# show ip route
S   192.168.99.0/24 [1/0] via 10.0.0.6
C   10.0.0.0/30 is directly connected, S0/0/0
""",
    "The static route to 192.168.99.0/24 points to next-hop 10.0.0.6, which is not a valid address on the 10.0.0.0/30 point-to-point link (valid host range is only 10.0.0.1-10.0.0.2); the next-hop is wrong so the route is unusable.",
    "Layer 3", "wrong-next-hop", "High")

add("C019", "Routing", "OSPF-connected branch offices suddenly cannot reach HQ subnets; interfaces show up/up on both ends.",
    "R1 (HQ) and R2 (branch) run OSPF area 0 over a serial link.",
    """
R1# show ip ospf neighbor
(empty - no neighbors)

R1# show ip interface brief
S0/0/0   10.0.0.1   up   up

R2# show run | section router ospf
router ospf 1
 network 10.0.0.0 0.0.0.3 area 1
""",
    "R2 is advertising the shared link in OSPF area 1 while R1 advertises area 0 for the same network, an area mismatch that prevents the OSPF neighbor adjacency from forming, so no routes are exchanged.",
    "Layer 3", "routing-protocol-area-mismatch", "Critical")

add("C020", "Routing", "A PC can ping its own gateway and the router's other interfaces, but nothing beyond the router.",
    "PC subnet 192.168.7.0/24 gateway R1 G0/0; R1 has a route to the internet via ISP but PC subnet mask is wrong.",
    """
PC> ipconfig
IP Address: 192.168.7.50
Subnet Mask: 255.255.255.128
Default Gateway: 192.168.7.1

R1# show ip interface brief
G0/0   192.168.7.1   up   up  (mask /24)
""",
    "The PC's subnet mask (/25, 255.255.255.128) does not match the router interface's /24 mask, so the PC calculates a different subnet boundary than the router expects, breaking routing decisions for traffic beyond the local segment.",
    "Layer 3", "subnet-mask-mismatch", "Medium")

# ---------------- ACL (4) ----------------
add("C021", "ACL", "PCs in the Finance VLAN cannot reach the payroll server even though routing and DHCP are confirmed working.",
    "R1 G0/2 (Finance gateway) has an inbound ACL applied.",
    """
R1# show access-lists
Extended IP access list FINANCE-IN
 10 deny ip any host 192.168.50.10
 20 permit ip any any (0 matches)

R1# show run interface g0/2
interface GigabitEthernet0/2
 ip access-group FINANCE-IN in
""",
    "ACL entry 10 explicitly denies all traffic to the payroll server (192.168.50.10) before the permit-any statement is ever reached; the deny is matching and blocking legitimate Finance traffic.",
    "Layer 3/4", "acl-explicit-deny-blocking-traffic", "High")

add("C022", "ACL", "A newly added 'permit' rule for a new subnet doesn't seem to have any effect; traffic from that subnet is still blocked.",
    "ACL was edited by appending a permit line after an existing deny-any at the bottom.",
    """
R1# show access-lists
Extended IP access list BRANCH-ACL
 10 permit tcp 192.168.1.0 0.0.0.255 any eq 443
 20 deny ip any any
 30 permit ip 192.168.9.0 0.0.0.255 any
""",
    "Line 30, the new permit for 192.168.9.0/24, was appended after the 'deny ip any any' at line 20, which matches first and drops the traffic before the new permit is ever evaluated -- ACL entries are processed top-down and the implicit/explicit deny at line 20 short-circuits everything below it.",
    "Layer 3/4", "acl-rule-order-implicit-deny", "Medium")

add("C023", "ACL", "Traffic from the internet reaches the internal server, but the server's replies never get back out.",
    "ACL applied to R1's outside interface.",
    """
R1# show run interface g0/0
interface GigabitEthernet0/0
 ip access-group WAN-ACL in
 ip access-group WAN-ACL out

R1# show access-lists
Extended IP access list WAN-ACL
 10 permit tcp any host 203.0.113.10 eq 80
""",
    "The same ACL (WAN-ACL), which only permits inbound port 80 to the server, is also applied outbound on the same interface, so return traffic and any other outbound flow from the server hits the implicit deny -- the ACL was applied in the wrong direction/duplicated.",
    "Layer 3/4", "acl-wrong-direction", "High")

add("C024", "ACL", "A site-to-site VPN tunnel is up, but no application traffic passes between the two sites; ICMP works fine.",
    "ACL on R1 permits ICMP but not the TCP ports the application actually uses.",
    """
R1# show access-lists
Extended IP access list VPN-TRAFFIC
 10 permit icmp any any
 20 deny ip any any (matches=142)
""",
    "The ACL only explicitly permits ICMP; there is no permit statement for the application's TCP ports, so all non-ICMP traffic falls through to the deny-any and is blocked, while ping (ICMP) succeeds.",
    "Layer 3/4", "acl-missing-permit-for-app-traffic", "Medium")

# ---------------- NAT (3) ----------------
add("C025", "NAT", "Internal PCs can reach each other and the router, but nothing on the internet responds to their requests.",
    "R1 G0/0 inside, G0/1 outside; NAT overload expected on G0/1.",
    """
R1# show ip nat statistics
Total active translations: 0
Outside interfaces: (none)
Inside interfaces: (none)

R1# show run | include ip nat
(no ip nat inside / ip nat outside lines found)
""",
    "Neither interface has been marked with 'ip nat inside' or 'ip nat outside', so NAT is not actually applied anywhere even if a NAT/PAT rule exists in the config -- private addresses are being sent unmodified to the internet and dropped upstream.",
    "Layer 3", "nat-interfaces-not-marked", "High")

add("C026", "NAT", "Only one internal PC at a time can reach the internet; as soon as a second PC tries, the first one's session drops.",
    "R1 configured with static NAT pool instead of PAT/overload.",
    """
R1# show run | include ip nat
ip nat pool INTERNET 203.0.113.5 203.0.113.5 netmask 255.255.255.255
ip nat inside source list 1 pool INTERNET
""",
    "The NAT pool contains only a single public address (203.0.113.5) and is not configured with the 'overload' keyword, so only one internal host can hold a translation at a time instead of allowing many-to-one port address translation.",
    "Layer 3/4", "nat-pool-missing-overload", "Medium")

add("C027", "NAT", "After a router interface re-cabling, internal users lost internet access even though the physical link and IP addressing are unchanged.",
    "G0/0 and G0/1 roles were swapped during cabling but the NAT inside/outside statements were not updated.",
    """
R1# show run | include ip nat
interface GigabitEthernet0/0
 ip nat outside
interface GigabitEthernet0/1
 ip nat inside

R1# show ip interface brief
G0/0   192.168.1.1   up   up   (internal LAN, should be inside)
G0/1   203.0.113.1   up   up   (ISP link, should be outside)
""",
    "The 'ip nat inside'/'ip nat outside' designations are reversed relative to the physical topology after the re-cabling -- the internal LAN interface is marked outside and the ISP-facing interface is marked inside, so NAT translation never triggers correctly.",
    "Layer 3", "nat-inside-outside-reversed", "High")

# ---------------- Wireless (3) ----------------
add("C028", "Wireless", "Laptops repeatedly prompt for the Wi-Fi password and fail to connect to the corporate SSID.",
    "AP configured with WPA2-PSK on SSID 'CORP'.",
    """
AP# show run | section wlan CORP
wlan CORP
 security wpa wpa2
 wpa-psk ascii 0 CorpNetw0rk!
(Help desk confirms the passphrase distributed to users is 'CorpNetwork!')
""",
    "The passphrase configured on the AP ('CorpNetw0rk!') does not match the passphrase distributed to end users ('CorpNetwork!') -- a simple credential mismatch causing repeated authentication failures.",
    "Layer 2", "wireless-psk-mismatch", "Low")

add("C029", "Wireless", "Guest Wi-Fi users can successfully connect and get an IP address, but they can also reach internal file servers, which should be isolated.",
    "SSID 'GUEST' is supposed to map to VLAN 30 (isolated); AP config maps it to VLAN 10 (internal).",
    """
AP# show run | section wlan GUEST
wlan GUEST
 vlan 10
(expected: vlan 30 per network design doc)
""",
    "The Guest SSID is mapped to VLAN 10 (the internal/production VLAN) instead of the isolated Guest VLAN 30, so guest clients land on the same broadcast domain as internal servers -- this is a security-relevant misconfiguration, not a connectivity fault.",
    "Layer 2", "wireless-ssid-vlan-mapping-error", "High")

add("C030", "Wireless", "Wireless clients connect fine near the AP but constantly drop and struggle to reconnect at the far end of the office.",
    "AP1 on channel 6, AP2 (adjacent overlapping cell) also on channel 6 with high transmit power.",
    """
AP1# show wlan config | include channel
Channel: 6
AP2# show wlan config | include channel
Channel: 6

Site survey: AP1 and AP2 coverage cells overlap by ~40%
""",
    "AP1 and AP2 use the same 2.4GHz channel (6) in overlapping coverage areas, causing co-channel interference that degrades signal quality and connection stability at the cell edge -- an RF design issue rather than an authentication or VLAN fault.",
    "Layer 1/2", "wireless-co-channel-interference", "Medium")

# ---------------- Spanning Tree Protocol (STP) (3) ----------------
add("C031", "STP", "Network performance drops severely across the entire campus switch block due to massive frame flooding.",
    "SW1, SW2, SW3 in a triangle topology; SW3 was expected to be Root Bridge but has default priority.",
    """
SW1# show spanning-tree vlan 1
VLAN0001
  Spanning tree enabled protocol ieee
  Root ID    Priority    32769
             Address     0001.C467.1111
             This bridge is the root

SW3# show spanning-tree vlan 1
VLAN0001
  Root ID    Priority    32769
             Address     0001.C467.1111
""",
    "Core switch SW3 has default STP priority 32768, causing edge switch SW1 with a lower MAC address to win the Root election; suboptimal root placement causes excessive frame flooding across access uplinks.",
    "Layer 2", "stp-root-bridge-election", "High")

add("C032", "STP", "An access port connected to an unmanaged hub repeatedly transitions between Forwarding and Blocking, causing packet loss.",
    "SW1 Fa0/10 connects to a user hub; BPDU Guard was enabled on the port.",
    """
SW1# show interfaces fa0/10 status
Port      Name               Status       Vlan       Duplex  Speed Type
Fa0/10                       err-disabled 10         auto    auto  10/100BaseTX

SW1# show logging | include ErrDisable
%PM-4-ERR_DISABLE: bpduguard error detected on Fa0/10, putting Fa0/10 in err-disable state
""",
    "BPDU Guard put Fa0/10 into err-disabled state after detecting rogue BPDUs from an unmanaged switch/hub plugged into a PortFast-enabled access port.",
    "Layer 2", "stp-bpduguard-errdisable", "Medium")

add("C033", "STP", "Hosts on VLAN 20 experience broadcast storms after a new redundant link was added between SW1 and SW2.",
    "SW1 Gi0/2 -- SW2 Gi0/2 link added; PortFast was enabled globally or on trunk interface.",
    """
SW1# show run interface gi0/2
interface GigabitEthernet0/2
 switchport mode trunk
 spanning-tree portfast trunk
""",
    "PortFast trunk was enabled on uplink Gi0/2, bypassing Listening and Learning states upon link up and causing an immediate temporary Layer 2 switching loop.",
    "Layer 2", "stp-portfast-loop", "Critical")

# ---------------- EtherChannel (2) ----------------
add("C034", "EtherChannel", "EtherChannel link between SW1 and SW2 shows Port-Channel 1 down, and individual member links are suspended.",
    "Port-Channel 1 bundles Fa0/23 and Fa0/24; LACP protocol configured.",
    """
SW1# show etherchannel summary
Group  Port-channel  Protocol    Ports
------+-------------+-----------+-----------------------------------------------
1      Po1(SD)       LACP        Fa0/23(s) Fa0/24(s)

SW1# show run interface fa0/23
interface FastEthernet0/23
 channel-group 1 mode active
 speed 100
 duplex full

SW2# show run interface fa0/23
interface FastEthernet0/23
 channel-group 1 mode passive
 speed 10
 duplex full
""",
    "Speed mismatch on member interface Fa0/23 (SW1 is 100Mbps, SW2 is 10Mbps) prevents LACP bundling, causing member ports to be suspended.",
    "Layer 2", "etherchannel-misconfig", "High")

add("C035", "EtherChannel", "Traffic distribution across a 4-link EtherChannel is heavily skewed; one link carries 90% of all traffic while others sit idle.",
    "SW1 Po1 carries inter-subnet traffic routed by a single upstream core router MAC.",
    """
SW1# show etherchannel load-balance
EtherChannel Load-Balancing Operational State (src-mac):
Global LB Method: src-mac
""",
    "EtherChannel load-balancing hash is set to src-mac on a switch where all egress traffic originates from the same default gateway MAC, preventing traffic distribution across bundle links.",
    "Layer 2", "etherchannel-load-balance", "Medium")

# ---------------- HSRP/VRRP (2) ----------------
add("C036", "HSRP", "Hosts on VLAN 10 use R1 as active gateway, but when R1's WAN link drops, traffic still routes to R1 instead of failing over to R2.",
    "R1 and R2 configured with HSRP group 10 for 192.168.10.1; R1 priority 110, R2 priority 100.",
    """
R1# show standby vlan 10
Vlan10 - Group 10
  State is Active
  Virtual IP address is 192.168.10.1
  Priority 110 (configured 110)
  Track interface Serial0/0/0 decrements 20
  (Preemption disabled)
""",
    "HSRP preempt is not enabled on R2. Even though R1's tracked WAN interface failed and reduced its priority to 90 (below R2's 100), R2 will not take over active status without preempt enabled.",
    "Layer 3", "hsrp-preempt-missing", "High")

add("C037", "HSRP", "Both R1 and R2 claim to be the Active HSRP gateway for VLAN 30, resulting in duplicate IP warnings and MAC address flapping on the switch.",
    "R1 and R2 running HSRP group 30 on G0/0.30.",
    """
R1# show standby vlan 30
Vlan30 - Group 30
  State is Active
  Virtual IP address is 192.168.30.1
  Active router is local

R2# show standby vlan 30
Vlan30 - Group 30
  State is Active
  Virtual IP address is 192.168.30.1
  Active router is local

SW1# show logging | include Flapping
%SW_MATM-4-MACFLAP_NOTIF: Host 0000.0c07.ac1e in vlan 30 is flapping between port Gi0/1 and port Gi0/2
""",
    "HSRP hellos between R1 and R2 are blocked (or subinterfaces use mismatched HSRP authentication keys), leading both routers to believe the peer is dead and concurrently claim Active status.",
    "Layer 3", "hsrp-split-brain", "Critical")

# ---------------- IPv6 (2) ----------------
add("C038", "IPv6", "IPv6-enabled workstations can ping local IPv6 link-local addresses but cannot reach external IPv6 global unicast destinations.",
    "R1 G0/0 configured with IPv6 address 2001:db8:1::1/64.",
    """
R1# show run | include ipv6
ipv6 unicast-routing (MISSING)
interface GigabitEthernet0/0
 ipv6 address 2001:DB8:1::1/64

PC> ipconfig /all
IPv6 Address: 2001:db8:1::100
Default Gateway: fe80::1
""",
    "Global 'ipv6 unicast-routing' is missing on router R1; without it, R1 acts only as an IPv6 end-host and will not forward IPv6 packets between interfaces or send Router Advertisements.",
    "Layer 3", "ipv6-unicast-routing-disabled", "High")

add("C039", "IPv6", "Clients fail to acquire an IPv6 address automatically via SLAAC on VLAN 50.",
    "R1 G0/0.50 configured for IPv6; Router Advertisements suppressed.",
    """
R1# show run interface g0/0.50
interface GigabitEthernet0/0.50
 encapsulation dot1Q 50
 ipv6 address 2001:DB8:50::1/64
 ipv6 nd suppress-ra
""",
    "Router Advertisements are explicitly suppressed on G0/0.50 with 'ipv6 nd suppress-ra', preventing SLAAC clients from learning the network prefix and default gateway.",
    "Layer 3", "ipv6-slaac-ra-suppressed", "Medium")

# ---------------- Security (3) ----------------
add("C040", "Security", "Connecting a new user desktop to switch port Fa0/12 immediately causes the port link LED to turn amber and shut down.",
    "Port security enabled on Fa0/12 with maximum 1 MAC address.",
    """
SW1# show port-security interface fa0/12
Port Security              : Enabled
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Maximum MAC Addresses      : 1
Total MAC Addresses        : 1
Configured MAC Addresses   : 1 (0011.2233.4455)
Last Source Address:Vlan   : 00aa.bbcc.ddee:10
""",
    "Port security violation occurred on Fa0/12: incoming MAC address (00aa.bbcc.ddee) did not match the configured sticky MAC (0011.2233.4455), triggering the shutdown action.",
    "Layer 2", "port-security-violation", "Medium")

add("C041", "Security", "Network administrator cannot SSH into R1 from the Management VLAN 40, getting 'Connection refused'.",
    "R1 VTY lines configured for remote management access.",
    """
R1# show run | section line vty
line vty 0 4
 transport input telnet
 login local
""",
    "VTY lines on R1 are configured with 'transport input telnet' instead of 'transport input ssh' (or 'all'), blocking encrypted SSH connection attempts on TCP port 22.",
    "Layer 7", "ssh-transport-disabled", "Medium")

add("C042", "Security", "Switch management access fails for all admin credentials when authentication server is unreachable.",
    "SW1 configured to authenticate VTY logins via TACACS+.",
    """
SW1# show run | include aaa
aaa authentication login default group tacacs+
(no local fallback configured)

SW1# ping 10.40.1.5
Request timed out.
""",
    "AAA authentication is configured to use TACACS+ only without a 'local' fallback; when the TACACS+ server 10.40.1.5 is unreachable, admins are locked out.",
    "Layer 7", "aaa-missing-local-fallback", "High")

# ---------------- QoS (2) ----------------
add("C043", "QoS", "VoIP phone calls experience severe jitter and audio clipping whenever large file downloads occur over the WAN link.",
    "R1 WAN interface G0/1 has no queuing strategy configured; default FIFO queue drops voice packets during congestion.",
    """
R1# show interface g0/1 | include Queueing
Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 1420
Queueing strategy: fifo

R1# show policy-map interface g0/1
(no policy-map attached)
""",
    "No QoS policy-map (LLQ / CBWFQ) is applied on WAN interface G0/1; default FIFO queuing drops latency-sensitive VoIP packets under link saturation.",
    "Layer 3/4", "qos-missing-voip-llq", "Medium")

add("C044", "QoS", "Differentiated Services Code Point (DSCP) EF markings set by IP phones are wiped out at the access switch.",
    "SW1 Fa0/5 access port connects to IP Phone.",
    """
SW1# show run interface fa0/5
interface FastEthernet0/5
 mls qos trust cos (MISSING)
 no mls qos trust
""",
    "Access switch port Fa0/5 does not trust CoS/DSCP markings from the connected IP phone ('no mls qos trust'), overwriting incoming voice packets to DSCP 0 (Best Effort).",
    "Layer 2/3", "qos-untrusted-boundary", "Low")

# ---------------- Advanced VLAN/Routing/NAT (6) ----------------
add("C045", "VLAN", "Inter-VLAN routing for VLAN 60 fails completely on router-on-a-stick topology while VLAN 10 and 20 work fine.",
    "R1 G0/0.60 subinterface configured for VLAN 60 gateway.",
    """
R1# show run interface g0/0.60
interface GigabitEthernet0/0.60
 encapsulation dot1Q 65
 ip address 192.168.60.1 255.255.255.0
""",
    "Subinterface G0/0.60 has encapsulation mismatched to dot1Q 65 instead of dot1Q 60, causing tagged frames from VLAN 60 to be ignored by the subinterface.",
    "Layer 2/3", "roas-vlan-id-mismatch", "High")

add("C046", "Routing", "A router's CPU utilization spikes to 100% and traffic between two internal subnets is dropped due to TTL expired.",
    "R1 and R2 have static routes for 172.20.0.0/16 pointing to each other.",
    """
R1# show ip route 172.20.0.0
S   172.20.0.0/16 [1/0] via 10.0.0.2 (R2)

R2# show ip route 172.20.0.0
S   172.20.0.0/16 [1/0] via 10.0.0.1 (R1)
""",
    "Routing loop between R1 and R2 for destination network 172.20.0.0/16; both routers point to each other as the next-hop, causing packets to bounce until TTL expires.",
    "Layer 3", "routing-loop-static", "Critical")

add("C047", "NAT", "Web server in DMZ (192.168.100.10) is unreachable from the internet on public IP 203.0.113.50.",
    "Static NAT configured on R1.",
    """
R1# show ip nat translations
Pro Inside global      Inside local       Outside local      Outside global
tcp 203.0.113.50:80    192.168.100.10:808 ---                ---

R1# show run | include ip nat inside source
ip nat inside source static tcp 192.168.100.10 808 203.0.113.50 80 extendable
""",
    "Static NAT rule maps public port 80 to internal port 808 instead of port 80 on the web server, causing external HTTP requests to hit a closed port.",
    "Layer 3/4", "nat-static-port-mismatch", "High")

add("C048", "ACL", "Admin host 10.40.1.100 cannot access web management on switch SW1, but pings succeed.",
    "SW1 HTTP server enabled with access-class 50.",
    """
SW1# show run | include ip http
ip http server
ip http access-class 50

SW1# show access-lists 50
Standard IP access list 50
 10 permit 10.40.2.0, wildcard bits 0.0.0.255
""",
    "Standard ACL 50 protecting the switch HTTP server permits 10.40.2.0/24 but omits admin subnet 10.40.1.0/24, denying web access while pinging (ICMP) remains unaffected.",
    "Layer 7", "acl-http-access-class-denied", "Medium")

add("C049", "Routing", "BGP session between R1 (AS 65001) and ISP router (AS 65002) stays in 'Active' or 'Idle' state indefinitely.",
    "R1 eBGP peer configured over multi-hop loopback interfaces.",
    """
R1# show ip bgp summary
Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
198.51.100.1    4 65002       0       0        1    0    0 00:15:22 Active

R1# show run | section router bgp
router bgp 65001
 neighbor 198.51.100.1 remote-as 65002
 (ebgp-multihop missing)
""",
    "eBGP peer 198.51.100.1 is multiple hops away, but 'neighbor 198.51.100.1 ebgp-multihop' is not configured; default TTL of 1 drops eBGP packets before reaching the peer.",
    "Layer 3/4", "bgp-ebgp-multihop-missing", "High")

add("C050", "VLAN", "Laptops connected to IP Phone PC ports drop off the network whenever the phone reboots.",
    "SW1 Fa0/9 configured for voice and data VLANs.",
    """
SW1# show run interface fa0/9
interface FastEthernet0/9
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 10
""",
    "Data VLAN and Voice VLAN on Fa0/9 are both set to VLAN 10. Voice and data must be on separate VLANs to allow proper 802.1Q tagging and prioritization.",
    "Layer 2", "vlan-voice-data-same-vlan", "Low")

# ---------------- write CSV ----------------
fields = ["case_id", "category", "symptom", "topology_note", "show_output",
          "expected_fault", "osi_layer", "concept_tag", "severity"]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for c in cases:
        writer.writerow(c)

print(f"Wrote {len(cases)} cases to {OUTPUT}")

