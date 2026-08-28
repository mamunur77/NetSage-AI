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
