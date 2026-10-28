# Planning and Execution: From Design to a Working System

Scope: the "execution" stage. How experts break a design into tasks, where they start coding, and the loop that keeps a project moving and correct. The audience is a self-taught or early-career developer. Research date: 2026-10-19.

Source quality note: several classic ideas (walking skeleton, Agans' rules, Ousterhout, Gall's law, "make it work, make it right, make it fast") are mostly available online only as secondary summaries of the books. Where I could reach only a summary, I say so. Primary or near-primary sources: the Artima interview with Hunt & Thomas, martinfowler.com, refactoring.com, dora.dev, kentcdodds.com, arXiv (Fucci et al.), the Anthropic research page, the Claude Code docs, simonwillison.net and addyosmani.com.

---

## 1. Walking skeleton and tracer bullets: what they are, how to build one, how they differ from prototypes

### Takeaway
Start by building the thinnest possible piece of real functionality that runs end to end through every major component, and that you can build, deploy and test automatically. Keep that code and grow the system around it. A prototype is different: it is throwaway code that answers one specific question (for example, "can the database handle 10k transactions an hour?") and is then deleted.

### Cited Findings
- **Tracer bullets exist for feedback.** Dave Thomas: "Basically, it all comes down to feedback." The sooner you get feedback, the less you have to correct course. — [Artima interview: Tracer Bullets and Prototypes](https://www.artima.com/articles/tracer-bullets-and-prototypes)
- **What a tracer bullet looks like.** Andy Hunt describes a "skeletal" first build: one thin path from the UI through the business logic to the database. Each later feature adds a use case to that path. His example first skeleton might "put a checkbox value into the database as a Boolean," which exercises every layer. — [Artima](https://www.artima.com/articles/tracer-bullets-and-prototypes)
- **Why start early.** Thomas and Hunt argue you should build the skeleton while requirements are still volatile, "when the requirements are more volatile, the code is easiest to change." — [Artima](https://www.artima.com/articles/tracer-bullets-and-prototypes)
- **Prototypes are for learning and are thrown away.** Hunt: "Prototypes are for your learning." Thomas: "prototypes are a learning tool." Example: you need 10,000 database transactions per hour but have never exceeded 5,000, so you "hack together a real ugly little script" to test whether the database can cope. "Prototypes are designed to be thrown away," and it is "inappropriate to over-engineer a prototype." — [Artima](https://www.artima.com/articles/tracer-bullets-and-prototypes)
- **The term "walking skeleton".** Secondary sources attribute it to Alistair Cockburn (*Crystal Clear*; coined in the 1990s and written up on his site around 2008). In their account, the skeleton does not need the final architecture, but it should link together the main architectural components, so architecture and functionality can then evolve in parallel. — [Henrico Dolfing, "Start your project with a walking skeleton"](https://henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html); [Matt Blodgett, "Start with a Walking Skeleton"](https://www.mattblodgett.com/2020/09/start-with-walking-skeleton.html)
- **GOOS definition.** *Growing Object-Oriented Software, Guided by Tests* (Freeman & Pryce) describes the walking skeleton as "an implementation of the thinnest possible slice of real functionality that we can automatically build, deploy, and test end-to-end." This quote comes via secondary summaries; I did not read the book text. — summarised in [Henrico Dolfing](https://henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html) and other results from the same search
- **Skeleton vs. spike or proof of concept.** "A proof of concept (or spike) is meant to be throw away code while the Walking Skeleton is meant to evolve over time." — [Matt Blodgett](https://www.mattblodgett.com/2020/09/start-with-walking-skeleton.html)
- **How long it takes.** One secondary source says Cockburn estimates 20 minutes to 2 weeks. I could not confirm this in Cockburn's own writing. — search-result summary, unverified
- **Variants.** Dan North's "Dancing Skeleton" adds an interface for developers to experiment with the environment. Gojko Adzic's "Forget the walking skeleton, put it on crutches" argues for shipping an even thinner, partly manual version to real users sooner. — [Gojko Adzic](https://gojko.net/2014/06/09/forget-the-walking-skeleton-put-it-on-crutches/)
- **When to use which.** Secondary summaries of *The Pragmatic Programmer* recommend tracer bullets when you are "shooting in the dark" (vague requirements, unproven architecture). Prototypes suit a single risky aspect that you throw away afterward. — [Barbarian Meets Coding notes](https://www.barbarianmeetscoding.com/notes/books/pragmatic-programmer/tracer-bullets/)

### Inferences
- **How to build a walking skeleton, step by step** (synthesised from the sources above):
  1. List the main components from your design, for example browser UI → API → worker → database.
  2. Pick the most trivial user-visible behaviour that touches all of them, such as "click button, a row is saved, a confirmation appears" (Hunt's checkbox example).
  3. Hard-code everything else: fake data, a single user, no error handling, no styling.
  4. Make it **automatically** buildable, testable and deployable: one command to run, one end-to-end test, a CI job, and ideally a deploy to the real target environment. This is what the GOOS definition adds beyond "a demo that works on my machine."
  5. Commit it. Every later feature is a new thin slice added to this path (§2).
- **Comparison table:**

  | | Prototype / spike | Tracer bullet / walking skeleton |
  |---|---|---|
  | Purpose | Answer one question, learn | Prove the end-to-end architecture and get feedback |
  | Breadth | One risky piece | Every major component, thinly |
  | Code fate | Thrown away | Kept and grown |
  | Quality bar | Ugly is fine | Production-minded but minimal |

- **Applied to a live-translator-style project:** a skeleton would be browser mic → WebRTC room → agent receives audio → ASR → MT → TTS → listener hears audio, for one language pair, with one hard-coded room. Picking the "best" model can wait. Separate throwaway prototypes answer narrow questions such as "is model X fast enough on CPU?"

### Gaps
- I found no primary Cockburn page (his site and the c2 wiki did not render), so his exact wording and the "20 minutes to 2 weeks" estimate are unverified.
- The exact wording of *The Pragmatic Programmer* (20th anniversary edition), Topic 12 "Tracer Bullets" and Topic 13 "Prototypes and Post-it Notes", was not available. The Artima interview with the same authors stands in for it.

---

## 2. Vertical slicing, story splitting, and "make it work, make it right, make it fast"

### Takeaway
Split work into **vertical slices**: small changes that cut through every layer (UI, logic, data) and deliver something a user can see and test. Avoid horizontal splits ("build the database layer first"), which deliver nothing until all layers are combined. Use named splitting patterns to make slices small, and separate "make it work" from "make it fast."

### Cited Findings
- **Vertical vs. layer splitting.** Vertical slices cut across architectural layers to deliver a user-visible change. They make value explicit, surface constraints sooner and produce earlier, better feedback. Layer splitting (separate UI, database and logic stories) may look small but usually fails the Independent and Valuable criteria, because the work only has value once the layers are combined. — [Humanizing Work Guide to Splitting User Stories](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)
- **Nine splitting patterns** (Richard Lawrence / Humanizing Work) — [Humanizing Work](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/):
  1. *Workflow steps:* build the simple end-to-end path first, then add middle steps. ("Publish directly", then "publish with editor review", then "with legal review".)
  2. *Operations (CRUD):* split "manage X" into create, edit, delete.
  3. *Business rule variations:* each rule variant is its own complete behaviour.
  4. *Variations in data:* start with a simple data model (county-level search), then add cities and neighbourhoods.
  5. *Data entry methods:* simplest UI first (a text date field), then the richer one (a calendar widget).
  6. *Major effort:* when the first item carries most of the effort, implement one case first (one card type), then the rest.
  7. *Simple/complex:* define the simplest version as its own story, and move each edge case to its own story.
  8. *Defer performance:* split "make it work" from "make it fast" (a slow search with a spinner, then under 5 s). Warning from the guide: don't treat the first version as finished.
  9. *Break out a spike:* a time-boxed investigation when the implementation is poorly understood. Use it only after the other patterns fail.
  - Meta-pattern: "Find the core complexity, identify its sources of variation, and reduce them to one complete slice." Prefer splits that let you drop low-value work and that produce similarly sized stories.
- **INVEST criteria** for a good slice: Independent, Negotiable, Valuable, Estimable, Small (roughly 6 to 10 stories fit in a sprint), Testable (a concrete, verifiable change in behaviour defines "done"). — [Humanizing Work](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)
- **"Make it work, make it right, make it fast."** This is widely attributed to Kent Beck, but I found no primary source with a date, book or talk. One informal source says it echoes older Unix practice (Kernighan) and the rules of optimisation. — [Keyhole Software](https://keyholesoftware.com/writing-quality-code-practicing-make-it-work-make-it-right-make-it-fast/); [NCSU blog](https://freeh.wordpress.ncsu.edu/2017/11/page/2/); [Scrapbox note (informal)](https://scrapbox.io/nikkie-memos/Make%20It%20Work%20Make%20It%20Right%20Make%20It%20Fast)
- **The same sequencing for AI-assisted planning.** Osmani asks a reasoning model to turn the spec into "bite-sized milestones," then implements one step at a time. — [Addy Osmani, "My LLM coding workflow going into 2026"](https://addyosmani.com/blog/ai-coding-workflow/)

### Inferences
- **Worked example of slicing** (an invented "translation call" feature, applying the patterns above):
  - Slice 1 (workflow steps, simplest path): one hard-coded language pair, en→te, text captions only.
  - Slice 2: add TTS audio for the same pair.
  - Slice 3 (data variations): add a second pair.
  - Slice 4 (simple/complex): handle numbers and dates correctly.
  - Slice 5 (defer performance): get first audio under 2 s.
  - Each slice is demoable, has its own end-to-end check, and could ship alone.
- Read "make it work, make it right, make it fast" as an ordering of *attention*, not permission to skip correctness. "Work" means passes its tests, "right" means refactored to clean structure (§4), and "fast" means optimised only where measurements show a need.
- A useful self-check: if a task's description names a layer ("write the DB schema", "build the API") rather than a behaviour ("user can save a contact"), it is probably a horizontal split.

### Gaps
- I found no primary source for Beck's "make it work, make it right, make it fast", or for the related Beck line "make the change easy, then make the easy change". Both are widely quoted, but I did not verify them this session.
- I found no empirical studies quantifying the benefit of vertical over horizontal slicing. The evidence is practitioner consensus.

---

## 3. Test-Driven Development in practice, the evidence, and the testing pyramid vs. trophy

### Takeaway
TDD is a tight loop: list the test cases, write one failing test, write just enough code to pass it, refactor, repeat. The evidence is **mixed**. The most rigorous dissection found that the benefit comes from working in *small, steady steps* (granularity and uniformity), not from writing the test *first*. For test mix, the pyramid (many fast unit tests, few end-to-end tests) and the trophy (mostly integration tests, plus static checks) are two rules of thumb. They share one goal: the most confidence per unit of time.

### Cited Findings
**How TDD works (the loop)**
- Fowler's description: first "write out a list of test cases" ("a vital initial step"). Then repeat: "Write a test for the next bit of functionality you want to add," "Write the functional code until the test passes," "Refactor both new and old code to make it well structured." — [Fowler, bliki: TestDrivenDevelopment](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- The most common failure mode: "The most common way that I hear to screw up TDD is neglecting the third step" (refactoring). The result is messy code, though at least it has tests. — [Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- TDD yields "SelfTestingCode, since we can only write some functional code in response to making a test pass." — [Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

**Evidence on effectiveness**
- **Fucci, Erdogmus, Turhan, Oivo, Juristo (IEEE TSE 2017, arXiv 2016)**, "A Dissection of the Test-Driven Development Process: Does It Really Matter to Test-First or to Test-Last?". 82 data points from 39 professionals. "Quality and productivity improvements were primarily positively associated with the granularity and uniformity." "Sequencing, the order in which test and production code are written, had no important influence." Refactoring effort was *negatively* associated with both outcomes, possibly because of "mixed refactoring" (refactoring tangled with feature work). Conclusion: "The claimed benefits of TDD may not be due to its distinctive test-first dynamic" and "TDD-like processes encourage fine-grained, steady steps that improve focus and flow." Quality was measured as functional correctness only. — [arXiv:1611.05994](https://arxiv.org/abs/1611.05994)
- **An industrial replication** found "no evidence to support the claim that external quality and productivity are improved by the adoption of TDD compared to test-last development." Process conformance improved quality but did not affect productivity. — [Helsinki repository (Helda)](https://helda.helsinki.fi/server/api/core/bitstreams/28435ba6-f068-4f28-983a-47d703536365/content)
- **Skills matter more than process for professionals.** One study concluded that quality and productivity gains "are associated with skills, rather than with the process, at least in the case of professional developers." The test-first approach may help novices' productivity. — [Oulu repository](https://oulurepo.oulu.fi/handle/10024/34912?show=full)
- **More tests correlate with better outcomes.** One replication found that the number of tests written is related to external quality and productivity, and recommended writing as many tests as possible. — [Brunel repository](https://bura.brunel.ac.uk/handle/2438/14828)
- **Literature-review level.** One review across ten quality attributes found TDD "can reduce the amount of introduced defects and lead to more maintainable code," while "initial development may last longer." — [Springer, Empirical Software Engineering, doi 10.1007/s10664-013-9259-7](https://link.springer.com/doi/10.1007/s10664-013-9259-7)
- **Reviews disagree with each other.** A 2025 tertiary study of TDD systematic reviews found "Conclusions regarding external quality and productivity may vary across the SLRs," depending on which primary studies each includes. — [Reliability of systematic literature reviews on TDD](https://repositorioacademico.uda.cl/entities/publication/78377e78-9bb6-43d4-aaba-40636f76fdd4)

**Testing pyramid vs. trophy**
- **Pyramid (Mike Cohn, *Succeeding with Agile*).** Two rules: "Write tests with different granularity" and "The more high-level you get the fewer tests you should have." That means many small, fast unit tests, some coarser tests and very few end-to-end tests. The anti-pattern is the "test ice-cream cone." — [Ham Vocke, "The Practical Test Pyramid," martinfowler.com](https://martinfowler.com/articles/practical-test-pyramid.html)
- Unit tests should "test the public interface of the class," checking observable behaviour rather than private methods or call order. Trivial getters and setters don't need tests. — [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- End-to-end tests are "notoriously flaky and often fail for unexpected and unforeseeable reasons," "require a lot of maintenance and run pretty slowly." Keep a few for high-value user journeys. Contract tests (consumer-driven, e.g. Pact) check that service boundaries keep their agreement. — [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- **Trophy (Kent C. Dodds).** Layers from bottom to top: static (types, linters), unit, integration (the biggest), end-to-end. It builds on Guillermo Rauch's "Write tests. Not too many. Mostly integration." Guiding principle: "The more your tests resemble the way your software is used, the more confidence they can give you." Dodds frames it as return on investment, where confidence is the return and time is the investment. He notes the view comes from UI work in a single codebase. — [Kent C. Dodds, "The Testing Trophy and Testing Classifications"](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)

### Inferences
- **Concrete TDD example** (`parse_amount("₹1,200")` → `1200`), following Fowler's steps:
  1. Test list: "₹1,200" → 1200; "1200" → 1200; "1.5k" → 1500; "" → error.
  2. **Red:** write `assert parse_amount("1200") == 1200` and run it. It fails because the function doesn't exist.
  3. **Green:** `def parse_amount(s): return int(s)`. The test passes, which is fine for now.
  4. Next test: `"₹1,200"`. It fails, so strip the symbol and commas. Green.
  5. **Refactor:** extract `_normalise(s)`, rename variables, rerun all tests.
  6. Repeat for "1.5k" and the error case. Each loop takes a few minutes, and that small, steady step size is what Fucci et al. found mattered.
- **When experts use TDD vs. not (inferred from the evidence):**
  - Use it for pure logic with clear inputs and outputs (parsers, calculators, rules, algorithms), for bug fixes (write the failing test that reproduces the bug first), and when working with an AI agent, which needs a pass/fail signal (§7).
  - Skip it or loosen it for exploratory spikes and prototypes (thrown away anyway), for UI layout, and when you don't yet know what the API should be. Write tests right after the code stabilises instead.
  - Whichever order you choose, keep steps small and uniform, and keep refactoring separate from feature work, since mixed refactoring correlated with worse outcomes.
- Pyramid vs. trophy is less a contradiction than a difference of context. Pure-logic back ends and libraries lean pyramid. UI-heavy apps lean trophy. Both say: few slow, flaky end-to-end tests; test behaviour, not implementation.

### Gaps
- I could not retrieve the abstract or effect sizes of Rafique & Mišić (2013, IEEE TSE), "The effects of test-driven development on external quality and productivity: A meta-analysis". Its findings are not reported here.
- I did not access the primary text of Beck's *Test-Driven Development: By Example* (2002). The steps above come from Fowler's summary.
- Google Testing Blog guidance (small/medium/large test sizes, the "Just Say No to More End-to-End Tests" post) was not fetched this session.

---

## 4. Structuring code while writing it: refactoring, complexity, small changes, trunk-based development, CI

### Takeaway
Experts keep the system working at every step. They refactor in small behaviour-preserving moves, invest a steady 10–20% of time in design (Ousterhout's "strategic programming"), integrate small changes into the main branch at least daily, and rely on fast automated tests in CI. DORA's research finds this kind of speed and stability go together, not against each other.

### Cited Findings
- **Refactoring defined.** "A disciplined technique for restructuring an existing body of code, altering its internal structure without changing its external behavior." Its heart is a series of "small behavior preserving transformations," and "The system is kept fully working after each refactoring." Without automated refactoring tools, Fowler relies on small steps and "using frequent testing to detect mistakes." — [Martin Fowler, refactoring.com](https://refactoring.com/)
- **Ousterhout: tactical vs. strategic programming** (*A Philosophy of Software Design*, via secondary summaries). Tactical programmers optimise for getting the current feature done fast and let complexity accumulate. Strategic programmers treat good design as part of the job. He recommends investing about 10–20% of development time in design and cleanup, and warns of the "tactical tornado," a fast developer who leaves "a wake of destruction" for others. He notes complexity accumulates in small increments and is hard to remove later. — [Carsten Behrens summary (dev.to)](https://dev.to/carstenbehrens/summary-of-a-philosophy-of-software-design-by-john-ousterhout-c52); [Antoine Buteau, lessons from Ousterhout](https://www.antoinebuteau.com/lessons-from-john-ousterhout.md)
- **Ousterhout: deep modules.** A deep module offers a lot of functionality behind a simple interface. The Unix file I/O calls are the classic example: a handful of simple calls hide permissions, caching, scheduling and drivers. A shallow module's interface is nearly as complex as its implementation. Deep modules come from information hiding. — [Carsten Behrens summary](https://dev.to/carstenbehrens/summary-of-a-philosophy-of-software-design-by-john-ousterhout-c52)
- **Trunk-based development (DORA).** Developers "merge … at least once (and potentially several times) a day" into trunk. Branches "typically last no more than a few hours." Keep "three or fewer active branches." Avoid code freezes and integration phases. Supporting practices: fast automated tests before every commit, a build-and-test goal of "a few minutes," and synchronous code review. DORA's 2016–2017 data link these practices to higher delivery and operational performance. The page gives no effect sizes. — [DORA: Trunk-based development](https://dora.dev/capabilities/trunk-based-development/)
- **DORA delivery metrics.** Throughput: change lead time (commit to production), deployment frequency, failed-deployment recovery time. Instability: change fail rate, deployment rework rate. "DORA's research has repeatedly demonstrated that speed and stability are not tradeoffs," and "Top performers do well across all five metrics." — [DORA metrics guide](https://dora.dev/guides/dora-metrics/)
- **Commits as save points (AI era).** Osmani makes small, frequent commits so bad changes can be rolled back, comparing them to "save points in a game," and uses branches or worktrees to isolate experiments. — [Addy Osmani](https://addyosmani.com/blog/ai-coding-workflow/)

### Inferences
- **A practical in-the-moment routine** for an early-career developer:
  1. Pull the latest main and run the tests, so you start from green.
  2. Make one small change: a slice, a test, or a refactor, but never a refactor and a feature in the same commit. This follows Fowler's "two hats" idea and the Fucci finding on mixed refactoring.
  3. Run the fast tests and linters.
  4. Commit with a message that says *why*. Aim for commits small enough to describe in one sentence.
  5. Merge or push to main at least daily, behind a feature flag if the work is unfinished.
  6. Every 30–60 minutes, ask: what is the most confusing name or function I just wrote? Fix it now. That is Ousterhout's "strategic" investment, made in small doses.
- Function-level habits like small functions and intention-revealing names come from Fowler's and Beck's refactoring catalogues, but Ousterhout pushes back on splitting too finely. Shallow, tiny functions can *increase* complexity. Aim for functions and modules whose interface is much simpler than what they do.
- CI is the mechanical enforcement of all of this. If the build and tests take a few minutes and run on every push, small commits become cheap and safe.

### Gaps
- I did not access the primary texts of Fowler's *Refactoring* (2nd ed.) or Ousterhout's book. The details above rely on refactoring.com and secondary summaries; one dev.to review in the results contained invented-looking statistics and was excluded.
- I did not fetch Fowler's "Continuous Integration" article or *Accelerate* (Forsgren, Humble, Kim) directly this session. DORA's own pages stand in for them.

---

## 5. Systematic debugging

### Takeaway
Reproduce first, then observe instead of guessing. Narrow the search space by halving it (divide and conquer, `git bisect`), change one thing at a time, keep a log, and don't call it fixed until you've shown the fix removes the failure. Agans' nine rules are the standard checklist.

### Cited Findings
- **David Agans, *Debugging: The 9 Indispensable Rules* (AMACOM, 2002).** The rules: (1) Understand the System, (2) Make It Fail, (3) Quit Thinking and Look, (4) Divide and Conquer, (5) Change One Thing at a Time, (6) Keep an Audit Trail, (7) Check the Plug, (8) Get a Fresh View, (9) If You Didn't Fix It, It Ain't Fixed. — [Inspirezone book review](https://inspirezone.tech/9-indispensable-rules-for-debugging-software-and-hardware/); [Embedded Artistry](https://embeddedartistry.com/blog/2017/9/6/debugging-9-indispensable-rules); [debuggingrules.com](https://debuggingrules.com/) (official site, poster only)
- *Make It Fail:* knowing how to reproduce the failure is critical to fixing it. "Stimulate the failure, don't simulate it." — [Inspirezone](https://inspirezone.tech/9-indispensable-rules-for-debugging-software-and-hardware/)
- *Quit Thinking and Look:* don't jump to conclusions and fix what you *think* the problem is. Observe the actual failure, and keep an open mind about mechanisms. — [Inspirezone](https://inspirezone.tech/9-indispensable-rules-for-debugging-software-and-hardware/)
- *Divide and Conquer:* eliminate what is definitely not part of the problem and focus on what's left. Each experiment should isolate a factor: "Does it still fail if this factor is removed?" — [Univ. of Washington CSE 466 lecture on Agans' rules (PDF)](https://courses.cs.washington.edu/courses/cse466/15au/pdfs/lectures/DebuggingRules.pdf)
- **AI agents and root causes.** Anthropic's guidance tells the agent to "address the root cause, don't suppress the error," and to "write a failing test that reproduces the issue, then fix it." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Debugging is the skill most hurt by over-delegation to AI.** In Anthropic's 2026 RCT, the largest mastery deficit in the AI-assisted group was on debugging questions. — [Anthropic, "How AI assistance impacts the formation of coding skills"](https://www.anthropic.com/research/AI-assistance-coding-skills); [InfoQ coverage](https://infoq.com/news/2026/02/ai-coding-skill-formation/)

### Inferences
- **A hypothesis-driven debugging loop** (synthesis of Agans plus the scientific method):
  1. **Reproduce.** Write down the exact steps, input and environment. If possible, capture it as a failing automated test (rule 2, and Anthropic's advice).
  2. **Observe.** Read the actual error, logs and stack trace, and add logging or a debugger breakpoint *before* forming theories (rule 3).
  3. **Hypothesise.** State one falsifiable guess, for example "the cache returns stale data after a timeout."
  4. **Experiment.** Change one thing (rule 5) and predict the result before you run it.
  5. **Bisect.** If it "used to work," binary-search the history with `git bisect` (good/bad commits) or comment out half the pipeline. Each step halves the suspects (rule 4). See the [git-bisect documentation](https://git-scm.com/docs/git-bisect).
  6. **Record.** Keep a running notes file of what you tried and what happened (rule 6). This also helps when you ask a colleague or an AI for a fresh view (rule 8).
  7. **Check the plug.** Wrong branch? Stale build? Wrong environment variable or port? Is the service actually running (rule 7)?
  8. **Verify the fix.** The reproduction test now passes, and it fails again if you revert the fix (rule 9). Keep the test as a regression guard.

### Gaps
- I did not access Agans' book text. The rule explanations come from secondary reviews and a university lecture deck.
- I did not fetch the git-bisect documentation this session. The description given is its standard function: a binary search through commit history to find the change that introduced a bug.

---

## 6. Measuring progress and deciding what to do next (feedback loops, demos, retrospectives, Gall's law)

### Takeaway
Progress means *working, demonstrated behaviour*, not code written. Keep feedback loops short at every scale: tests in seconds, CI in minutes, demos and retrospectives every iteration, delivery metrics over months. Gall's law is the reason to grow a system from a simple working one rather than assembling a big design all at once.

### Cited Findings
- **Gall's law** (John Gall, *Systemantics*, 1975): "A complex system that works is invariably found to have evolved from a simple system that worked." A complex system designed from scratch tends not to work, because it contains too many untested dependencies and interactions at once. — [Matt Rickard, "Gall's Law"](https://blog.matt-rickard.com/p/galls-law); [The Personal MBA](https://personalmba.com/galls-law/); [Laws of Software Engineering](https://lawsofsoftwareengineering.com/laws/galls-law/)
- Caveat: the law says working complex systems come from working simple ones. It does *not* say simplicity guarantees success. — [Andy Matuschak's notes](https://notes.andymatuschak.org/z4GDrXLY7RaUDcvZLim3mfA)
- **Feedback is the point of tracer bullets.** "It all comes down to feedback" (Dave Thomas). — [Artima](https://www.artima.com/articles/tracer-bullets-and-prototypes)
- **Vertical slices give earlier, better feedback** and surface constraints sooner than layer-based work. — [Humanizing Work](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)
- **Team-level delivery metrics.** DORA's five metrics (lead time, deployment frequency, recovery time, change fail rate, rework rate) measure the delivery system. Speed and stability are not trade-offs. — [DORA metrics](https://dora.dev/guides/dora-metrics/)
- **Evidence over assertion.** Claude Code's guidance asks for evidence (test output, the command run and its result, a screenshot) rather than claims of success, because "reviewing evidence is faster than re-running the verification yourself." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **"If you haven't seen it run, it's not a working system."** — [Simon Willison](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)
- **Perceived progress can be wrong.** In METR's RCT (July 2025), 16 experienced open-source developers did 246 real tasks in their own repos. They were about 19% *slower* with early-2025 AI tools, though they forecast a 24% speedup beforehand and still believed afterwards they had been about 20% faster. This was a small sample with early-2025 tools, and other trials (e.g. a Google enterprise study) found speedups. — [eWeek](https://eweek.com/news/news-ai-tools-slow-developer-productivity-study); [The Decoder](https://the-decoder.com/ai-coding-can-make-developers-slower-even-if-they-feel-faster/); [Larridin summary](https://larridin.com/blog/ai-vs-human-developer-productivity)

### Inferences
- **Gall's law applied to execution:**
  1. Get the walking skeleton working (§1).
  2. Add one slice at a time, and confirm the whole system still works after each one.
  3. Never integrate several new components at once. If you must, integrate them one by one behind the existing working path.
  4. When something big fails, retreat to the last working version, the "simple system that worked," and grow it again in smaller steps.
- **Feedback loops at each time scale:**

  | Loop | Time scale | Signal |
  |---|---|---|
  | Type checker / linter / unit tests | seconds | compile errors, failing assertions |
  | Local end-to-end smoke test | a minute | "does the whole path still work?" |
  | CI on every push | minutes | full test suite green on a clean machine |
  | Demo (to yourself, users, team) | per slice / per week | does it do what someone actually needs? |
  | Fixed eval set or benchmark | per significant change | p50/p95 latency, error rates, regressions |
  | Retrospective | per iteration | what slowed us down? what will we change? |
  | DORA-style metrics | monthly | lead time, change fail rate |

- **Deciding what to do next:** after each slice, (a) demo it, (b) look at measurements, (c) pick the next slice that removes the biggest remaining *risk* or delivers the most *value*. Because self-perception is unreliable (METR), base the "are we faster/better?" judgement on measurements, not feelings.
- **A simple solo retrospective** (structure inferred from common agile practice, no source fetched): weekly, write down what went well, what was slow or painful, and one change to try next week.

### Gaps
- I did not fetch a primary source on retrospective formats (e.g. Derby & Larsen, *Agile Retrospectives*) or on demo cadence. The retrospective guidance above is common practice, not sourced.
- I found no empirical study that measures Gall's law directly. It is an aphorism backed by experience, not experiment.

---

## 7. Working effectively with AI coding assistants (2025–2026) without losing your skills

### Takeaway
Current expert guidance converges on: **spec first, then a plan, then small focused steps, each verified by a check the AI can run (tests or a build), committed as save points, and reviewed by a human who stays accountable.** Evidence from 2025–2026 shows two risks. Experienced developers can be slower than they feel (METR), and learners who delegate code generation learn less, especially debugging (Anthropic RCT). Learners who use AI to ask conceptual questions learn as well as those who code by hand.

### Cited Findings
**Workflow guidance**
- **Explore → Plan → Implement → Commit.** "Letting Claude jump straight to coding can produce code that solves the wrong problem." Use plan mode to separate exploration from execution. Skip planning for tiny changes: "If you could describe the diff in one sentence, skip the plan." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Give the agent a verifiable check.** "Give Claude a check it can run: tests, a build, a screenshot to compare." Without one, "'looks done' is the only signal available, and you become the verification loop." Example: write `validateEmail` with listed test cases and "run the tests after implementing." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **For bugs:** "write a failing test that reproduces the issue, then fix it." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Specs.** For larger features, have the AI interview you, write SPEC.md, then start a fresh session to implement it. "The most useful specs are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Manage context.** The context window "is the most important resource to manage." Clear it between unrelated tasks. After two failed corrections, start fresh with a better prompt. — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Independent review.** Use a fresh-context reviewer (Writer/Reviewer sessions or a review subagent) because the author is biased toward its own code. But tell it to flag only correctness or requirement gaps, since chasing every finding "leads to over-engineering." — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Named failure patterns:** the kitchen-sink session, correcting over and over, an over-long CLAUDE.md, the "trust-then-verify gap" ("If you can't verify it, don't ship it"), and infinite exploration. — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **Simon Willison:** treat the LLM as "an over-confident pair programming assistant." "Most of the craft of getting good results out of an LLM comes down to managing its context." For production code, act like you're directing "a digital intern," giving function signatures and precise instructions. "If you haven't seen it run, it's not a working system," and testing cannot be outsourced. "A bad initial result isn't a failure, it's a starting point." Vibe coding is fine for throwaway projects; production needs the controlled process. "Expect to need to take over." — [Simon Willison, "Here's how I use LLMs to help me write code" (Mar 2025)](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)
- **Addy Osmani (going into 2026):** "Don't just throw wishes at the LLM - begin by defining the problem and planning a solution." Spec, then plan (a "waterfall in 15 minutes"), then "feed the LLM manageable tasks, not the whole codebase at once." Pack context with relevant code, docs and constraints. "Stay alert, test often, review always." Commit as "save points." "I remain the accountable engineer." "Be intentional about periodically coding without AI too, to keep your raw skills sharp." — [Addy Osmani, "My LLM coding workflow going into 2026"](https://addyosmani.com/blog/ai-coding-workflow/); ["waterfall in 15 minutes" via secondary coverage](https://hamy.xyz/blog/2026-01_ai-engineering-best-practices)

**Evidence on productivity and skills**
- **METR RCT (July 2025).** Experienced developers were about 19% slower with early-2025 AI tools (mainly Cursor with Claude 3.5/3.7 Sonnet) on tasks in their own large repos, yet believed they were about 20% faster. Small sample (16 developers, 246 tasks); results vary with tools and tasks. — [eWeek](https://eweek.com/news/news-ai-tools-slow-developer-productivity-study); [The Decoder](https://the-decoder.com/ai-coding-can-make-developers-slower-even-if-they-feel-faster/)
- **Anthropic skill-formation RCT (Jan 2026).** 52 mostly junior engineers learned an unfamiliar Python library (Trio). The AI-assisted group scored 17% lower on a mastery quiz (about 50% vs. 67%, "roughly two letter grades"). They finished about 2 minutes faster, which was not statistically significant. The biggest gap was on debugging questions. How people used AI mattered: those who asked conceptual or follow-up questions scored 65% or more, while those who delegated code generation scored below 40%. — [Anthropic research](https://www.anthropic.com/research/AI-assistance-coding-skills); [InfoQ](https://infoq.com/news/2026/02/ai-coding-skill-formation/)
- **Corroboration.** A 2024 peer-reviewed study of 32 undergraduates learning React found negative correlations between LLM use for code generation or debugging and final grades, and no significant negative effect for LLM use for explanations. — reported by [InfoQ](https://infoq.com/news/2026/02/ai-coding-skill-formation/)
- **Critique.** The Anthropic study measures learning a *new library*, not general programming ability. — summarised in [ITPro](https://itpro.com/software/development/anthropic-research-ai-coding-skills-formation-impact) / [Gigazine](https://gigazine.net/gsc_news/en/20260202-ai-assistance-impacts)

### Inferences
- **A concrete AI-assisted execution loop** for an early-career developer, combining the guidance above with §1–§6:
  1. **Spec** (you write it, or the AI interviews you): goal, out-of-scope, interfaces, and an end-to-end acceptance check.
  2. **Plan:** the AI proposes vertical slices. You edit and approve the plan, and you should be able to explain every step.
  3. **For each slice:** you (or the AI) write the failing test or acceptance check first, the AI implements, the check runs, you read the diff line by line, then you commit.
  4. **Review:** a fresh-context reviewer looks for correctness gaps only.
  5. **Demo or measure** before choosing the next slice.
  6. **Reset context** between slices. Keep durable decisions in a short project file (CLAUDE.md, ADRs), not in chat history.
- **Guarding your own skills** (based on the Anthropic RCT finding that *how* you use AI matters):
  - Ask "why" and "explain" questions, not only "write this."
  - Do the debugging reasoning yourself first (form a hypothesis, then ask the AI to check it), because debugging was the most-eroded skill.
  - Hand-write the first version of unfamiliar core concepts, then compare with the AI's.
  - Regularly do small tasks with no AI (Osmani).
  - Never commit code you can't explain (Osmani's "accountable engineer").
- TDD fits AI work especially well. The Fucci finding (small, uniform steps matter most) matches the "small chunks" advice, and tests provide the pass/fail signal agents need to iterate unattended.
- Because perceived speedups can be illusory (METR), measure your own throughput and defect rate with and without AI on comparable tasks before concluding it helps.

### Gaps
- I did not fetch GitHub's official Copilot guidance this session.
- The Anthropic and METR studies use specific tools and time periods (early 2025, Jan 2026). I found no larger 2026 RCT replicating or overturning METR's slowdown result.
- I found no long-term (multi-year) studies of skill atrophy from AI coding assistants. Current evidence is short-term learning studies.
