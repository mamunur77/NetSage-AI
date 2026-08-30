# Responsible AI Log — NetSage AI

Every case in `cases.csv` was diagnosed by the AI (see `sample_ai_responses.csv`
for this demo run; `ai_diagnose.py` produces the live version) and then
reviewed by a human, logged in `review_log.csv`. Of 50 cases:

- **41 Accepted** — AI root cause matched the known-correct fault.
- **6 Edited** — AI got the general area right but the specific cause wrong
  or imprecise; human corrected it.
- **3 Rejected** — AI's root cause was substantively wrong; human replaced
  it entirely.

This log documents the 9 corrected cases in detail, exceeding the
"at least 5 cases where the AI answer was corrected" deliverable.

---

## C004 — VLAN (Edited)

- **AI said:** Switchport Fa0/8 is misconfigured in the wrong VLAN.
- **Human found:** `show vlan brief` already shows Fa0/8 correctly in VLAN
  30. The AI pattern-matched "VLAN" in the case category and reached for a
  switchport misconfig without checking that the evidence already
  contradicted it. The real cause is a stale DHCP lease left over from the
  PC's previous VLAN 10 membership.
- **Why it matters:** Fixing the switchport (which was already correct)
  would have wasted a truck-roll / lab reset for nothing. This is exactly
  the kind of error human review exists to catch.

## C016 — DNS (Edited)

- **AI said:** DNS server 10.10.1.11 is down or unreachable.
- **Human found:** The server is up; it's simply not authoritative for the
  internal zone, and PC-B is pointed at the wrong DNS server. "Restarting a
  service" would not have changed anything.
- **Why it matters:** AI conflated "query failed" with "server is down" —
  an important distinction between a config problem (fix the client) and
  an availability problem (fix the server).

## C018 — Routing (Edited)

- **AI said:** HQ router is missing a route to the branch subnet.
- **Human found:** `show ip route` clearly lists a static route to
  192.168.99.0/24 — it exists, but its next-hop (10.0.0.6) isn't a valid
  address on the /30 link. AI's fix (add a route) would have created a
  conflicting duplicate route instead of correcting the real one.
- **Why it matters:** "Missing" vs. "wrong" routes need different fixes;
  conflating them can make the config worse.

## C023 — ACL (Rejected)

- **AI said:** The ACL is missing a permit statement for return traffic.
- **Human found:** The same ACL is applied both inbound and outbound on
  the interface, so return traffic hits the implicit deny regardless of
  what permit lines exist. Adding more permits would not fix a
  directionality problem.
- **Why it matters:** This is the most serious error — the AI's
  proposed fix addresses the wrong mechanism entirely and was fully
  rejected rather than merely edited.

## C029 — Wireless (Edited)

- **AI said:** Minor connectivity misconfiguration, low confidence.
- **Human found:** Guest SSID traffic is landing on the internal VLAN
  (10) instead of the isolated Guest VLAN (30) — a security exposure, not
  a connectivity glitch. Severity was raised and a security note was
  added.
- **Why it matters:** Confidence and severity both need review, not just
  root cause — an AI can be technically pointed at the right config line
  and still mis-frame the risk.

## C003 — VLAN (Edited)

- **AI said:** The core switch's native VLAN should change to match SW1.
- **Human found:** Per the network design doc, native VLAN 1 is the
  campus-wide trunk standard, so SW1 (native VLAN 15) is the outlier that
  should change, not the core switch. Evidence alone (two mismatched
  values) doesn't say which side is "correct" — that requires the design
  doc, which the AI didn't have.
- **Why it matters:** A reminder that some fixes depend on organizational
  standards outside the show-command evidence; the AI should flag this as
  a case needing a design-doc check rather than guessing a direction.

## C033 — STP (Rejected)

- **AI said:** SW1 PortFast is globally disabled, causing temporary link blocking on trunk ports.
- **Human found:** `spanning-tree portfast trunk` was explicitly enabled on uplink Gi0/2, bypassing Listening/Learning states and causing an immediate L2 loop. Enabling global PortFast would not stop the loop.
- **Why it matters:** Enabling global PortFast would aggravate loop vulnerability; the human reviewer correctly removed PortFast from the trunk uplink.

## C037 — HSRP (Edited)

- **AI said:** R1 and R2 have mismatched HSRP priority values causing active router contention.
- **Human found:** Priority mismatch is normal in HSRP. Both routers declared Active status ("split-brain") because HSRP hello messages were blocked between them on the subinterface.
- **Why it matters:** AI blamed configuration priority rather than reachability/filtering, which would leave both routers acting as active gateways.

## C046 — Routing Loop (Rejected)

- **AI said:** Destination Subnet 172.20.0.0/16 is unroutable due to missing default gateway on R1.
- **Human found:** R1 and R2 had mutual static routes pointing at each other for 172.20.0.0/16, causing packets to loop until TTL expired and spiking CPU to 100%.
- **Why it matters:** Adding a default gateway would not stop a 2-way routing loop. The static route pointing to R2 had to be removed.

---

## Patterns worth watching (for the team retro)

1. **Confirmation bias toward the case category label.** C004 shows the AI
   reaching for a "VLAN" explanation because the case was tagged VLAN, even
   though the evidence didn't support it.
2. **"Missing" vs. "wrong" conflation.** C016, C018, and C046 show the AI
   treating "the state isn't what I expected" as "it doesn't exist," which
   leads to additive fixes instead of corrective ones.
3. **Mechanism vs. symptom-shaped fixes.** C023 and C033 proposed fixes that
   addressed the right symptom but wrong mechanism. This is why human review
   is mandatory.
