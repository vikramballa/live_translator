# Stage 1 of Idea → Working System: Understanding the Problem and Gathering Requirements

Scope: how experienced engineers turn a vague idea into clear requirements (what to build, for whom, under what constraints), plus quick quantitative sizing. Audience: self-taught or early-career developers who want a repeatable checklist.

Source quality: the interview frameworks (ByteByteGo/Alex Xu, system-design-primer, Hello Interview), Google design-doc guidance, Fowler, Patton, SVPG, the Working Backwards site and the Pragmatic Engineer were all fetched directly. DDIA is cited only through secondary reading notes, because the book text was not available. Event Storming notation comes from the Open Group standard, Wikipedia and course material, because the official site is only a landing page.

---

## 1. Techniques for turning a vague idea into clear requirements

### Takeaway
Experts start from the customer and the problem, not the solution. The usual tools each answer a different question:
- **PR/FAQ ("working backwards"):** should we build this at all, and for whom?
- **Job stories / JTBD:** in what situation, with what motivation, toward what outcome?
- **User stories:** small chunks of behaviour that each stand for a conversation.
- **Story mapping:** what is the whole flow, and what is the thinnest end-to-end slice?
- **Event Storming:** what actually happens in the domain, step by step?

They work best together, in roughly that order.

### Cited Findings

**Amazon Working Backwards (PR/FAQ)**
- The process exists so that leaders "start with the customer and work backwards." It is meant to work as a funnel that filters ideas early, not a tunnel that builds everything. — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- Press release structure:
  - **Heading:** a product name target customers understand, plus one sentence.
  - **Subheading:** one sentence naming the customer and the benefit. The customer must be defined precisely.
  - **Summary:** "Start with the city, media outlet, and your proposed launch date."
  - **Problem paragraph:** written from the customer's viewpoint. "Not all problems are created equal." The problem must have a large TAM, defined as customers with the problem × what they will pay to solve it.
  - **Solution paragraph:** must acknowledge competitors and say how the product differs.
  - **Close:** a spokesperson quote, a hypothetical customer quote, how easy it is to start, and a call to action.
  — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- The **external FAQ** answers customer and press questions (price, how it works, support, where to buy) in plain language. The **internal FAQ** covers "the challenging problems" (technical, financial, legal, operational):
  - unit economics and upfront investment
  - "top three reasons the product could fail"
  - third-party dependencies
  - TAM and demand
  - regulatory issues
  - assumptions that must hold
  — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- A first draft should take "a few hours, not a few days," so weak ideas are cheap to drop. Reviews aim at "truth-seeking vs. selling and improving vs. deciding." — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- Examples:
  - **AWS:** more than a year of PR/FAQ drafting before S3 and EC2 launched in 2006.
  - **Fulfillment by Amazon:** used two PR/FAQs, one for the seller and one for the buyer.
  - **Fire Phone:** the cautionary case. Its 3D technology "didn't solve any important problems for customers."
  — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)

**User stories**
- Fowler defines user stories as "chunks of desired behavior of a software system." A story's essence "can be written on a single note card." Stories are not detailed until they are close to development. — [Martin Fowler, UserStory](https://martinfowler.com/bliki/UserStory.html)
- Template: "As a [who] I want [what] so that [why]." The "so that" clause "provides important context" for moving from what customers think they want to what they actually need. — [Martin Fowler](https://martinfowler.com/bliki/UserStory.html)
- Kent Beck introduced stories in Extreme Programming (XP) to make requirements gathering "more informal and conversational" than long specifications. — [Martin Fowler](https://martinfowler.com/bliki/UserStory.html)
- Bill Wake's **INVEST** checklist for good stories:
  - **I**ndependent
  - **N**egotiable
  - **V**aluable
  - **E**stimable
  - **S**mall (person-days of work)
  - **T**estable
  — [Martin Fowler](https://martinfowler.com/bliki/UserStory.html)

**Job stories (Jobs-to-be-Done)**
- Intercom's format is "When ___, I want to ___, so I can ___." The three parts are situation, motivation and expected outcome. Intercom built it because most JTBD writing was applied to "milkshakes and chocolate bars." — [Intercom](https://www.intercom.com/blog/accidentally-invented-job-stories/)
- Job stories frame the need around the situation and context rather than a persona. Example: "When searching by postal code, a buyer wants to be required to enter a valid code so the buyer doesn't waste time." — [Mountain Goat Software](https://www.mountaingoatsoftware.com/blog/job-stories-offer-a-viable-alternative-to-user-stories)

**User story mapping (Jeff Patton)**
- A flat backlog is "a bag of context-free mulch." It does not explain what the system does, it hides missing stories, and it makes release planning tedious. — [Jeff Patton, The New Backlog](https://jpattonassociates.com/the-new-backlog/)
- How the map is built:
  - Put big user **activities** across the top as the **backbone**, left to right in "the order you'd explain the behavior of the system."
  - Put smaller **tasks/stories** beneath each activity as "ribs."
  - Vertical position is priority: higher means more necessary.
  - Backbone items are not prioritized against each other. They are essential; the backbone "just is."
  — [Jeff Patton](https://jpattonassociates.com/the-new-backlog/)
- The top row of stories forms the **walking skeleton** (Alistair Cockburn's term): the smallest system with end-to-end function. It is built first.
- Horizontal swim lanes slice releases. Prioritization happens *within* each backbone item, e.g. a car needs an engine, but which engine size is a priority decision. "That way we never release a car without brakes."
— [Jeff Patton](https://jpattonassociates.com/the-new-backlog/)

**Event Storming (Alberto Brandolini)**
- Event Storming is "a flexible workshop format for collaborative exploration of complex business domains." It relies on "cross-discipline conversations between business, service designers and IT representatives." — [EventStorming.com](https://www.eventstorming.com/)
- Styles: Improve (map an existing line of business and find blockers), Envision (a startup ecosystem), Explore (new services), Design (critical software, event-driven, aligned with DDD and microservices). — [EventStorming.com](https://www.eventstorming.com/)
- Notation:
  - **Orange** = domain events, past-tense verbs such as "Order Placed."
  - **Blue** = commands, placed directly before the event they trigger.
  - **Red/pink** = hot spots (open issues or confusion). Colour conventions vary slightly between sources.
  — [Open Group standard](https://pubs.opengroup.org/architecture/o-aa-standard/event-storming-workshop.html); [Wikipedia](https://en.wikipedia.org/wiki/Event_storming); [course lab PDF](https://sf.infs.ch/wp-content/uploads/4066/Lab3-EventStorming.pdf)

### Inferences
- A practical solo-developer sequence:
  1. A one-page PR/FAQ (forces "who is the customer, what problem, why now").
  2. 3–5 job stories for the main situations.
  3. A story map whose top row is the walking skeleton/MVP.
  4. Event Storming on a whiteboard only if the domain has a non-obvious multi-step process.
- Writing the internal FAQ's "top three reasons this could fail" amounts to a riskiest-assumptions list, which links directly to Section 2.
- User stories ("as a…") suit known personas. Job stories ("when…") suit products where the *situation* matters more than the role, e.g. "when I'm on a call with a supplier who speaks another language…".

### Gaps
- The exact PR/FAQ length limits (often quoted as ~1 page PR + up to 5 pages FAQ) were not on the fetched page. Check them in the *Working Backwards* book (Bryar & Carr).
- Brandolini's own step-by-step workshop phases (chaotic exploration → timeline → hot spots → pivotal events, etc.) were not available from a primary source in this pass.
- Christensen's original JTBD "milkshake" study was not fetched directly.

---

## 2. Separating functional vs non-functional requirements; constraints and riskiest assumptions

### Takeaway
- **Functional requirements** say what the system does: "Users should be able to…".
- **Non-functional requirements (NFRs)** say how well it must do it: "The system should be…". Experts **quantify** NFRs (e.g. p99 < 200 ms, 99.9% availability), keep only the top 3–5 that actually shape the design, and record explicit **non-goals**.
- Risk is tackled first. Cagan's four risks (value, usability, feasibility, viability) are a simple way to list the riskiest assumptions.

### Cited Findings

**Definitions**
- DDIA defines functional requirements as "the functionality that the application must offer" and nonfunctional requirements as "everything else." The boundary is fuzzy because performance is a matter of degree. — [Bill Mill's DDIA ch.2 notes](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)
- The DDIA 2nd edition chapter 2 covers four NFRs: performance, reliability, scalability and maintainability. — [ExplainThis DDIA ch2 guide](https://www.explainthis.io/en/swe/ddia-ch2-non-functional-requirements)

**Hello Interview phrasing**
- Functional requirements are written as "Users/Clients should be able to…". You should "identify and prioritize the top 3." "Keep your requirements targeted!" — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- NFRs are written as "The system should be…", quantified and tied to the system. Example: "The system should have low latency search, < 500ms"; Twitter feeds render in under 200 ms. Pick the **top 3–5**. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Eight-area NFR checklist:
  1. CAP (consistency vs availability)
  2. Environment constraints (device, battery, memory, bandwidth)
  3. Scalability (bursty traffic, read/write ratio)
  4. Latency
  5. Durability (how much data loss is tolerable)
  6. Security
  7. Fault tolerance
  8. Compliance
  — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)

**Measuring performance and reliability (DDIA via notes)**
- Response time is what the client sees. Throughput is requests per second. Service time is active processing time. Latency is time spent waiting. — [Bill Mill's DDIA notes](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)
- Note: these notes also say "response time generally decreases as throughput increases." That runs against queueing theory and is probably a note-taking error.
- Use percentiles, not averages:
  - Amazon uses the **99.9th percentile** for internal service response-time requirements.
  - The 99.99th was judged too expensive to optimize.
  - Averaging percentiles is "meaningless."
  - Tail-latency amplification: a request that fans out to many backends is more likely to hit one slow one ("The Tail at Scale").
  — [Bill Mill's DDIA notes](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)
- Reliability vocabulary: a **fault** is one component going wrong; a **failure** is the whole system no longer providing service.
- A 2003 study found operator configuration changes were the leading cause of outages. Hardware caused only 10–25%.
— [Bill Mill's DDIA notes](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)

**Availability arithmetic (system-design-primer)**

| Availability | Downtime per year | Per month | Per day |
|---|---|---|---|
| 99.9% | 8h 45m 57s | 43m 49.7s | 1m 26.4s |
| 99.99% | 52m 35.7s | 4m 23s | 8.6s |

- Components in **sequence** multiply: two at 99.9% give 99.8%.
- Components in **parallel**: 1 − (1−A)(1−B). Two at 99.9% give 99.9999%.
— [system-design-primer](https://github.com/donnemartin/system-design-primer)

**Goals and non-goals (Google design docs)**
- Non-goals are things that "could reasonably be goals" but are deliberately excluded. They are not negated goals: "non-goals aren't negated goals like 'The system shouldn't crash'." Example: ACID compliance as a non-goal for a database. — [Malte Ubl, Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- The "Context and scope" section "isn't a requirements doc. Keep it succinct!" — [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)

**Riskiest assumptions (Cagan's four big risks)**
- **Value:** "whether customers will buy it or users will choose to use it." Owned by the PM.
- **Usability:** can users figure it out? Owned by the designer.
- **Feasibility:** can engineers build it with the available time, skills and technology? Owned by the lead engineer.
- **Business viability:** go-to-market, compliance, acquisition cost, monetization. Owned by the PM.
- Strong teams "tackle the big risks early."
— [SVPG, The Four Big Risks](https://www.svpg.com/four-big-risks/)

### Inferences
- A checklist rule: every NFR must contain a **number and a percentile or time window**. "Fast" is not a requirement; "p95 speech-end → first audio ≤ 2.0 s" is.
- Do the sequence-availability maths early. A chain of five 99.9% services gives only ~99.5%, which is why long synchronous call chains quietly break availability targets.
- Constraints worth listing separately from NFRs: budget, team size and skills, deadlines, mandated platforms or licences, regulation, existing systems.
- Rank each assumption by (impact if wrong) × (uncertainty). The top 1–3 become the first experiments or spikes, before any polished build.

### Gaps
- No primary source was fetched on formal "Riskiest Assumption Test" (RAT) methodology. Cagan's four risks are used as the stand-in.
- The DDIA 1st-edition Twitter load figures (often quoted as ~4.6k tweets/s average, ~12k peak, ~300k timeline reads/s, from 2012) come from memory and were not verified in this pass. Mark them [VERIFY] if used.
- ISO/IEC 25010 quality-attribute taxonomy not covered.

---

## 3. Clarifying questions the system design frameworks recommend asking first

### Takeaway
All three major frameworks open with 3–10 minutes of clarifying questions. The questions cover:
- who the users are and how many
- the core features (top ~3)
- inputs and outputs
- data volume and requests per second
- read/write ratio
- growth
- the existing stack

Write the answers down as explicit assumptions.

### Cited Findings
- **Alex Xu, Step 1 "Understand the problem and establish design scope" (3–10 min of 45).** "The interview is not a trivia contest." Ask:
  - What specific features will we build?
  - How many users does the product have?
  - How fast does the company expect to scale up (in 3, 6 and 12 months)?
  - What is the existing tech stack, and which services could simplify the design?

  Write down assumptions you are asked to make. — [ByteByteGo, A Framework for System Design Interviews](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Xu's news-feed worked example of the answers:
  - mobile + web
  - posting and viewing friends' feeds are the key features
  - reverse-chronological order (to keep it simple)
  - 5,000-friend limit
  - 10 million DAU
  - images and video supported
  — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Xu's remaining steps: (2) high-level design and buy-in (10–15 min), (3) deep dive (10–25 min), (4) wrap-up (3–5 min). — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- **system-design-primer Step 1 "Outline use cases, constraints, and assumptions."** Ask:
  - Who is going to use it?
  - How are they going to use it?
  - How many users are there?
  - What does the system do?
  - What are the inputs and outputs of the system?
  - How much data do we expect to handle?
  - How many requests per second do we expect?
  - What is the expected read to write ratio?
  — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- The primer's Pastebin solution shows the output format:
  - **In scope:** paste text → random link, optional expiry, view paste, anonymous users, monthly stats, delete expired pastes, highly available.
  - **Out of scope:** accounts, login and editing, visibility settings, custom shortlinks.
  - **Constraints:** traffic is uneven, following a link should be fast, text only, analytics need not be real-time, 10M users, 10M writes/month, 100M reads/month, 10:1 read:write.
  — [system-design-primer Pastebin](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md)
- **Hello Interview delivery framework**:
  1. Requirements (~5 min)
  2. Core entities (~2 min)
  3. API / system interface (~5 min)
  4. Optional data flow (~5 min)
  5. High-level design (~10–15 min)
  6. Deep dives (~10 min)

  Treat requirements as a back-and-forth "as if talking to a product manager." For entities, ask: who are the actors, and what nouns do the functional requirements need? — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Hello Interview's API defaults: REST unless there is a reason not to; GraphQL for diverse clients; gRPC for internal performance-critical calls; WebSockets/SSE added for real-time features. Derive the user from the auth token, never from the request body. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)

### Inferences
- Merged first-questions checklist for real projects, not just interviews:
  1. Who are the users, and what job are they hiring this for?
  2. Top 3 things they must be able to do.
  3. Inputs and outputs (data types and sizes).
  4. How many users (DAU), and how many concurrent?
  5. Requests per second, average and peak.
  6. Read:write ratio.
  7. Data volume per item and retention.
  8. Latency target (percentile).
  9. Availability and durability target.
  10. Consistency needs.
  11. Security, privacy and compliance.
  12. Devices, network and bandwidth constraints.
  13. Growth over 3/6/12 months.
  14. Existing stack, team and budget.
  15. Explicitly out of scope.
- On a real project, the "interviewer" is the user, customer or stakeholder. If you are building alone, write both the questions and your assumed answers, then validate the assumptions that matter most (Section 2).

### Gaps
- Hello Interview's per-problem question lists (e.g. for chat or ride-share) were not fetched.

---

## 4. Back-of-the-envelope estimation, with a worked example

### Takeaway
Estimation exists to answer "does this change the design?":
- one machine or many?
- cache or not?
- shard or not?

Use a few memorized constants (latency numbers, powers of two, 1 month ≈ 2.5M seconds), round aggressively, and compute QPS, storage and bandwidth. Hello Interview advises skipping maths that won't change a decision.

### Cited Findings

**When to estimate**
- Xu places back-of-the-envelope maths in Step 2, to check that the blueprint fits the scale constraints, and asks you to think out loud. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Hello Interview: "perform calculations only if they will directly influence your design." Example where it matters: estimating topic volume for Top-K trending decides between one min-heap and sharding. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)

**Constants to memorize**
- Latency numbers (as reproduced in system-design-primer):

| Operation | Latency |
|---|---|
| L1 cache reference | 0.5 ns |
| Branch mispredict | 5 ns |
| L2 cache reference | 7 ns |
| Mutex lock/unlock | 25 ns |
| Main memory reference | 100 ns |
| Compress 1 KB (Zippy) | 10 µs |
| Send 1 KB over 1 Gbps | 10 µs |
| Random 4 KB SSD read | 150 µs |
| Read 1 MB sequentially from memory | 250 µs |
| Round trip within a datacenter | 500 µs |
| Read 1 MB sequentially from SSD | 1 ms |
| HDD seek | 10 ms |
| Read 1 MB over 1 Gbps | 10 ms |
| Read 1 MB sequentially from HDD | 30 ms |
| Packet CA → Netherlands → CA | 150 ms |

  Handy derived rates: HDD 30 MB/s, 1 Gbps Ethernet 100 MB/s, SSD 1 GB/s, memory 4 GB/s, "6-7 world-wide round trips per second," "2,000 round trips per second within a data center." — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Powers of two: 2^10 ≈ 1 thousand (1 KB), 2^20 ≈ 1 million (1 MB), 2^30 ≈ 1 billion (1 GB), 2^32 = 4 GB, 2^40 ≈ 1 trillion (1 TB). — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Where the latency numbers come from:
  - The table traces to Jeff Dean's talks, drawing on Peter Norvig's work. Sources disagree on the date: one says a 2002 talk, others a ~2010 Stanford lecture.
  - In 2012 Colin Scott found that "the numbers Jeff quotes are over a decade old" and built an interactive, year-adjusted version.
  - Newer estimates differ, e.g. L1 1 ns, L2 4 ns, mutex 17 ns. Treat all of them as orders of magnitude, not measurements.
  — [HighScalability](https://highscalability.com/more-numbers-every-awesome-programmer-must-know/); [freeCodeCamp](https://www.freecodecamp.org/news/must-know-numbers-for-every-computer-engineer/)

**Worked example (Pastebin, system-design-primer)**
- Inputs: 10M users, 10M paste writes/month, 100M reads/month, 10:1 read:write.
- Size per paste ≈ 1.27 KB: 1 KB content + 7-byte shortlink + 4-byte expiry + 5-byte timestamp + 255-byte path.
- Storage: ~12.7 GB/month of new pastes, and ~450 GB over 3 years (~360M shortlinks).
- Traffic: ~4 writes/s and ~40 reads/s on average.
- Conversions: 1 month ≈ 2.5M seconds; 1 req/s ≈ 2.5M req/month; 40 req/s ≈ 100M/month; 400 req/s ≈ 1B/month.
— [system-design-primer Pastebin](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md)

### Inferences
- **Generic recipe** (my synthesis of the above):
  1. DAU × actions per user per day = actions/day.
  2. ÷ ~100k s/day (86,400 rounded) = average QPS.
  3. × a peak factor (assume 2–10× unless you know better; state it).
  4. Item size × writes/day × retention days = storage. Add replication (×3 is a common assumption) and indexes.
  5. Average QPS × response size = egress bandwidth.
  6. Compare against the constants: does it fit in RAM on one box? Does one SSD's IOPS suffice? Does the latency budget allow a cross-region round trip (150 ms)?
- **Second worked example** (illustrative arithmetic; the inputs are assumptions, not sourced data): a chat app with 1M DAU sending 40 messages/day of ~200 bytes.
  - 40M messages/day ÷ ~86,400 s ≈ **~460 writes/s average**. At an assumed 5× peak, ~2,300/s.
  - Storage: 40M × 200 B = 8 GB/day, so **~2.9 TB/year** raw, and ~9 TB/year with 3× replication.
  - Conclusions: write QPS fits a single well-tuned database, but storage growth means planning partitioning or retention within a year. The real design pressure is fan-out and connections, not QPS.
- **Latency-budget estimation** applies the same thinking to a single request's critical path. Add up the stages (network RTTs + queueing + compute per stage) against the p95 target. This matters more than QPS for real-time systems such as voice pipelines.
- Common unit traps: bits vs bytes (1 Gbps ≈ 125 MB/s theoretical, ~100 MB/s practical, per the primer's handy metric); decimal vs binary units; and the average vs peak gap.

### Gaps
- No primary Jeff Dean slide deck or Norvig page was fetched, so the origin date conflict (2002 vs ~2010) is unresolved.
- No authoritative source was found for "typical" peak-to-average ratios. Treat them as stated assumptions.

---

## 5. Defining scope/MVP and success metrics; deciding what NOT to build

### Takeaway
- Scope is defined as much by what is excluded as by what is included: explicit out-of-scope lists and non-goals.
- The MVP is the thinnest end-to-end slice (the walking skeleton), not one finished feature.
- Success metrics are written as quantified NFRs and customer outcomes. The PR/FAQ funnel exists to kill ideas cheaply before anything is built.

### Cited Findings
- Story mapping: the walking skeleton (top row across every backbone activity) is the first release, so you "never release a car without brakes." Build left-to-right and top-to-bottom, a little of every feature at a time rather than one feature at a time. — [Jeff Patton](https://jpattonassociates.com/the-new-backlog/)
- The Pastebin solution lists four explicit **out-of-scope** items (accounts, login/editing, visibility, custom links) next to the in-scope list. — [system-design-primer Pastebin](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md)
- Google design docs: non-goals are reasonable goals deliberately excluded. Skip the design doc entirely when the problem is not ambiguous; docs that are just "implementation manuals" mean you should "just write the program." "'I tried it out and it works' is one of the best arguments for choosing a design." Mini design docs of 1–3 pages are valid; large projects run "around 10-20ish pages." — [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- The PR/FAQ rejects ideas that are copycats, have too small a TAM, carry too much upfront risk, aren't viable yet, or lose to backlog priorities. — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- Hello Interview: limit functional requirements to the top 3 and NFRs to the top 3–5. A long list "will hurt you more than it will help you." — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Pragmatic Engineer on writing plans first:
  - Writing exposes disagreements and missed edge cases early instead of halfway through.
  - A plan that is hard to write may signal a project that will take longer than expected.
  - Templates grow from recurring reviewer questions such as "What is the motivation to do this work?" and "How will this be tested?"
  - Uber's backend RFC template includes service SLAs, dependencies, load testing, security, rollout, and metrics/monitoring.
  — [The Pragmatic Engineer](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)
- Xu's wrap-up step asks how to handle "the next scale curve" (e.g. 1M → 10M users), which implies the MVP is sized for the current curve, not the final one. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)

### Inferences
- **MVP definition checklist:**
  1. One primary user and one primary job.
  2. The walking skeleton across all backbone steps.
  3. 3 functional requirements.
  4. 3–5 quantified NFRs.
  5. A written non-goals list (things people will reasonably expect but you will not do yet).
  6. The 1–3 riskiest assumptions the MVP is designed to test.
  7. A "next scale curve" note saying what changes at 10× load.
- **Success metrics in three layers:**
  - Customer outcome (e.g. task completed, retention).
  - Quality/SLO (p95 latency, error rate, availability).
  - Guardrails (cost per user, critical-error rate).
- Each metric needs a target, a measurement method and a fixed evaluation set or window.
- "What not to build" heuristics:
  - Anything not on the walking-skeleton row.
  - Anything that serves a scale you have not reached (Xu's "next curve").
  - Anything whose only justification is "it would be nice."
  - Anything that adds a dependency to the critical path without moving a top-3 requirement.

### Gaps
- No primary source fetched on HEART/North-Star metric frameworks or OKRs. The success-metric layering above is my own synthesis.
- Eric Ries's original MVP definition (*The Lean Startup*) was not fetched.

---

## 6. Common beginner mistakes at this stage, and how experts avoid them

### Takeaway
The dominant beginner failures are:
- jumping to a solution before clarifying
- over-engineering for imagined scale
- listing too many requirements
- doing estimates that change nothing
- going deep on one component before an end-to-end design exists
- working silently or alone without checking shared understanding

Experts counter each with time-boxed clarification, written assumptions, explicit non-goals, and early feedback.

### Cited Findings
- From Alex Xu's framework:
  - Answering too quickly: the "Jimmy" archetype who blurts out answers.
  - "Don't jump into a solution before clarifying the requirements and assumptions."
  - Over-engineering is "a real disease of many engineers."
  - Don't dive deep into one component before the high-level design exists.
  - Don't think in silence.
  - Don't be stubborn with feedback.
  - Never claim the design is perfect.
  — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- From Hello Interview:
  - The most common failure is "failing to deliver a working system," often blamed on time management.
  - Listing too many requirements.
  - Unnecessary estimation.
  - Layering on complexity too early.
  - Trusting user IDs from request bodies instead of auth.
  — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- From the Pragmatic Engineer:
  - Skipping the write-up.
  - Overdoing the "how."
  - Limiting review to a small circle.
  - Assuming shared understanding without checking. The warning sign is "This is not what I meant when we talked."
  — [The Pragmatic Engineer](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)
- From Patton: working from a flat backlog hides missing stories and loses the narrative of what the system does. — [Jeff Patton](https://jpattonassociates.com/the-new-backlog/)
- From Working Backwards: building technology that doesn't solve an important customer problem (the Fire Phone's 3D feature). — [Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- From DDIA notes: using averages instead of percentiles for latency; averaging percentiles. — [Bill Mill's DDIA notes](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)
- From Google design docs: writing non-goals as negated goals ("shouldn't crash"); writing a design doc that is just an implementation manual. — [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)

### Inferences

| Beginner mistake | Expert habit |
|---|---|
| Starts coding or choosing tech first | Writes the PR/FAQ or problem statement and the top-3 job stories first |
| "It should be fast and scalable" | Quantified NFR with a percentile and a number |
| Designs for 100M users on day one | Sizes for the current curve; notes what changes at 10× |
| 20 features in v1 | 3 functional requirements + walking skeleton + written non-goals |
| Estimates everything | Estimates only what decides between design options |
| Polishes one component | Gets an ugly end-to-end slice working first |
| Assumes, never writes it down | Keeps an explicit assumptions list, ranked by risk |
| Trusts the happy path | Asks "top 3 reasons this fails" (internal FAQ) and lists fault cases |
| Works alone | Shares a short written plan early and asks for written feedback |

### Gaps
- No empirical data was found on how often these mistakes cause real (non-interview) project failures. The evidence is practitioner opinion and interview-coaching experience.
