# How Engineers Turn Ideas Into Working Systems

Experienced engineers do not start with code. They run one loop, again and again. First they understand the problem and write down what "success" means as numbers. They estimate only the numbers that change a decision. They choose the simplest design that meets those numbers and write the important decisions down. Then they build a very thin version that works from start to end (a "walking skeleton"), and grow it one small, testable slice at a time. They measure every change on a fixed test set and decide the next step from the results, not from feelings. The same pattern appears in Google's design-doc practice, Amazon's "working backwards" process, Uber's RFCs, Martin Fowler's writing and every major system-design framework. Most of the evidence is practitioner experience, not controlled experiments, so treat it as strong advice, not proven law. A self-taught developer can learn this process. Skill grows from the number of feedback loops you close (a test that fails, a design you compare with a real one, a review of your code), not from hours spent. Plan for about two years of steady practice to become solid ([Norvig](https://norvig.com/21-days.html)). Use AI assistants as a tutor and a reviewer, not a ghostwriter: in a 2026 randomised trial, learners who handed code-writing to AI scored 17 points lower on a skills quiz, with the biggest gap in debugging ([Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills)). Your live-translator project in this repo already follows this loop, so this report uses it as the running example.

## Words used in this report

Many terms come up again and again. Here they are in plain words. Each one is also explained when it first appears.

| Term | Plain meaning |
|---|---|
| Functional requirement | What the system must **do**. "A user can start a call and share a link." |
| Non-functional requirement (NFR) | **How well** it must do it. "First translated audio arrives within 2 s." |
| Non-goal | Something people might expect, but you have **decided not to build** now. |
| Latency | Waiting time. How long one action takes. |
| p50 / p95 / p99 (percentiles) | p50 = half of all requests are faster than this. p95 = 95 out of 100 are faster. It shows the slow cases that an average hides. |
| QPS | Queries (requests) per second. |
| MVP | Minimum viable product. The smallest version that is really useful. |
| Spike / prototype | Quick throwaway code that answers **one** question. You delete it after. |
| Walking skeleton / tracer bullet | The thinnest version that runs end to end through every part. You **keep** it and grow it. |
| Vertical slice | A small piece of work that goes through every layer and gives something a user can see. |
| Design doc / RFC | A short document written before coding. It explains the plan and its trade-offs. |
| ADR | Architecture Decision Record. One short file that records **one** important decision and why. |
| Refactor | Change the structure of code without changing what it does. |
| TDD | Test-driven development. Write a failing test, make it pass, then clean up. |
| CI | Continuous integration. Tests run automatically on every push. |
| Eval set | A fixed set of test cases you run after every important change, so results can be compared. |
| Regression test | A test that stops an old bug from coming back. |

In the translator example: **VAD** (voice activity detection) finds when someone is speaking. **ASR** (automatic speech recognition) turns speech into text. **MT** (machine translation) translates text. **TTS** (text-to-speech) turns text back into speech. **SE2FA** is your main speed metric: the time from when a speaker stops talking to when the listener hears the first translated audio. **WER** (word error rate) is the percentage of words the ASR gets wrong.

## One loop of nine steps runs every serious project

Here is the whole process on one page. The rest of the report explains each step, gives a checklist, and shows how the translator project did it.

| Step | Question it answers | Main output |
|---|---|---|
| 1. Understand | Who is it for, what must it do, how well, and what are we not doing? | Problem statement, 3 core requirements, 3–5 numeric targets, non-goals, risk list |
| 2. Estimate | Do the numbers change the design? | A few back-of-the-envelope numbers or a latency budget |
| 3. Design | What is the simplest design that meets the targets? | Boxes-and-arrows diagram, data flow, trade-offs, spikes on the riskiest part |
| 4. Write it down | Can someone else (or future me) understand and challenge it? | A 1–5 page design doc plus ADRs |
| 5. Walking skeleton | Do all the parts connect? | A thin end-to-end path that runs with one command |
| 6. Vertical slices | What is the next small thing a user can see? | Small, demoable changes, one at a time |
| 7. Test, refactor, debug | Is it correct and clean? | Passing tests, clean code, root-caused bugs |
| 8. Measure | Is it actually better? | p50/p95 numbers and error rates on a fixed eval set |
| 9. Repeat | What should I do next? | Next slice chosen by biggest risk or value; docs updated |

Why does this order work? The best short answer is **Gall's law**: "A complex system that works is invariably found to have evolved from a simple system that worked. A complex system designed from scratch never works and cannot be patched up to make it work" ([Matt Rickard](https://blog.matt-rickard.com/p/galls-law)). Note what the law does **not** say. It does not promise that simple systems succeed. It says working complex systems grow from working simple ones ([Andy Matuschak](https://notes.andymatuschak.org/z4GDrXLY7RaUDcvZLim3mfA)). The second reason is feedback. Dave Thomas, co-author of *The Pragmatic Programmer*, says: "Basically, it all comes down to feedback." The sooner you get feedback, the less you have to correct ([Artima interview](https://www.artima.com/articles/tracer-bullets-and-prototypes)). Every step in the loop exists to get feedback earlier and more cheaply.

The steps are not a strict waterfall. You will jump back. A spike in step 3 can change a requirement in step 1. A measurement in step 8 can change the design. That is normal and good.

## Steps 1–2: experts define success in numbers before choosing any technology

### Step 1. Understand the problem

Experts start from the customer and the problem, not from the solution or the tech stack. Amazon's "working backwards" process asks the team to write a one-page **press release** for the finished product before building anything. It names the customer, the problem from the customer's view, and why this solution is better than others. An internal FAQ then lists hard questions, including the "top three reasons the product could fail." A first draft should take "a few hours, not a few days," so weak ideas die cheaply ([Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)). The cautionary example is the Fire Phone, whose 3D feature "didn't solve any important problems for customers" (same source).

Next, describe the main situations. A **job story** uses the format "When ___, I want to ___, so I can ___" ([Intercom](https://www.intercom.com/blog/accidentally-invented-job-stories/)). A user story uses "As a [who] I want [what] so that [why]" ([Martin Fowler](https://martinfowler.com/bliki/UserStory.html)). Job stories suit products where the situation matters more than the person's role.

Then split requirements into two kinds. **Functional requirements** say what the system does: "Users should be able to…". **Non-functional requirements** say how well: "The system should be…". Keep only the top 3 functional and the top 3–5 non-functional ones. "Having a long list of requirements will hurt you more than it will help you" ([Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)). Every non-functional requirement needs a number. "Fast" is not a requirement. "p95 under 2 seconds" is. Use percentiles, not averages, because averages hide the slow cases; Amazon sets internal targets at the 99.9th percentile ([DDIA notes, Bill Mill](https://notes.billmill.org/book_notes/Designing_Data-Intensive_Applications/Chapter_2_-_defining_nonfunctional_requirements.html)).

Write **non-goals** too. A non-goal is something that "could reasonably be" a goal but you deliberately exclude. It is not a negative goal like "the system shouldn't crash" ([Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)).

Finally, list your **riskiest assumptions**. Marty Cagan names four big risks: **value** (will people use it?), **usability** (can they figure it out?), **feasibility** (can we build it with our time, skills and technology?) and **viability** (does it work as a business, legally and financially?). Strong teams "tackle the big risks early" ([SVPG](https://www.svpg.com/four-big-risks/)). Rank each assumption by "how bad if wrong" × "how unsure am I". The top one or two become your first experiments.

If nobody is there to answer your questions, write both the questions and your assumed answers. The system-design frameworks open with the same questions: who uses it, how many users, what goes in and out, how much data, how many requests per second, what is the read-to-write ratio, and how fast it will grow ([system-design-primer](https://github.com/donnemartin/system-design-primer); [ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews)).

**Checklist, step 1**
- [ ] One paragraph: who is the user, what is their problem, why now?
- [ ] 3–5 job stories ("When…, I want to…, so I can…").
- [ ] Top 3 functional requirements.
- [ ] 3–5 non-functional requirements, each with a number and a percentile.
- [ ] Constraints: budget, hardware, deadline, licences, laws, skills.
- [ ] Non-goals list.
- [ ] Top 3 reasons this could fail, ranked by risk.

**Translator example.** The plan names real people: traders, families, workers. It defines success concretely: a Telugu shopkeeper and a Mandarin-speaking buyer agree price, quantity and delivery date "with every number correct" and without touching the screen after joining ([plan §1.4](../docs/plan.md)). Functional requirements are numbered FR-1 to FR-11. Numeric targets include SE2FA p50 ≤ 1.2 s on the server and ≤ 2.0 s on the Mac, and a critical-error rate (wrong number, negation, name or date) of ≤ 1% ([plan §2.8, §3.2](../docs/plan.md)). Non-goals for v1 include phone-number calling, voice cloning, group calls of more than two, video and automatic language detection ([plan §2.9](../docs/plan.md)). Hard constraints are written down as rules: open-source licences only, no raw audio stored, no transcript text in logs, Bun for JavaScript and uv for Python. The risk list is explicit too: Telugu speech recognition is risk #1 and Telugu TTS is risk #2.

### Step 2. Estimate only what changes a decision

Estimation answers one question: does this number change the design? One machine or many? Cache or no cache? "Perform calculations only if they will directly influence your design" ([Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)).

A simple recipe works for most web systems. Daily users × actions per user = actions per day. Divide by about 100,000 seconds in a day to get average requests per second. Multiply by a peak factor (state your guess, such as 5×). Item size × items per day × days kept = storage. Useful rules: one month is about 2.5 million seconds, so 40 requests per second is about 100 million per month ([system-design-primer, Pastebin](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md)). The Pastebin example works out 10 million new pastes a month at about 1.27 KB each, which is about 12.7 GB a month and about 450 GB over three years, with about 4 writes and 40 reads per second (same source). That tells you one database server is enough.

Learn a few "latency numbers" by heart, as rough sizes, not exact facts: main memory about 100 ns, a round trip inside a data centre about 0.5 ms, reading 1 MB from an SSD about 1 ms, a packet from California to the Netherlands and back about 150 ms ([system-design-primer](https://github.com/donnemartin/system-design-primer)). These numbers are old and newer estimates differ, so use them only for order of magnitude ([HighScalability](https://highscalability.com/more-numbers-every-awesome-programmer-must-know/)).

Also do the availability maths. Parts that run one after another multiply: two services at 99.9% give 99.8% ([system-design-primer](https://github.com/donnemartin/system-design-primer)). By the same maths, a chain of five such services gives only about 99.5%.

For real-time systems the most important estimate is a **latency budget**. Add up the time of each stage on the critical path and compare it with your p95 target. This matters more than requests per second.

**Checklist, step 2**
- [ ] Which decision does each estimate inform? If none, skip it.
- [ ] Requests per second (average and peak), storage per year, bandwidth.
- [ ] For real-time work: a time budget for each stage that adds up to the target.
- [ ] Memory and hardware budget.
- [ ] Write every guess down as an assumption.

**Translator example.** Two people in one call means requests-per-second maths changes nothing. The real limits are time and memory. The plan gives each stage a deadline. If a request would miss it, the system picks a lighter route instead of waiting in a queue ([plan §5.14](../docs/plan.md)). The memory budget for the AI models on the 16 GB Mac is 9 GB. Measured stage times then fill the budget: IndicConformer ASR about 70–100 ms per sentence, Piper Telugu TTS about 0.09 s, Kokoro TTS about 0.6–0.7 s ([ADR-019, ADR-024](../docs/adr/0017-local-dev-and-mvp-decisions.md)). The slowest step is Mandarin ASR at about 0.9 s, so that is where the next improvement must come from ([ADR-029](../docs/adr/0017-local-dev-and-mvp-decisions.md)).

## Steps 3–4: the simplest design that meets the numbers, written down with its reasons

### Step 3. Design

All major frameworks follow the same order. Name the main things in the system (entities). Define the interface (API). Draw boxes and arrows. Walk one real request through it from start to end, then one failure. Only then go deep, and only where a non-functional requirement is under threat ([ByteByteGo](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews); [Hello Interview](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)). Walking through a concrete use case "often reveals edge cases" (ByteByteGo).

Draw two pictures from the **C4 model**. A *context* diagram shows your system as one box with its users and outside systems. A *container* diagram shows every running program and data store. Here "container" means "an application or a data store," not Docker. "The system context and container diagrams are sufficient for most software development teams" ([c4model.com](https://c4model.com/diagrams)). For a pipeline, add a **sequence diagram** with a time budget on every arrow.

Choose boring, simple options unless a measured number forces you to do more. Martin Fowler advises against starting a new project with microservices (many small separate services), because "almost all the successful microservice stories have started with a monolith that got too big and was broken up" ([Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)). A monolith is one program with clear modules inside it. Dan McKinley says each team gets "maybe three" **innovation tokens**: spend new, unfamiliar technology only on what makes your product special. Before adding a tool, ask "how would we solve the problem at hand without adding anything new?" ([Choose Boring Technology](https://boringtechnology.club/)). **YAGNI** ("you aren't gonna need it") says do not build features for an imagined future, because they cost time to build, delay other work, make the code harder to carry, and may be wrong. But YAGNI never excuses messy code: refactoring and tests are not YAGNI violations ([Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)).

Name every trade-off in one line: "We choose X, so we give up Y, and we will revisit if Z happens." Always compare at least two options, including "do nothing" or "use what we have."

Then attack the riskiest unknown with a **spike**: "a very simple program to explore potential solutions" that you expect to throw away ([XP rules](https://person.dibris.unige.it/reggio-gianna/ISII03WWW/ExtremeProgramming/rules/spike.html)). Write the question as a pass/fail test: "Can model X transcribe these 10 sentences in under 1 s each on my laptop, with no wrong numbers?" Time-box it to hours or a few days. A prototype's value lies "not in the code produced, but in the lessons learned" (*The Pragmatic Programmer*, via [Goodreads notes](https://www.goodreads.com/notes/8214124-the-pragmatic-programmer/25024972-v-t-kota-ka)).

**Checklist, step 3**
- [ ] Main entities (nouns) and who owns each piece of data.
- [ ] The external API and the main internal interfaces.
- [ ] Context and container diagrams; label each arrow with what it sends and the protocol.
- [ ] One request traced end to end, plus one failure path.
- [ ] For each numeric target: which box threatens it, and what is the plan?
- [ ] Every new technology justified by a requirement; no more than about three new ones.
- [ ] A time-boxed spike on the riskiest assumption, with a pass/fail number.

**Translator example.** The design is a pipeline: VAD → turn detection → streaming ASR → sentence segmenter → mask numbers and names → choose a route for the language pair → MT → quality checks → TTS → ordered playback. Two of its principles are worth copying: keep the media path separate from the AI path, so the call never waits on a model, and put every engine (ASR, MT, TTS) behind a stable interface so it can be swapped ([plan §4.1](../docs/plan.md)). The boring choices are recorded: no Docker locally ([ADR-017](../docs/adr/0017-local-dev-and-mvp-decisions.md)), no vector database because nothing needs one yet ([ADR-018](../docs/adr/0017-local-dev-and-mvp-decisions.md)), and, for just two tables, plain SQL with Bun's built-in Postgres client instead of an extra database library (Drizzle) ([ADR-022](../docs/adr/0017-local-dev-and-mvp-decisions.md)). Mandarin ASR got a real spike, with numbers:

| Model | Runtime | Mean latency | Errors |
|---|---|---|---|
| whisper-small int8 | CPU | 1.04 s | 2 (dropped a phone digit, 发货→罚货) |
| whisper-large-v3-turbo int8 | CPU | 5.2 s | 0 |
| whisper-large-v3-turbo | Mac GPU (MLX) | 0.96 s | 0 |

Source: [ADR-021](../docs/adr/0017-local-dev-and-mvp-decisions.md). Four test sentences is a small sample, and the ADR says so by leaving a follow-up benchmark open. That is honest spike work.

### Step 4. Write it down

A design doc is a "relatively informal" document written before coding that records the strategy and key decisions "with an emphasis on the trade-offs." Google's "Rule #1" is to write it in whatever form fits the project. Small projects need 1–3 pages; large ones 10–20 ([Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)). The "alternatives considered" section is "one of the most important." Skip the doc when the solution is obvious; a doc that is only an implementation manual adds nothing (same source). At Uber, writing plans down exposed disagreements and missed edge cases early, and a plan that is hard to write was a warning that the project would take longer than expected ([The Pragmatic Engineer](https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/)).

A short template for a solo project:

```
# <Title>   Status · Date
1. Context and scope      what exists, what problem, why now
2. Goals (with numbers)   and Non-goals
3. Design                 diagrams, main data flow, API, data storage, estimates
4. Alternatives           each with why it was rejected
5. Cross-cutting          security, privacy, logging/metrics, cost, licences
6. Risks and open questions, and how each will be tested
7. Testing and rollout
8. Milestones             thin end-to-end slice first
```

An **ADR** records one decision in one or two pages: title, status, context (the facts and forces), decision ("We will…") and consequences, good and bad ([Michael Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)). ADRs are numbered and never edited after they are accepted. If you change your mind, write a new ADR that supersedes the old one. Fowler adds two useful fields: your **confidence level** and **revisit triggers** ([Fowler, ADR](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)). Without this record, later readers either accept or reverse old decisions blindly (Nygard). Write an ADR when a decision is hard to reverse, touches more than one module, or someone will later ask "why did we do this?"

**Checklist, step 4**
- [ ] Design doc of 1–5 pages, including alternatives and non-goals.
- [ ] Every non-functional target in the doc is a number.
- [ ] One ADR per hard-to-reverse decision, with "revisit if…".
- [ ] Ask one person (or a fresh AI session acting only as a critic) to find holes.
- [ ] Update the doc when reality changes; do not let it lie.

**Translator example.** `docs/plan.md` is the design doc, with a section for the active MVP and a build-order table that says what "done" means for each step ([plan §1A.6](../docs/plan.md)). ADR-017 to ADR-030 record decisions as they happened. ADR-026 is a model of the format. *Observed:* the Hindi→Telugu model dropped amounts ("50 रुपये किलो" lost the 50). *Decision:* retry that sentence once through English and keep the retry only if every number survives; otherwise flag the caption "check this number." *Cost:* 300–400 ms, only on the sentences that need it ([ADR-026](../docs/adr/0017-local-dev-and-mvp-decisions.md)). ADR-025 shows a revised decision: the first fix (turning the cache off) was replaced when a better fix made translation 2.3× faster with identical output.

## Steps 5–9: build a thin skeleton first, then grow it one measured slice at a time

### Step 5. Build the walking skeleton

A walking skeleton is "an implementation of the thinnest possible slice of real functionality that we can automatically build, deploy, and test end-to-end" (*Growing Object-Oriented Software*, quoted by [Henrico Dolfing](https://henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html)). Andy Hunt's example is tiny: put one checkbox value into the database as a true/false value, which still touches every layer ([Artima](https://www.artima.com/articles/tracer-bullets-and-prototypes)). Unlike a spike, you keep this code: "A proof of concept (or spike) is meant to be throw away code while the Walking Skeleton is meant to evolve over time" ([Matt Blodgett](https://www.mattblodgett.com/2020/09/start-with-walking-skeleton.html)). Build it early, while requirements are still changing, because then "the code is easiest to change" (Artima).

| | Spike / prototype | Walking skeleton |
|---|---|---|
| Purpose | Answer one question | Prove all parts connect |
| Breadth | One risky piece | Every main part, thinly |
| Code | Thrown away | Kept and grown |

**Checklist, step 5**
- [ ] Pick the most trivial user-visible behaviour that touches every box.
- [ ] Hard-code everything else: one user, fake data, no styling.
- [ ] One command starts it; one end-to-end test checks it.
- [ ] Tests run automatically (CI) on every push.
- [ ] Commit it before polishing anything.

**Translator example.** The first milestone was headless end-to-end calls (real calls through LiveKit and the agent, with recorded speech instead of a person) working in all directions. Single warm runs gave en→te 1.14 s and te→en 2.43 s. Those were explicitly marked "1 run each, not yet p50," which is the right honesty for a skeleton ([CLAUDE.md status](../CLAUDE.md)). The best model was not chosen first. The connected path was.

### Step 6. Grow by vertical slices

Each new piece of work should be a **vertical slice**: a small change through every layer that a user can see and test. Avoid horizontal tasks such as "build the database layer," which deliver nothing until all layers join up ([Humanizing Work](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)). A quick test: if a task names a layer ("write the API") instead of a behaviour ("user can share a call link"), it is probably horizontal. Useful ways to split big work (same source): simplest workflow first, then extra steps; simple data first, then variations; one case first when it carries most of the effort; "make it work" first, then "make it fast"; and a spike only when you truly do not know how. Good slices meet **INVEST**: independent, negotiable, valuable, estimable, small and testable ([Martin Fowler](https://martinfowler.com/bliki/UserStory.html)).

**Checklist, step 6**
- [ ] Each slice is described as a behaviour a user notices.
- [ ] Each slice is small enough to finish in a day or two.
- [ ] Each slice has its own pass/fail check.
- [ ] The system still works end to end after every slice.
- [ ] Never add several new components at once.

**Translator example.** After the skeleton, the work went one weak step at a time. A punctuation model went after Telugu/Hindi ASR, because run-on sentences were turning "50 rupees per kilo" into "50 kilos" ([ADR-027](../docs/adr/0017-local-dev-and-mvp-decisions.md)). A check now fails a translation if a number's unit changes, and only the first long sentence is split at a comma so the first audio comes sooner ([ADR-028](../docs/adr/0017-local-dev-and-mvp-decisions.md)). Each change had one clear reason and one measurement.

### Step 7. The inner loop: test, refactor, debug

**Tests.** TDD is a short loop: list the test cases, write one failing test, write just enough code to pass, then refactor ([Fowler, TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html)). The most common mistake is skipping the refactor step (same source). The research is mixed, and you should know that. A careful study of 39 professionals found that quality and productivity were linked to working in **small, steady steps**, while writing the test first or last "had no important influence" ([Fucci et al., arXiv](https://arxiv.org/abs/1611.05994)). An industrial replication found no evidence that TDD beats test-last development ([Helsinki repository](https://helda.helsinki.fi/server/api/core/bitstreams/28435ba6-f068-4f28-983a-47d703536365/content)). The practical lesson: keep steps small, write tests for all logic, and use test-first where it is natural, such as parsers, calculators and every bug fix.

For the mix of tests, the **test pyramid** says many fast unit tests and few slow end-to-end tests, because end-to-end tests are "notoriously flaky" ([Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)). The **testing trophy** puts integration tests at the centre: "The more your tests resemble the way your software is used, the more confidence they can give you" ([Kent C. Dodds](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)). They agree on the main point: test behaviour, not internal details, and keep only a few end-to-end tests for the most important journeys.

**Refactoring** is "restructuring an existing body of code, altering its internal structure without changing its external behavior," in small steps, with the system kept working after each one ([refactoring.com](https://refactoring.com/)). Never mix a refactor and a feature in one commit; the Fucci study found mixed refactoring linked to worse outcomes. John Ousterhout suggests spending about 10–20% of your time on design and cleanup, and prefers "deep" modules (a simple interface hiding a lot of work) over many tiny classes (via [summary](https://dev.to/carstenbehrens/summary-of-a-philosophy-of-software-design-by-john-ousterhout-c52)). Merge small changes into the main branch at least once a day, with tests that run in a few minutes; DORA's research finds speed and stability go together ([DORA](https://dora.dev/capabilities/trunk-based-development/); [DORA metrics](https://dora.dev/guides/dora-metrics/)).

**Debugging.** David Agans' nine rules are the standard checklist: understand the system, make it fail, quit thinking and look, divide and conquer, change one thing at a time, keep an audit trail, check the plug, get a fresh view, and "if you didn't fix it, it ain't fixed" ([Embedded Artistry](https://embeddedartistry.com/blog/2017/9/6/debugging-9-indispensable-rules)). "Divide and conquer" means halving the search space; `git bisect` does this over your commit history to find the commit that broke something ([git docs](https://git-scm.com/docs/git-bisect)). Turn every bug into a failing test first, then fix it ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)).

**Checklist, step 7**
- [ ] Start from green: pull, run tests.
- [ ] One small change. Feature **or** refactor, never both.
- [ ] Run fast tests and linters. Commit with a message that says *why*.
- [ ] For a bug: reproduce → observe logs → one hypothesis → change one thing → bisect if it "used to work" → keep the test.
- [ ] Every hour: fix the most confusing name or function you just wrote.

**Translator example.** `pipeline-core` holds pure logic with no input/output, so it can be replayed from WAV files and unit-tested; the project has 139 Python tests and 17 API tests ([CLAUDE.md](../CLAUDE.md)). The security pass followed "make it fail" exactly: each of 12 findings was reproduced first and then covered by a regression test. The worst bug is a good debugging lesson. When a call ended in the middle of a sentence, the TTS program fell one reply behind, so the **next caller, in any room, heard the previous room's translated speech**. The fix checks a reply id on every exchange and restarts the worker on any protocol error ([ADR-030](../docs/adr/0017-local-dev-and-mvp-decisions.md)).

### Step 8. Measure on a fixed eval set

Progress means working, measured behaviour, not code written. "If you haven't seen it run, it's not a working system" ([Simon Willison](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)). Measure distributions (p50, p95), not single runs, on the same fixed test set each time. Feelings are not reliable. In METR's 2025 trial, 16 experienced developers were about **19% slower** with early-2025 AI tools but believed afterwards that they had been about 20% faster ([METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)). The sample was small and newer tools may differ, but the gap between feeling and fact is the lesson.

| Feedback loop | Time | What it tells you |
|---|---|---|
| Types, linter, unit tests | seconds | Did I break logic? |
| Local end-to-end smoke test | a minute | Does the whole path still work? |
| CI on every push | minutes | Is it green on a clean machine? |
| Fixed eval set | per important change | Are p50/p95 and error rates better or worse? |
| Demo to a real user | per slice or week | Does it help someone? |
| Weekly retrospective | weekly | What slowed me down? What will I change? |

**Checklist, step 8**
- [ ] A fixed eval set, saved in the repo, run the same way every time.
- [ ] Report p50 and p95, never one demo run.
- [ ] Record before-and-after numbers for every important change.
- [ ] Write down what the eval set cannot tell you.

**Translator example.** A 72-call smoke set runs real calls in all six directions. Run 2 scored 61 correct out of 72. The final run, after the accuracy pass, scored **63/72 (88%)**, with both remaining wrong-meaning errors coming from ASR, and every number and negation kept ([final review](../eval/results/2026-10-15/smoke-v0-call-final-review.md); [CLAUDE.md](../CLAUDE.md)). Each change was measured: cleaning ASR text cut Hindi WER from 4.1% to 1.4%; a prompt fix cut Mandarin character errors from 4.2% to 0.8%; unloading unused models cut hi→te p95 from 4.4 s to 1.6 s ([ADR-029](../docs/adr/0017-local-dev-and-mvp-decisions.md)). Some ideas were measured and **rejected**, such as a decoder that raised Telugu WER from 4.8% to 7.4%. The eval also states its limits: the speakers are TTS voices, so results are optimistic, and a native speaker should re-check the meaning reviews.

### Step 9. Repeat: choose the next slice by risk and value

After each slice: demo it, look at the numbers, then pick the next slice that removes the biggest remaining risk or adds the most value. Update the design doc and write ADRs for any new decision. When a big change fails, go back to the last working version and grow again in smaller steps; that is Gall's law in daily practice. A simple solo retrospective each week (what went well, what was painful, one change to try) keeps the loop honest. This retro format is common agile practice rather than something the research measured.

**Checklist, step 9**
- [ ] Demo the slice and record numbers.
- [ ] Re-rank risks. Is the top risk still the same?
- [ ] Choose the next slice. Write it down in one sentence.
- [ ] Update the plan and ADRs.

**Translator example.** The next steps follow from the numbers and the risk list: try a real browser call, then build an eval set with recorded **human** voices (because TTS speakers flatter the ASR scores), then deploy to the Contabo server. Mandarin ASR is the slowest stage, so Qwen3-ASR is the next model to benchmark ([CLAUDE.md](../CLAUDE.md)).

## Skill comes from closed feedback loops, not hours

Expertise research says practice must be focused, a little beyond your current ability, and come with fast feedback. Peter Norvig puts it simply: "challenging yourself with a task that is just beyond your current ability," and "there appear to be no real shortcuts" ([Norvig](https://norvig.com/21-days.html)). Anders Ericsson calls practice with these features **purposeful practice**. His stricter **deliberate practice** also needs established training methods and a coach. Programming mostly has neither, so a self-taught developer must design their own feedback ([Commoncog](https://commoncog.com/the-problems-with-deliberate-practice/)).

Be careful with the famous "10,000 hours" story. A 2014 meta-analysis found deliberate practice explained 26% of performance differences in games but **less than 1% in professions** ([New Statesman](https://www.newstatesman.com/science-tech/2014/08/when-it-comes-expertise-10000-hours-practice-isn-t-enough)). Critics answer that the study used a much looser definition of practice, and a stricter reanalysis found 29–61% ([Frontiers in Psychology](https://frontiersin.org/article/10.3389/fpsyg.2019.02396/full)). The fair reading: practice clearly takes you from beginner to good. Whether it explains the gap between good and great is disputed. No controlled study of programmers exists. So aim to be a solid, reliable engineer, and judge progress by feedback loops closed, not hours logged. Dan Luu argues that reaching the top 5% of people doing something is "not very hard" because "relatively few people are trying to improve at all." One programmer recorded his screen for a week and found a quarter of his time went to finding which function had the bug; testing each function as he wrote it fixed that ([Dan Luu](https://danluu.com/p95-skill/)).

Where does feedback come from when you have no mentor? Several sources work well:

| Feedback source | How to use it |
|---|---|
| Automated tests | "Build your own X" projects, where your version must match the real tool ([build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)) |
| Expert reference | Write your design first, then compare with a published real system ([AOSA books](https://aosabook.org/en/)) |
| Code review | Open-source pull requests; review others' merged PRs and compare your comments with the maintainers' |
| Your past self | A journal or ADR log of predictions you grade later |
| Self-testing | Close the book, write the explanation from memory; spaced flashcards |

Two research findings shape this list. Code review's main proven benefit is **knowledge transfer**, more than finding bugs ([Bacchelli and Bird, Microsoft Research](https://web.eecs.umich.edu/~weimerw/2018-481/readings/codereview.pdf)). And of ten study methods, **practice testing** (quizzing yourself) and **spaced practice** were rated most useful, while rereading, highlighting and summarising were rated low ([APS, Dunlosky et al.](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html)). Julia Evans adds a cheap habit: when you feel "wait, I'm really confused," turn it into a specific yes/no question and write a tiny program to "ask the computer" ([jvns.ca](https://jvns.ca/blog/learn-how-things-work/)).

## A two-year practice plan built around the nine-step loop

The core idea: **run every practice project through the nine-step loop**, even small ones. Write the one-page plan, the numbers, the non-goals and the ADRs for a URL shortener, just as you would for a big system. The process is the skill you are training. The plan below combines the research above. The hours come from the sources, but the exact schedule and milestones are my synthesis, not measured data, and your pace will differ.

### Weekly plan (about 10–15 hours)

| When | Time | Activity | Feedback built in |
|---|---|---|---|
| Daily | 30–45 min | One small coding problem **without AI** (LeetCode or Exercism), then compare with good solutions. 10 min of flashcards. | Tests pass or fail; better solutions to compare |
| 3× a week | 1.5–2 h | Build: your current project or "build your own X." Write the test before the feature. | Your tests; the real tool to compare against |
| 1× a week | 2 h | Theory: one chapter (for example from OSTEP). Then close the book and write half a page from memory. Do one tiny experiment that tests a claim from the chapter. | Self-test; the computer |
| 1× a week | 1–1.5 h | Design drill: pick a real system. Write a 1–2 page mini design doc first. Then read the real design and list the differences. | Expert reference |
| 1× a week | 1 h | Review: read one merged PR in a good open-source project, or open your own PR, or swap reviews with a friend. Ask an AI to **critique, not rewrite**, one piece of your code. | Other people's judgement |
| Weekly | 20 min | Journal: what I built, one bug and its root cause, one decision with alternatives, real time spent, next week's single focus. | Your past predictions |

If you have only about 6 hours a week, keep the daily problem, one build session, the design drill and the journal. Do not drop the feedback parts first; they are what make practice work.

### Monthly plan

- [ ] Finish one project stage. Write a short README or blog post explaining how it works (teaching is self-testing).
- [ ] One timed mock system design (45–60 min, using steps 1–4). Record yourself or do it with a friend, and review it later.
- [ ] Reread last month's journal and design docs. Grade your predictions: what did you get wrong?
- [ ] One "no-AI day" of building and debugging, to check you can still work alone.

### A project ladder (suggested)

Each rung adds one new kind of difficulty. Run all of them through the nine steps.

1. **Pastebin or URL shortener with Postgres.** Practise requirements, non-goals, the estimate from the system-design-primer, a walking skeleton, deployment.
2. **Your own HTTP server or shell** from build-your-own-x. Practise testing against a real tool and reading specs.
3. **A Redis clone or Git clone** that passes a test suite. Practise data structures, protocols and debugging.
4. **A real project with users** (your translator counts). Practise measurement, an eval set, monitoring and a written post-mortem of one real bug.
5. **MIT 6.824 distributed-systems labs**, which are free and graded by tests. Practise reasoning about failure.

### Milestones

| Period | Target |
|---|---|
| Months 0–3 | A deployed CRUD app (create, read, update, delete) with login, Postgres and Git, following the roadmap.sh backend path ([roadmap.sh](https://roadmap.sh/backend)). 30+ small problems. First rebuild project. |
| Months 3–9 | A rebuild (Redis or Git clone) passing tests. Core chapters of *Computer Systems: A Programmer's Perspective* and *OSTEP*. First merged open-source PR. 5 design drills logged. |
| Months 9–18 | A database or key-value store rebuild. Networking and databases studied. *Designing Data-Intensive Applications* read with notes. About 100 problems. 15+ design docs. A real project with users and one post-mortem. |
| Months 18–36 | Distributed systems labs. Remaining fundamentals. Regular open-source reviews. You can write a 5–10 page design doc with real alternatives and capacity numbers. |

The fundamentals roadmap at teachyourselfcs lists nine subjects at **100–200 hours each**, about 900–1,800 hours in total, and says beginners should code for a year or two first. If time is short, it picks two books: *Computer Systems: A Programmer's Perspective* and *Designing Data-Intensive Applications* ([teachyourselfcs](https://teachyourselfcs.com/)). At 10 hours a week, 900–1,800 hours is about 2–3.5 years, which fits Norvig's "continually improve over 24 months" as the first horizon. Most of these resources are free: OSTEP, *Crafting Interpreters*, the System Design Primer with its flashcard decks, the AOSA and *500 Lines or Less* books, university lecture videos and Exercism. One untested idea for a bilingual learner: after you learn a concept, explain it to yourself in Telugu or Hindi, then write it in English. Both directions force you to recall it, which is the kind of self-testing the learning research supports.

## AI assistants: use them as a tutor and reviewer, not a ghostwriter

The strongest evidence comes from Anthropic's 2026 randomised trial. 52 mostly junior engineers learned a new Python library. The group that used AI finished only about 2 minutes faster (not statistically significant) and scored **50% vs 67%** on a mastery quiz. The biggest gap was on **debugging** questions. How people used the AI mattered. Those who handed over code-writing scored under 40%. Those who asked conceptual questions, or generated code and then asked follow-up questions to understand it, scored 65% or more ([Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills); [InfoQ](https://infoq.com/news/2026/02/ai-coding-skill-formation/)). The limits: one library, a short quiz, a chat tool rather than an agent. The authors expect agentic tools could have bigger effects. A Microsoft/CMU survey of 319 knowledge workers found that **more confidence in AI went with less critical thinking** ([Microsoft Research](https://www.microsoft.com/en-us/research/?p=1135061)). Add METR's finding that people feel faster than they are, and the message is clear: AI can help you ship, but it can quietly stop you learning, and you will not feel it happen.

Expert workflows agree on one shape: **spec → plan → small steps → a check the AI can run → you read the diff → commit**. Anthropic's own guide says "letting Claude jump straight to coding can produce code that solves the wrong problem," and "give Claude a check it can run: tests, a build, a screenshot to compare." Without a check, "you become the verification loop." For bugs: "write a failing test that reproduces the issue, then fix it" ([Claude Code best practices](https://code.claude.com/docs/en/best-practices)). Addy Osmani writes the spec and plan first, feeds the model "manageable tasks, not the whole codebase," commits as "save points," and says: "I remain the accountable engineer" and "be intentional about periodically coding without AI too" ([Addy Osmani](https://addyosmani.com/blog/ai-coding-workflow/)). Simon Willison calls the model "an over-confident pair programming assistant" and says testing cannot be outsourced ([Simon Willison](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)).

**Rules for learning days** (from the high-scoring patterns)
- [ ] Try it yourself first, for 20–30 minutes, before asking.
- [ ] Ask "why" and "explain" questions, not only "write this."
- [ ] If AI writes code, you must be able to explain every line and rewrite it from memory.
- [ ] Debug yourself first: form your own hypothesis, then ask the AI to check it.
- [ ] Use the AI as a critic: "What fails at 10× load? What did I miss?"
- [ ] Turn on learning or explanatory modes where your tool has them.

**Rules for shipping days**
- [ ] You write or approve the spec and the plan. You can explain each step.
- [ ] Every task has a check the AI can run: tests, a build, an eval set.
- [ ] Read every diff. Never commit code you cannot explain.
- [ ] Keep durable decisions in project files (CLAUDE.md, ADRs), not in chat history.
- [ ] Use a fresh session as a reviewer, asking only for correctness and requirement gaps.
- [ ] Measure your real time and defect rate; do not trust the feeling of speed.

**Translator example.** This project shows the shipping-day rules working. The plan came first, and implementation started only after you approved it. Durable memory lives in CLAUDE.md, `docs/plan.md` and the ADRs, so each AI session starts from written decisions, not from guesses. The 72-call eval set is the check the AI runs after each change. One detail is worth copying: the eval meaning reviews were done by the AI, and the results file says "A native speaker should re-check" ([final review](../eval/results/2026-10-15/smoke-v0-call-final-review.md)). That is the human staying in the verification loop. The risk, for your learning, is that the AI did most of the debugging. To turn this project into practice, take one real bug from an ADR (for example the TTS cross-room bug in ADR-030), check out the code from before the fix, and find the root cause yourself without AI before you read the answer.

## Conclusion

The surprising thing about expert practice is how little of it is about code. Most of the skill sits before the first line (numbers, non-goals, the riskiest guess) and after each change (a fixed measurement, a written decision). Coding is the middle of the loop, and AI is making the middle cheaper every year. That shifts where human value lies: defining success in numbers, designing checks a machine can run, judging trade-offs, and debugging what the checks reveal. These are exactly the skills the 2026 trial found most eroded by delegation, so they are the ones to protect on purpose.

For a self-taught developer, this means the process itself is the curriculum. Do not wait to "know enough" before writing a design doc or an ADR. Write them for small projects now, grade them later, and count the feedback loops you close each week. The research cannot promise how fast you will improve, and its timelines are averages with wide variation. But it is consistent on direction: steady, small, checked steps beat long unchecked effort. Your translator project already proves you can run the loop with an AI partner. The next level is running it again with the AI as tutor, not author, and owning the debugging yourself.
