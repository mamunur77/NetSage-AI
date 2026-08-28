# Responsible AI Log — NetSage AI

Every case in `cases.csv` was diagnosed by the AI (see `sample_ai_responses.csv`
for this demo run; `ai_diagnose.py` produces the live version) and then
reviewed by a human, logged in `review_log.csv`. Of 30 cases:

- **24 Accepted** — AI root cause matched the known-correct fault.
- **5 Edited** — AI got the general area right but the specific cause wrong
  or imprecise; human corrected it.
- **1 Rejected** — AI's root cause was substantively wrong; human replaced
  it entirely.

This log documents the 6 corrected cases in detail, as required by the
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
- **Why it matters:** This is the most serious of the six — the AI's
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

---

## Patterns worth watching (for the team retro)

1. **Confirmation bias toward the case category label.** C004 shows the AI
   reaching for a "VLAN" explanation because the case was tagged VLAN, even
   though the evidence didn't support it. Consider not passing the
   `category` field into the prompt, or explicitly instructing the model to
   ignore it as a hint.
2. **"Missing" vs. "wrong" conflation.** Both C016 and C018 show the AI
   treating "the state isn't what I expected" as "it doesn't exist," which
   leads to additive fixes instead of corrective ones. Worth adding a
   prompt rule: distinguish absence of evidence from evidence of a wrong
   value.
3. **Mechanism vs. symptom-shaped fixes.** C023 proposed a fix that
   addressed the right symptom (traffic blocked) but the wrong mechanism
   (permit lines vs. ACL direction). This is the highest-risk error type
   since acting on it could pass validation checks superficially while
   leaving the real bug in place.
4. **Confidence/severity calibration.** C029 shows the AI can find the
   right config line but under-rate the severity — a purely accuracy-based
   score would have called this case "correct" even though the framing was
   materially wrong.
