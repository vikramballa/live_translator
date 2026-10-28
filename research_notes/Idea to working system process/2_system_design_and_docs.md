# System Design and Design Documentation: How Experts Go from Requirements to a Reviewable, Executable Design

Research date: 2026-10-19. Audience: self-taught / early-career developer. Sources are mostly primary (Fowler, Ubl, Nygard, McKinley, c4model.com, ByteByteGo, Hello Interview, system-design-primer). DDIA and Ousterhout content comes from secondary book notes because the book text was not retrievable (O'Reilly returned 403); those items are flagged.

---

## 1. Step-by-step approach: requirements -> high-level design -> deep dive

### Takeaway
Every major framework follows the same arc: (1) clarify scope and write down assumptions, (2) list functional and a few quantified non-functional requirements, (3) name core entities and the API, (4) draw boxes-and-arrows and walk one request through it end to end, (5) deep-dive only where the non-functional requirements or bottlenecks bite, and (6) wrap up with bottlenecks, failure cases, operations and the next scale tier. The process matters more than the final picture.

### Cited Findings
**Alex Xu, *System Design Interview* (4-step framework, ByteByteGo)**
- Step 1, "Understand the problem and establish design scope" (3–10 min of a 45-min session): "do not jump right in to give a solution. Slow down." Ask which features, how many users, expected scale in 3/6/12 months, existing tech stack and services you can reuse. Write assumptions down. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Step 2, "Propose high-level design and get buy-in" (10–15 min): draw box diagrams (clients, APIs, web servers, data stores, cache, CDN, queues), do back-of-the-envelope checks, walk through concrete use cases (which "often reveals edge cases"), include API endpoints and DB schema only where the problem warrants it. News-feed example splits into two flows: feed publishing and feed building. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Step 3, "Design deep dive" (10–25 min): first confirm goals, scope and blueprint are agreed, then prioritise the components that matter; "Try not to get into unnecessary details." — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Step 4, "Wrap up" (3–5 min): identify bottlenecks (never claim the design is perfect), recap, error cases (server failure, network loss), operations (metrics, logs, rollout), what changes from 1M to 10M users. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- The framework says the "final design is less important compared to the work you put in the design process." Don'ts include diving deep into one component before the high-level design exists. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)

**Hello Interview "Delivery" framework**
- Steps with time budgets: Requirements (~5 min; functional as "Users should be able to…", ideally ~3; non-functional top 3–5, quantified) -> Core Entities (~2 min) -> API/interface (~5 min, REST by default, derive user from auth token) -> optional Data Flow (~5 min, for pipeline-like systems) -> High-Level Design (~10–15 min, built one endpoint at a time, noting where caches/queues could go) -> Deep Dives (~10 min, harden against the non-functional requirements). — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- "Having a long list of requirements will hurt you more than it will help you." — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Estimates: "perform calculations only if they will directly influence your design" (e.g. one instance vs sharding). — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Non-functional checklist: CAP (consistency vs availability), environment constraints (battery, memory, bandwidth), scalability (bursts, read/write ratio), latency, durability, security, fault tolerance, compliance. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- "Never rely on sensitive information like user IDs from request bodies when they should come from authentication." — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)

**system-design-primer (Donne Martin)**
- Four steps: (1) outline use cases, constraints, assumptions (who uses it, how many users, inputs/outputs, data volume, requests/sec, read:write ratio), (2) high-level design, (3) design core components (e.g. URL shortener: hash function, SQL vs NoSQL, schema, API), (4) scale the design: find bottlenecks, then load balancers, horizontal scaling, caching, sharding. "Everything is a trade-off." — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Performance vs scalability: a performance problem means slow for one user; a scalability problem means fast for one user but slow under load. Latency = time per action; throughput = actions per unit time; aim for "maximal throughput with acceptable latency." — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Availability maths: components in sequence multiply (two at 99.9% -> 99.8%); in parallel, 1 − (1−A)(1−A) (two at 99.9% -> 99.9999%). 99.9% ≈ 8h46m downtime/year; 99.99% ≈ 52m36s/year. — [system-design-primer](https://github.com/donnemartin/system-design-primer)

**Kleppmann, *Designing Data-Intensive Applications* (DDIA), chapter 1 (via book notes; not verified against book text)**
- Three concerns: **Reliability** = keep working correctly even when things go wrong (hardware faults, software faults, human error). A *fault* is one component deviating from spec; a *failure* is the whole system no longer delivering service; fault tolerance stops faults becoming failures. — [candost.blog notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications); [10k.mataroa notes](https://10k.mataroa.blog/blog/ddia-chapter1-note/)
- **Scalability** = ability to cope with increased load, described by *load parameters* specific to the system (requests/sec, read:write ratio, active users per chat room). Twitter example: ~12k tweets/sec writes is easy; the hard part is fan-out to followers. — [candost.blog notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications)
- Measure response time as a distribution (p50, p95, p99, p999); averages hide tail pain; SLOs/SLAs are built on percentiles; queueing delay dominates high percentiles. — [candost.blog notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications); [10k.mataroa notes](https://10k.mataroa.blog/blog/ddia-chapter1-note/)
- Scale up (bigger machine) vs out (more machines): neither is a silver bullet; manually scaled systems are simpler to operate; unproven products should prioritise iterating on the product over hypothetical future load. — [candost.blog notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications)
- **Maintainability** = operability (make routine ops easy), simplicity (remove *accidental* complexity, mainly via good abstractions, to avoid a "big ball of mud"), evolvability (easy to change as requirements change). — [candost.blog notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications)
- A DDIA reading guide describes a "Chapter 2" on non-functional requirements framed as performance, reliability, scalability, maintainability, with latency broken down into network, queueing and execution stages, each measured separately. This matches the 2nd-edition restructuring, but the page does not name the edition. — [explainthis.io](https://www.explainthis.io/en/swe/ddia-ch2-non-functional-requirements)

### Inferences
- **Unified working procedure (real projects, not just interviews):**
  1. *Scope*: one paragraph on the problem, users and success; list assumptions explicitly.
  2. *Requirements*: ≤3–5 functional ("User can…"), 3–5 quantified non-functional (latency p50/p95, availability, durability, cost ceiling, privacy/compliance). Write non-goals.
  3. *Load parameters and estimates*: only the numbers that change a decision (QPS, data/day, concurrent sessions, bytes per request).
  4. *Core entities and data model*: nouns, ownership, rough schema, and where the source of truth lives.
  5. *API/interfaces*: external contract first, then internal component contracts.
  6. *High-level design*: boxes for runtime units (C4 "containers"), arrows for data flow; trace one request end to end, then the main failure path.
  7. *Deep dives*: for each non-functional requirement, find the component that threatens it (bottleneck, single point of failure, consistency hazard) and decide on a mitigation.
  8. *Wrap up*: bottlenecks left, failure modes, observability, rollout and rollback, what changes at 10× load.
- For a real-time pipeline system (such as this repo's voice translator), the optional "data flow" step is the *main* step: the pipeline stage list plus a per-stage latency budget is the design. This follows from Hello Interview's guidance to use data flow for long sequential processing and DDIA's advice to break latency down by stage.
- Interview frameworks under-weight operations, migration and cost. Real design docs (section 3) add those back.

### Gaps
- Could not retrieve DDIA's primary text; exact Kleppmann wording (e.g. the reliability definition sentence) is unverified. The 2nd edition's publication date and chapter layout are also unverified [VERIFY].
- Alex Xu's book text was read via ByteByteGo's online chapter, not the print edition; wording may differ slightly.

---

## 2. Reasoning about trade-offs and "start simple" heuristics

### Takeaway
Experts name the trade-off explicitly ("we choose X, so we give up Y"), base it on the stated non-functional requirements, and default to the simplest, most familiar option that meets them: a modular monolith, synchronous calls, a relational DB and boring, well-understood tech. They add complexity only when a measured need forces it. Gall's law, YAGNI, Monolith First, Microservice Premium and Choose Boring Technology are all versions of the same rule.

### Cited Findings
**Consistency vs availability**
- CAP: in a partition, choose consistency (CP: requests may time out/error) or availability (AP: possibly stale data, reconciled later). Choose CP when the business needs atomic reads/writes; AP when eventual consistency is acceptable. — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Consistency spectrum: weak (best effort; memcached, VoIP, video chat, real-time games), eventual (async replication; DNS, email), strong (sync replication; RDBMS, file systems). — [system-design-primer](https://github.com/donnemartin/system-design-primer)
- Fail-over (active-passive, active-active) adds hardware and complexity and risks data loss if the active node dies before replicating. — [system-design-primer](https://github.com/donnemartin/system-design-primer)

**Monolith vs microservices**
- "you shouldn't start a new project with microservices, even if you're sure your application will be big enough to make it worthwhile." "Almost all the successful microservice stories have started with a monolith that got too big and was broken up"; greenfield microservice systems often "ended up in serious trouble." (Fowler, 3 Jun 2015) — [Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)
- Reason: microservices need stable boundaries (bounded contexts), which are hard to get right up front, and refactoring across services is much harder than inside a monolith. "By building a monolith first, you can figure out what the right boundaries are." — [Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)
- Strategies: a carefully modular monolith (modular APIs *and* data storage) split later; peel services off the edges; sacrificial architecture ("Don't be afraid of building a monolith that you will discard"); start with a few coarse services. Fowler also records the counter-view: start with microservices only if the team has real experience with them. He calls his own conclusion tentative. — [Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)
- "don't even consider microservices unless you have a system that's too complex to manage as a monolith"; "The majority of software systems should be built as a single monolithic application." The premium: automated deployment, monitoring, failure handling, eventual consistency. Quotes Kent Beck: any decent answer "begins, 'it depends…'" (13 May 2015). — [Fowler, MicroservicePremium](https://martinfowler.com/bliki/MicroservicePremium.html)

**Boring technology / build vs buy / adding tech**
- "Innovation tokens": a company gets "maybe three" early on; spend them on what differentiates the business. New tech brings more known unknowns and unknown unknowns (e.g. months chasing GC pauses caused by writing stats to a file). — [McKinley, Choose Boring Technology](https://boringtechnology.club/)
- "Adding the technology is easy, living with it is hard." Adding tech is a team decision. Before adding anything, ask "how would we solve the problem at hand without adding anything new?", list the workarounds, compare their cost with operating something new, roll out gradually, and retire the old tool if it is being replaced. "Happiness comes from shipping stuff." — [McKinley, Choose Boring Technology](https://boringtechnology.club/)
- Alex Xu's step 1 asks what existing services can be reused, a build-vs-reuse check up front. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)

**YAGNI**
- YAGNI: "some capability we presume our software needs in the future should not be built now." Four costs of a presumptive feature: cost of build, cost of delay, cost of carry (complexity slows everything else), cost of repair (if built wrong). (Fowler, 26 May 2015) — [Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)
- Limit: "Yagni only applies to capabilities built into the software to support a presumptive feature, it does not apply to effort to make the software easier to modify." Refactoring, self-testing code and CD are not YAGNI violations; "Yagni is not a justification for neglecting the health of your code base." — [Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)

**Gall's law**
- "A complex system that works is invariably found to have evolved from a simple system that worked. A complex system designed from scratch never works and cannot be patched up to make it work. You have to start over with a working simple system." John Gall, *Systemantics* (1975). — [Matt Rickard](https://blog.matt-rickard.com/p/galls-law); [Laws of Software Engineering](https://lawsofsoftwareengineering.com/laws/galls-law/)
- It does not claim simplicity guarantees success; it claims working complex systems come from working simple ones. — [Andy Matuschak notes](https://notes.andymatuschak.org/z4GDrXLY7RaUDcvZLim3mfA)

**Complexity budget (Ousterhout, via book notes)**
- Complexity shows up as change amplification, cognitive load and unknown unknowns; it is caused by dependencies and obscurity, and it accumulates incrementally. — [sive.rs summary](https://sive.rs/book/PoSD); [Dan Lebrero notes](https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/)
- Deep modules (simple interface, lots of functionality) beat shallow ones; "classitis" (many tiny classes) raises system complexity. — [sive.rs summary](https://sive.rs/book/PoSD); [freshman.tech summary](https://freshman.tech/philosophy-of-software-design-summary)

**Over-engineering**
- Over-engineering is "a real disease of many engineers": favouring design purity, ignoring trade-offs, underestimating the compounding cost of complexity. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)

### Inferences
- **Trade-off reasoning template** (use in a design doc or ADR):
  `Requirement it serves -> Options (≥2, including "do nothing / use what we have") -> what each costs (latency, $, ops burden, team familiarity, reversibility) -> chosen option -> what we explicitly give up -> trigger that would make us revisit.`
- **Default choices unless a requirement forces otherwise:**
  - Monolith (modular inside; clear module boundaries and separate data ownership per module) over microservices.
  - Synchronous request/response over queues; add async when work is slow, bursty, retryable or must outlive the request. Async buys decoupling and smoothing at the cost of eventual consistency and harder debugging (this follows from the consistency patterns and the Microservice Premium costs above).
  - One relational database (Postgres) over polyglot persistence.
  - Buy or reuse for non-differentiating parts (auth, email, media servers); build what differentiates you. Each new runtime dependency spends an innovation token.
  - Vertical scaling first (simpler to operate, per DDIA notes), horizontal when a load parameter says so.
  - Latency vs cost: set the latency target as a percentile (p50/p95) first, then buy only the hardware or complexity needed to hit it.
- **One-way vs two-way doors:** Fowler's "reevaluation triggers" and McKinley's "retire the old tool" both suggest separating hard-to-reverse decisions (data model, public API, licence, vendor lock-in), which deserve docs and spikes, from easy-to-reverse ones, which should just be made quickly. (Often credited to Amazon/Bezos; not sourced here, see Gaps.)
- Ousterhout's "deep modules" is the code-level version of a modular monolith: a few components with small, stable interfaces hiding lots of work.

### Gaps
- No primary source fetched for sync vs async trade-offs, PACELC (the latency-vs-consistency extension of CAP), or Amazon's "one-way/two-way door" framing; these are well known but uncited here.
- The counter-argument on Fowler's site ("Don't start with a monolith") is believed to be Stefan Tilkov's 2015 guest article; not fetched [VERIFY].
- Ousterhout material is from secondary summaries; exact book wording unverified.

---

## 3. How design docs / RFCs are written (Google, Uber, others)

### Takeaway
A design doc is a short, informal, trade-off-focused document written before coding and reviewed by the people who will be affected. Its core sections are Context & Scope, Goals & Non-goals, Design (overview, then detail, with a context diagram, APIs and data storage), Alternatives Considered, Cross-cutting concerns (security, privacy, observability) and Rollout/Testing. Keep it short (1–3 pages for small work, 10–20 for large), name the approvers, and update or amend it when reality changes.

### Cited Findings
**Google (Malte Ubl, "Design Docs at Google")**
- Design docs are "relatively informal documents that the primary author or authors of a software system or application create before they embark on the coding project," documenting high-level strategy and key decisions "with an emphasis on the trade-offs." "As software engineers our job is not to produce code per se, but rather to solve problems." — [Ubl, industrialempathy.com](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Benefits: catch design issues early when change is cheap, build consensus, ensure cross-cutting concerns, spread senior knowledge, create organisational memory. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- "Rule #1 is: Write them in whatever form makes the most sense for the particular project." Typical sections:
  - *Context and scope*: brief, objective background; not a requirements doc.
  - *Goals and non-goals*: non-goals are things that could reasonably be goals but are deliberately excluded (example: "ACID compliance" as a non-goal for a database), not negations of goals.
  - *The actual design*: overview then details; focus on trade-offs and why this design best meets the goals.
  - *System-context diagram*.
  - *APIs*: sketch only the parts relevant to the design and its trade-offs; don't paste formal interface definitions.
  - *Data storage*: how and in roughly what form; trade-offs, not full schemas.
  - *Code/pseudo-code*: rarely; link to prototypes instead.
  - *Degree of constraint*: greenfield (wide solution space, needs narrowing) vs heavily constrained (legacy/host-language) designs.
  - *Alternatives considered*: "one of the most important sections"; other reasonable designs and why they were rejected; can be brief.
  - *Cross-cutting concerns*: security, privacy, observability. Google requires a separate privacy design doc and has privacy/security reviews. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Length: 10–20 pages for larger projects (split if longer); 1–3 page "mini design docs" for incremental work. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Lifecycle: create and iterate with co-authors -> review (from a mailing-list comment thread to a formal senior-engineer meeting; don't block on formal review, seek critical feedback directly) -> implement and update the doc as shortcomings are found (link amendments from the original) -> maintenance: re-read a year or two later to see what was right and wrong. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- When **not** to write one: the solution is unambiguous; the doc would be an implementation manual without trade-offs or alternatives; rapid prototyping is the point. Write one if you answer yes to ~3+ of: unsure of the right design? want senior input? ambiguous or contentious? team tends to forget privacy/security/logging? need docs for a legacy system? — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)

**Uber (Gergely Orosz, The Pragmatic Engineer, 2018)**
- RFCs fixed poor visibility across teams and inconsistent architecture. Writing creates accountability, surfaces disagreements and edge cases early, and spreads knowledge. — [Orosz](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)
- Process: plan (whiteboard) -> short written doc -> a few named approvers (senior engineers or consumers of the feature) sign off in writing -> distribute to all engineers for comment -> apply to anything beyond trivial complexity. "Don't go overboard." Later scaled with domain mailing lists (backend, mobile, web) and approval tooling. — [Orosz](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)
- Uber backend template: approvers, abstract, architecture changes, service SLAs, service dependencies, load and performance testing, multi-datacenter concerns, security, testing and rollout, metrics and monitoring, customer support considerations. Mobile/web template adds UI/UX, network interactions, library dependencies, analytics and accessibility. Templates grew from questions reviewers kept asking. — [Orosz](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)
- "The type of information pushed to people in an organization shapes the culture considerably." Uber's open-source BaseUI publishes RFCs in its repo and starts development only after approval. — [Orosz](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)

### Inferences
- **Design doc template (merged Google + Uber; 1–5 pages for a solo or small-team project):**
  ```
  # <Title>  · Status: Draft | In review | Approved | Implemented | Superseded · Author · Date · Approvers
  1. Context & scope        – what exists, what problem, why now (facts only)
  2. Goals                  – measurable outcomes (incl. NFR targets: p50/p95 latency, availability, cost)
     Non-goals              – reasonable things we are deliberately NOT doing
  3. Proposed design
     3.1 Overview + system-context diagram (C4 L1) + container diagram (C4 L2)
     3.2 Data flow / sequence diagram for the main path and the main failure path
     3.3 APIs / interfaces (only the decision-relevant parts)
     3.4 Data model & storage (source of truth, retention)
     3.5 Capacity estimate (only numbers that drive decisions)
  4. Alternatives considered – each: summary, pros, cons, why rejected
  5. Cross-cutting concerns  – security, privacy, observability (metrics/logs/traces), cost, licences
  6. Risks & open questions  – ranked; how each will be de-risked (spike/prototype/benchmark)
  7. Testing, rollout & rollback plan; migration if any
  8. Milestones              – thin end-to-end slice first
  Appendix: links to spikes, benchmarks, ADRs
  ```
- **Review checklist for the reader:** Are non-goals stated? Is each NFR a number? Is there at least one real alternative? Is the riskiest assumption named, with a plan to test it? Does a request trace end to end? What happens when each box fails? Can it be rolled back? What does it cost per month?
- Practical rule: write the doc *after* a quick whiteboard or spike but *before* committing to irreversible choices. Keep it a living document until shipped, then freeze it and record later changes as ADRs or amendments.

### Gaps
- No primary public source found for **Stripe's** design-doc/RFC template in this pass; claims about Stripe's process are therefore omitted.
- Current (2026) practice details, such as AI-assisted drafting or review of design docs and RFC tooling, were not researched; no reliable source collected.

---

## 4. Architecture Decision Records (Nygard format) and how they are used

### Takeaway
An ADR is a 1–2 page Markdown file in the repo that records **one** significant decision: Title, Status, Context (forces), Decision ("We will…"), Consequences (good, bad and neutral). ADRs are numbered sequentially, never edited after acceptance, and superseded by newer ADRs. They complement design docs: the doc proposes a whole design, and ADRs keep the trail of individual decisions over time.

### Cited Findings
- Nygard (2011) format: **Title** (short noun phrase, e.g. "ADR 9: LDAP for Multitenant Integration"); **Context** (forces: technological, political, social, project-local; value-neutral, facts only); **Decision** (full sentences, active voice, "We will…"); **Status** (proposed, accepted, deprecated, superseded with a link); **Consequences** (resulting context: positive, negative, neutral). — [Nygard, cognitect.com](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- Stored in the repo (`doc/arch/adr-NNN.md`), lightweight markup, numbered sequentially and never reused. "If a decision is reversed, we will keep the old one around, but mark it as superseded." One or two pages; write "as if it is a conversation with a future developer," in full sentences (bullets only for layout). — [Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- Rationale: big documents go stale, small modular records are maintained; newcomers otherwise either blindly accept or blindly reverse past decisions. "It's better to avoid either blind acceptance or blind reversal." 6–10 developers rotating through projects all found the context helpful. — [Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- Fowler (bliki, dated 24 Mar 2026): an ADR "captures and explains a single decision"; about a page; store in `doc/adr` as Markdown so it can be diffed; filenames like `0001-HTMX-for-active-web-pages`. Status: proposed -> accepted (not reopened) -> superseded (link to replacement). Contents: rationale as "forces", serious alternatives with pros and cons, consequences, **confidence level**, **reevaluation triggers**, and advice gathered (when used with the "advice process"). Inverted-pyramid style, most important first. Writing one "forces clarity" and surfaces disagreement. Caveat: repos suit single-codebase decisions less well for ecosystem-wide ones, and git can be a barrier for non-developers. — [Fowler, ArchitectureDecisionRecord](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)
- Definitions: an Architectural Decision is "a justified design choice" addressing an architecturally significant requirement (ASR = a requirement that measurably affects the architecture). An ADR "captures a single AD and its rationale." Templates include Nygard's and the Y-statement (Zdun et al., "Sustainable Architectural Decisions"); a WICSA 2015 paper compares seven templates. — [adr.github.io](https://adr.github.io/)

### Inferences
- **ADR template (Nygard + Fowler 2026 additions):**
  ```
  # NNNN. <Decision as noun phrase>
  Date: YYYY-MM-DD   Status: Proposed | Accepted | Superseded by NNNN
  ## Context        – forces in tension, constraints, the requirement it serves (facts)
  ## Options        – 2–4 serious options, one line of pros/cons each
  ## Decision       – "We will …" (one paragraph)
  ## Consequences   – positive / negative / neutral; what becomes easier or harder
  ## Confidence     – high / medium / low and why
  ## Revisit if     – measurable triggers (e.g. "p95 > 2 s on target hardware", "licence changes")
  ```
- Y-statement one-liner (commonly given form; structure not shown on the fetched page): "In the context of <use case>, facing <concern>, we decided for <option> and neglected <other options>, to achieve <quality>, accepting <downside>."
- **When to write an ADR:** the decision is hard to reverse, affects more than one module, was contested, or someone will later ask "why on earth did we do this?" Don't write one for choices that are easy to reverse or local to one file.
- Design doc vs ADR: the design doc covers the whole proposal at a point in time; ADRs are the running decision log that survives after the doc goes stale. This repo already uses this pattern (`docs/plan.md` plus `docs/adr/` plus a decision log in CLAUDE.md).

### Gaps
- The adr.github.io landing page did not list tools (adr-tools, log4brains) or the MADR template's sections; these exist but were not verified in this pass.

---

## 5. Diagrams: the C4 model and sequence diagrams

### Takeaway
Use C4 "maps at different zoom levels": a **System Context** diagram (your system as one box, plus users and external systems) and a **Container** diagram (each runnable or deployable unit and data store, with protocols on the arrows) are enough for most teams. Add **dynamic/sequence** diagrams for the critical request path and failure path, and a **deployment** diagram when infrastructure matters.

### Cited Findings
- C4 is "an easy to learn, developer friendly approach to software architecture diagramming," with hierarchical abstractions (software system -> containers -> components -> code) and matching diagrams, plus supplementary system-landscape, dynamic and deployment diagrams. It does not depend on any notation or tool. — [c4model.com](https://c4model.com/)
- "The different levels of zoom allow you to tell different stories to different audiences"; "you don't need to use all 4 levels of diagram; only those that add value"; "the system context and container diagrams are sufficient for most software development teams." — [c4model.com/diagrams](https://c4model.com/diagrams)
- A container is "Not Docker!": it "represents an application or a data store," "something that needs to be running in order for the overall software system to work," "essentially a runtime boundary around some code that is being executed or some data that is being stored." Examples: server-side web app, browser SPA, mobile app, serverless function, database schema, S3 bucket/CDN, file system, shell script. — [c4model.com/abstractions/container](https://c4model.com/abstractions/container)
- Google design docs include a system-context diagram so readers can place the new system in its landscape. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Interview frameworks use box diagrams for the high-level design and walk concrete use cases through them to reveal edge cases. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)

### Inferences
- **Diagram checklist:** every box has a name, a type/technology and a one-line responsibility; every arrow has a direction, a verb ("sends audio frames") and a protocol (WebRTC, HTTP/JSON, gRPC); include a legend; one diagram per question it answers.
- **Sequence diagrams** are the best tool for latency budgets and race conditions: draw lifelines for each container and annotate each hop with a time budget. Draw the happy path and one failure path (timeout, reconnect).
- Diagrams-as-code (Mermaid, PlantUML, Structurizr DSL) keep diagrams in the repo next to ADRs and diffable. This is common current practice; Mermaid renders natively in GitHub Markdown. (General knowledge, not from a fetched source.)

### Gaps
- The c4model.com subpages fetched did not give per-level audience descriptions or notation rules in full; system context and component definitions were not retrieved.

---

## 6. Identifying and de-risking the riskiest part early (spikes, prototypes, PoCs, tracer bullets)

### Takeaway
Rank assumptions by "how likely to be wrong × how expensive if wrong", then attack the top one first with the cheapest experiment that could falsify it: a throwaway **spike** or prototype to answer one question, or a **tracer bullet** (a thin end-to-end skeleton you keep) to prove the components connect. Put the results back into the design doc or an ADR.

### Cited Findings
- XP spike: "a very simple program to explore potential solutions," addressing only the problem under study; most spikes are not good enough to keep, so expect to throw them away. Goal: reduce technical risk or make an estimate more reliable. — [XP rules: spike](https://person.dibris.unige.it/reggio-gianna/ISII03WWW/ExtremeProgramming/rules/spike.html)
- Pragmatic Programmer: a prototype's value lies "not in the code produced, but in the lessons learned"; prototypes are disposable and can be non-code. Tracer code is "lean but complete" and forms part of the skeleton of the final system. Prototyping is the reconnaissance before the first tracer bullet is fired. — [Goodreads notes on The Pragmatic Programmer](https://www.goodreads.com/notes/8214124-the-pragmatic-programmer/25024972-v-t-kota-ka); [Builtin, tracer bullets](https://builtin.com/software-engineering-perspectives/what-are-tracer-bullets)
- Some practitioners describe tracer bullets as also disposable, so the keep-or-discard line is not universal. — [Builtin, tracer bullets](https://builtin.com/software-engineering-perspectives/what-are-tracer-bullets)
- Google design docs: link to prototypes that show feasibility rather than include code; "a prototype can itself support a design decision"; the top reason to write a doc is being unsure of the right design. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Gall's law implies starting from a *working* simple system and growing it. — [Laws of Software Engineering](https://lawsofsoftwareengineering.com/laws/galls-law/)
- McKinley: new tech carries unknown unknowns, so the riskiest part is often the unfamiliar technology itself; roll it out in small steps. — [McKinley](https://boringtechnology.club/)
- Fowler: record the **confidence level** and **reevaluation triggers** in ADRs, since decisions are made under uncertainty. — [Fowler, ADR](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)

### Inferences
- **De-risking procedure:**
  1. List every assumption the design depends on (performance, model or library quality, third-party behaviour, licence, cost, user behaviour).
  2. Score each one by likelihood it is wrong × cost if wrong (H/M/L). Irreversible items rank higher.
  3. For the top 1–3, write a falsifiable question with a pass/fail threshold: "Can component X do Y within Z ms p95 on hardware H?"
  4. Time-box a spike (hours to a few days), on real data where possible, and throw away the code.
  5. Build the tracer bullet: the thinnest end-to-end path through every container (input -> processing -> output, logged and measured) before polishing any single stage.
  6. Record the result (numbers, method) in the design doc or an ADR, update confidence, and set revisit triggers.
- Prefer measuring distributions (p50/p95) on a fixed eval set over a single demo run. This follows from DDIA's percentile guidance and matches this repo's CLAUDE.md metric rules.
- Signs a risk was found too late: you are optimising a component before the end-to-end path exists, or the first real-hardware or real-data test happens after the architecture is fixed.

### Gaps
- The Pragmatic Programmer was not read directly; quotes come from reader notes and articles. Wording may vary between the 1999 and 20th-anniversary (2019) editions.
- No quantitative evidence (studies) was found on how much spikes or prototypes reduce project failure; the guidance is practitioner consensus.

---

## 7. Common beginner design mistakes

### Takeaway
The typical failures are solving before scoping, over-engineering (microservices, queues, caches, k8s, multiple databases for hypothetical scale), adopting too many new technologies at once, designing distributed systems before a monolith works, skipping alternatives and non-goals, ignoring operations/failure/security, and treating averages or one-off demos as performance evidence.

### Cited Findings
- Jumping to a solution before clarifying requirements ("Slow down"); diving deep into one component before the high-level design exists; staying silent; claiming the design is flawless. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Over-engineering is "a real disease of many engineers": design purity over trade-offs, underestimating compounding complexity costs. — [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)
- Too many requirements: "Having a long list of requirements will hurt you more than it will help you"; doing estimates that don't change the design. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Microservices first: greenfield microservice systems often "ended up in serious trouble"; boundaries are unknown at the start. — [Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html); premium costs (deployment automation, monitoring, failure handling, eventual consistency) slow development. — [Fowler, MicroservicePremium](https://martinfowler.com/bliki/MicroservicePremium.html)
- Premature, presumptive features carry build, delay, carry and repair costs. — [Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)
- Too much new tech: spending more than ~3 innovation tokens; individual engineers choosing tech with company-wide effects. — [McKinley](https://boringtechnology.club/)
- Designing a complex system from scratch "never works and cannot be patched up to make it work." — [Gall's law](https://blog.matt-rickard.com/p/galls-law)
- Shallow modules and classitis: many tiny classes with interfaces as complex as their bodies increase total complexity. — [sive.rs summary](https://sive.rs/book/PoSD)
- Using averages instead of percentiles hides tail latency; unproven products should not optimise for hypothetical future load. — [candost.blog DDIA notes](https://candost.blog/books/reliability-maintainability-and-scalability-in-applications)
- Design docs that are only implementation manuals (no trade-offs or alternatives) add overhead without value. — [Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Taking user identity from request bodies instead of auth tokens. — [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- Not recording why decisions were made, which leads to "blind acceptance or blind reversal" later. — [Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

### Inferences
- **"Am I over-engineering?" self-check:**
  - Can I name the requirement (with a number) that forces this component? If not, remove it.
  - Would a single process plus Postgres meet the next 12 months of expected load?
  - How many technologies here has the team never run in production? (Keep it ≤3.)
  - Is there a working end-to-end slice yet? If not, stop adding parts.
  - Is the boundary between these two services already stable? If not, keep them as modules.
  - Have I written the alternatives and non-goals?
  - What happens when each box is down, and how do I find out (metrics/logs)?
- **Beginner-to-expert shift:** beginners design for scale they don't have and skip the risks they do have. Experts design for the stated load, find the single riskiest unknown, test it first, and write down why.

### Gaps
- No empirical survey data located on the frequency of these mistakes; the list reflects practitioner consensus from the cited authors.
