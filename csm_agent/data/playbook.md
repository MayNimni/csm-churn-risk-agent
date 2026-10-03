# CSM Playbook

> Learning project: a generic, illustrative playbook based on common Customer Success
> practices. Not an official playbook of JFrog or any other company.

Recommended actions per risk signal and opportunity. Each section's `Keys`
match the rule names returned by calculate_risk and the opportunity types
returned by find_opportunities.

## Artifact downloads dropping
Keys: download_drop

**Why it matters:** Downloads come mostly from CI pipelines. A drop usually
means builds moved to another tool, a project ended, or a team migrated away.

**First 48 hours:**
1. Check which repositories and package types lost traffic (Docker, npm, Maven...).
2. Ask the main contact whether a project ended or a team changed tooling.

**Next 2 weeks:**
3. If traffic moved to another tool, schedule a technical session with a Solutions Engineer.
4. If a project ended, map other teams that could onboard.

**Talking point:** "We noticed your artifact traffic dropped recently. Did something
change in your pipelines that we can help with?"

**Escalate if:** The drop is over 50%, or the customer mentions a competitor.

## Key user / champion left
Keys: key_user_left

**Why it matters:** Without a champion, nobody inside the account defends the
renewal or knows the value JFrog delivers.

**First 48 hours:**
1. Identify who inherited the role and request an introduction.
2. Check who else is active on the platform (admins, heavy users).

**Next 2 weeks:**
3. Hold a value review with the new owner: what JFrog does for them today, in numbers.
4. Build relationships with at least two more stakeholders (multi-threading).

**Talking point:** "I'd love to make sure you have everything you need to get the
most from the platform. Can we set up a short walkthrough?"

**Escalate if:** No replacement owner is identified within 2 weeks.

## Unused licensed products
Keys: shelfware, adoption

**Why it matters:** Paying for products that are not used is the easiest line to
cut at renewal. Activating them is both risk reduction and value delivery.

**First 48 hours:**
1. List the unused products and find out why: no time, no owner, or a technical blocker.

**Next 2 weeks:**
2. Offer an enablement session for one unused product, with a concrete first use case.
3. Agree on a success metric (e.g. first repositories scanned, first policy created).

**Talking point:** "You already have access to this capability. Let's get it working
for one team and show the value before the renewal conversation."

**Escalate if:** The customer asks to remove products from the contract.

## Renewal approaching
Keys: renewal_soon

**Why it matters:** Any open problem close to renewal directly threatens revenue,
and the time to fix it is short.

**First 48 hours:**
1. Review all open risk signals for the account and decide which must be solved before renewal.
2. Align with the Account Executive on the renewal plan and owner.

**Next 2 weeks:**
3. Hold a value review (usage, adoption, outcomes) with the decision maker.
4. Confirm the decision process, timeline and any procurement steps.

**Talking point:** "Before we talk about the renewal, I want to review what's been
working and what we should improve together."

**Escalate if:** The customer has not engaged 45 days before renewal.

## High-severity support tickets
Keys: high_severity_tickets

**Why it matters:** High-severity tickets often mean broken builds or blocked
releases. Unresolved, they quickly erode trust.

**First 48 hours:**
1. Review each open high-severity ticket with Support and confirm status and owner.
2. Contact the customer to acknowledge the impact and share the plan.

**Next 2 weeks:**
3. Hold a follow-up once tickets are resolved to confirm the customer is satisfied.
4. Check for a pattern (same component, same team) and address the root cause.

**Talking point:** "I saw you're dealing with some critical issues. I'm personally
following them with our support team."

**Escalate if:** A ticket is open for more than 5 business days.

## Under-consuming commitment
Keys: low_consumption

**Why it matters:** Using much less than committed suggests the customer may
reduce the commitment at renewal.

**First 48 hours:**
1. Compare current consumption with the original plan: which teams or projects were expected to onboard?

**Next 2 weeks:**
2. Help onboard the missing teams or workloads.
3. If the commitment was oversized, prepare a right-sizing proposal together with the Account Executive.

**Talking point:** "Let's look at which teams were planned to onboard and how we can
help them get started."

**Escalate if:** Consumption is under 50% of commitment.

## Low adoption across teams
Keys: low_projects

**Why it matters:** An account used by few teams depends on few people, and is
easier to replace.

**First 48 hours:**
1. Map which teams use the platform today and which teams do not.

**Next 2 weeks:**
2. Ask the champion for an introduction to one additional team.
3. Offer an onboarding session for the new team.

**Talking point:** "Other organizations your size typically use the platform across
more teams. Which team would benefit next?"

**Escalate if:** Adoption keeps decreasing for two months in a row.

## UI logins dropping
Keys: login_drop

**Why it matters:** A weak signal on its own, since most usage comes from machines.
Combined with other signals, it may show people disengaging.

**First 48 hours:**
1. Check whether downloads also dropped. If not, this is likely low priority.

**Next 2 weeks:**
2. If combined with other signals, include it in the conversation with the main contact.

**Talking point:** "Is the team getting what it needs from the UI, or is most of the
work automated now?"

**Escalate if:** Not on its own.

## Open critical vulnerabilities
Keys: critical_vulnerabilities, advanced_security

**Why it matters:** Many open critical vulnerabilities mean the team cannot keep up
with what Xray finds. That is a security risk for the customer and a reason to
question the value of scanning.

**First 48 hours:**
1. Review the open critical vulnerabilities with the customer's security owner.

**Next 2 weeks:**
2. Help them define policies and prioritize what to fix first.
3. Present Advanced Security as a way to focus on the vulnerabilities that actually matter.

**Talking point:** "Your scans found many critical issues. Let's help your team
focus on the ones that are actually exploitable."

**Escalate if:** The customer reports a security incident.

## Over-consuming / tier upgrade
Keys: tier_upgrade

**Why it matters:** Consuming above commitment means the customer gets a lot of
value, but may face surprise overage costs.

**First 48 hours:**
1. Review consumption trend and estimated overage cost.

**Next 2 weeks:**
2. Present a tier upgrade or higher commitment that is cheaper than paying overages.

**Talking point:** "Your usage has grown nicely. Let's make sure you're on the plan
that fits it best."

**Escalate if:** Overage costs surprised the customer.

## Security cross-sell
Keys: security_cross_sell

**Why it matters:** Customers using only Artifactory store packages but do not scan
them, which leaves a gap in their software supply chain security.

**First 48 hours:**
1. Find out how the customer handles open-source security today.

**Next 2 weeks:**
2. Offer a short demo or trial of Xray and Curation on one repository.

**Talking point:** "You're already storing all your packages with us. Want to see
what's inside them?"

**Escalate if:** Not applicable.

## Expansion and SaaS migration
Keys: expansion, saas_migration

**Why it matters:** Growing, healthy accounts are the best candidates to expand to
more teams or move to SaaS and reduce their maintenance burden.

**First 48 hours:**
1. Confirm the growth drivers: new teams, new projects, more pipelines.

**Next 2 weeks:**
2. For expansion: identify the next teams and involve the Account Executive.
3. For Self-Managed accounts: discuss the effort they spend on upgrades and
   maintenance, and whether SaaS would free their team.

**Talking point:** "Your usage keeps growing. Let's plan ahead so the platform
scales with you."

**Escalate if:** Not applicable.
