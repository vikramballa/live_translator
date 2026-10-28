# Building System Design and Coding Skill Through Deliberate Practice

Scope: evidence-based ways a motivated self-taught or early-career developer (possibly a non-native English speaker in India, prefers free resources) can get good at writing code and designing systems. Ends with ingredients for a weekly/monthly practice plan. Research date: 2026-10-19.

## 1. What expertise research (Ericsson / deliberate practice) says, how it applies to programming, and its limits

### Takeaway
Expertise comes from years of practice that is focused, a little beyond your current ability and has fast feedback, not from years of plain experience. But "deliberate practice" in Ericsson's strict sense needs established training methods and a coach, which programming mostly lacks. Programmers therefore do "purposeful practice" and have to design their own feedback. Practice also explains much less of the differences between people in professional fields than the "10,000 hours" story suggests.

### Cited Findings
- Norvig: researchers find "it takes about ten years to develop expertise in any of a wide variety of areas". The key is "deliberative practice: not just doing it again and again, but challenging yourself with a task that is just beyond your current ability". "There appear to be no real shortcuts." He quotes Ericsson's own framing of "years of 10 to 20 hours a week" and says no single number (such as 10,000 hours) fits every skill or person. — [Norvig, Teach Yourself Programming in Ten Years](https://norvig.com/21-days.html)
- Norvig's "recipe": program for fun so you keep going; learn by doing, with "deliberate efforts to improve"; talk with other programmers and read their code ("more important than any book or training course"); work on projects with others (sometimes be the worst, so you learn "what the masters do"); work on projects *after* others (maintain someone else's code); learn about 6 languages from different paradigms; "know your computer" (the time cost of an instruction, a memory fetch, a disk read, a network send). His closing advice is to commit to "working hard to continually improve over 24 months." — [Norvig](https://norvig.com/21-days.html)
- *Peak* (Ericsson & Pool, 2016) puts **mental representations** at the centre of expertise: "a mental structure that corresponds to an object, an idea, a collection of information… that the brain is thinking about". They let experts see patterns novices miss, and deliberate practice both builds them and depends on them. — [Wikipedia: Peak](https://en.wikipedia.org/wiki/Peak:_Secrets_from_the_New_Science_of_Expertise); [Investing by the Books review](https://www.investingbythebooks.com/book-reviews-chronologically/2016/12/13/ericsson-anders-pool-robert-peak-secrets-from-the-new-science-of-expertise)
- Ericsson's **purposeful practice** has four principles: it is focused, it takes you out of your comfort zone, it uses feedback and adjustment, and it has "well-defined, specific goals". **Deliberate practice** adds three more: (1) the field has established training methods, (2) a teacher or coach guides the early stages, (3) practice builds on earlier skills, often with progressively better coaches. Without established methods you "cannot do deliberate practice in its pure form". — [Commoncog, The Problems with Deliberate Practice](https://commoncog.com/the-problems-with-deliberate-practice/)
- Self-learners in fields without established methods face four problems: ill-defined sub-skills (you must design your own syllabus), no feedback (you must invent a substitute), few chances to practise, and plateaus or lost motivation without a coach. Suggested workarounds include decision-making exercises (Gary Klein), comparing your choice with an expert's (as chess players compare their move with a grandmaster's), Franklin-style reconstruction of admired work, spaced repetition (Anki) and reviewing recordings of your own performance. — [Commoncog](https://commoncog.com/the-problems-with-deliberate-practice/)
- **Critique (Macnamara, Hambrick & Oswald 2014, *Psychological Science*):** deliberate practice explained 26% of performance variance in games, 21% in music, 18% in sports, 4% in education and **less than 1% in professions**. — [New Statesman summary](https://www.newstatesman.com/science-tech/2014/08/when-it-comes-expertise-10000-hours-practice-isn-t-enough); [Stafforini bibliography entry](https://stafforini.com/works/macnamara-2014-deliberate-practice-and/)
- **Counter-critique:** the meta-analysis defined deliberate practice much more broadly than Ericsson did. A reanalysis that kept only data meeting stricter criteria found that accumulated practice explained 29–61% of variance after attenuation correction. — [Frontiers in Psychology review (2019)](https://frontiersin.org/article/10.3389/fpsyg.2019.02396/full); [Progress Focused critique](https://progressfocused.com/2014/11/macnamara-et-al-2014-meta-analysis-on.html)
- Macnamara et al. 2016 (sports): deliberate practice explained 18% of variance overall but only **1% among elite performers**, so practice separates beginners from good performers more than it separates good from great. — [Macnamara et al. 2016 PDF (Purdue)](https://hhs.purdue.edu/skill-learning-and-performance-lab/wp-content/uploads/sites/43/2024/08/macnamara-et-al-2016-the-relationship-between-deliberate-practice-and-performance-in-sports-a-meta-analysis.pdf)
- Dan Luu's argument: reaching about the 95th percentile is "not very hard" because "relatively few people are trying to improve at all". People "improve slowly when getting feedback would make improving quickly easy". Programming example: Michael Malis recorded his screen for a week, found he spent "about a quarter of the total time implementing the feature tracking down which functions the bugs were in", and fixed it by testing each function as he wrote it. Luu: "One incredibly useful exercise I've found is to watch myself program." — [Dan Luu, 95%-ile isn't that good](https://danluu.com/p95-skill/)

### Inferences
- For programming, the realistic goal is **purposeful practice with home-made feedback** (tests, benchmarks, reference implementations, code review, comparing your design with a published real-world design), not Ericsson's coached deliberate practice.
- The "<1% in professions" figure is a warning against judging progress by hours logged. Count closed feedback loops instead (bugs found and explained, designs compared with a reference, reviews received).
- Because elite-level differences are only weakly explained by practice, a learner should aim to become a solid, reliable engineer (the "95th percentile of people who try"), which the evidence supports, rather than chase "10x".
- "Mental representations" are what software engineers call design intuition or mental models. Every exercise below should be judged by whether it builds one: can you predict how the system behaves before you run it?

### Gaps
- I found no controlled study of deliberate practice specifically among professional programmers. Applying it to software is by analogy.
- I did not get a primary text listing Ericsson's components from *Peak* itself, only secondary summaries (Commoncog is the most careful of them).

## 2. Practice methods experienced engineers recommend

### Takeaway
The methods that recur most are: build real things end to end; rebuild existing systems from scratch ("build your own X"); read and maintain other people's code; write design docs; and use small graded exercises (katas, about 100 LeetCode-style problems) for fluency. Each works best when it has a built-in check: a test suite, a reference implementation or a reviewer.

### Cited Findings
- **Build your own X** (CodeCrafters' GitHub list, about 554k stars): "Master programming by recreating your favorite technologies from scratch", under the Feynman motto "What I cannot create, I do not understand". It has 30 categories, among them database, Docker, emulator/VM, Git, memory allocator, network stack, OS, programming language, regex engine, search engine, shell, text editor, web browser, web server, BitTorrent client, neural network and AI model. Examples: "Let's Build a Simple Database" (C), "Build Your Own Redis from Scratch" (C++/Go), "Write yourself a Git!" (Python), "Linux containers in 500 lines of code" (C), "Let's code a TCP/IP stack" (C), "Beej's Guide to Network Programming". — [github.com/codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)
- **500 Lines or Less** (the AOSA series): each chapter solves a classic software problem in at most 500 lines and focuses on design decisions and trade-offs, such as how to split an application into modules. It is free online; text is CC-BY and code is MIT on GitHub (aosabook/500lines). — [aosabook.org](https://aosabook.org/en/); [emptysqua.re announcement](https://emptysqua.re/blog/architecture-open-source-applications-500-lines-published/)
- **Read code and work on others' code:** "Talk with other programmers and read their code: this is more important than any book or training course". "Work on projects after other programmers": maintain and understand inherited code, and design your own code so later maintainers can follow it. — [Norvig](https://norvig.com/21-days.html)
- **Small exercises:** teachyourselfcs recommends solving about 100 LeetCode problems while studying, plus Exercism for small programming exercises. — [teachyourselfcs.com](https://teachyourselfcs.com/)
- **Design docs as practice (Google):** informal documents written before coding that record "the high-level implementation strategy and key design decisions with emphasis on the trade-offs". Sections: context and scope; goals and **non-goals**; the design (system-context diagram, API sketch, data storage); **alternatives considered**; cross-cutting concerns (security, privacy, observability). Length is 10–20 pages for big projects or a 1–3 page "mini design doc". Skip one when the solution is obvious and has few trade-offs. Benefits: "early identification of design issues when making changes is still cheap", consensus, "scaling knowledge of senior engineers into the organization", organisational memory, and a portfolio record. — [Malte Ubl, Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- **Mock system design exercises:** the System Design Primer (about 375k stars) gives a 4-step method: (1) use cases, constraints, assumptions (users, traffic, read/write ratio); (2) high-level design; (3) core components (storage, schema, APIs); (4) scaling (load balancers, caching, sharding, queues) with trade-offs, plus back-of-the-envelope estimates (powers-of-two table, latency numbers). It has short/medium/long study plans and Anki decks for spaced repetition. — [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)
- **Self-observation as practice:** record your screen, find where the time went, and change the habit (for example, test each function as you write it). — [Dan Luu](https://danluu.com/p95-skill/)
- **roadmap.sh backend beginner path:** a language, then its package manager, a relational DB (PostgreSQL) with CRUD, optionally a framework, then a simple REST API with authentication/authorisation, learning Git throughout. It says to "build many projects while learning". — [roadmap.sh/backend](https://roadmap.sh/backend)

### Inferences
- A good weekly mix: one **"rebuild X" project** (for depth and understanding of internals), one **real end-to-end project** (deployment, users, operations: the parts tutorials skip), and short **daily reps** (katas, LeetCode, Exercism) for fluency.
- CodeCrafters' paid tracks (Redis, Git, SQLite, HTTP server, DNS, Kafka and others) give automated test feedback at each stage. The free build-your-own-x tutorials don't, so add your own tests or compare against the real tool (for example, run the real `redis-cli` against your server).
- Writing a 1–3 page mini design doc *before* each project, then a short "what I got wrong" note after, turns ordinary building into practice with feedback (your own past predictions are the reference).
- Post-mortems: write a blameless post-mortem for your own bugs and outages (timeline, root cause, what would have caught it). This is a practice I'm inferring from industry norms; see Gaps.

### Gaps
- I didn't fetch codecrafters.io directly, so its current track list, pricing and free tiers are unverified.
- Will Larson's writing on learning architecture (lethain.com, staffeng.com) couldn't be retrieved: two guessed URLs returned 404. His advice is not cited here.
- I found no direct source on personal post-mortems or code katas (for example, Dave Thomas's CodeKata) in this pass.
- I found no empirical comparison of "build your own X" against ordinary project work.

## 3. How experts build mental models and design intuition

### Takeaway
Intuition comes from a large store of worked examples (real architectures and the trade-offs behind them) plus first-hand experiments that test your model against reality. Study a real design, predict its behaviour, then check.

### Cited Findings
- *The Architecture of Open Source Applications* (free at aosabook.org) is written for "intermediate or senior developer[s]" who "want to see how your peers have solved hard design problems". Volumes 1–2 have chapter-per-system architecture write-ups, and *500 Lines or Less* covers small designs. — [aosabook.org](https://aosabook.org/en/)
- The System Design Primer tells learners to "skim engineering blogs" and "review a few real-world architectures" as part of every study plan, and it is organised around trade-offs: performance vs scalability, latency vs throughput, availability vs consistency (CAP). — [System Design Primer](https://github.com/donnemartin/system-design-primer)
- teachyourselfcs's top two books if nine subjects is too many: *Computer Systems: A Programmer's Perspective* and *Designing Data-Intensive Applications*. For a trendy technology, "work backward from the technology to the underlying concept". — [teachyourselfcs.com](https://teachyourselfcs.com/)
- Julia Evans on building mental models: treat bugs and the feeling of "wait, I'm really confused" as signs of a missing concept. Seniority is "quickly being able to recognize when you don't know something and learn it". Break vague confusion into specific factual questions; ask **yes/no questions** (they force you to state your current model); "ask the computer" with small experiments (atomics vs mutexes, how SQLite lays data out on disk); learn a few facts at a time; keep a list of what you don't know yet (isolation levels, BGP) and learn each when it becomes relevant. "The whole point of understanding how computers work is to actually write code to make them do things!" — [Julia Evans, jvns.ca](https://jvns.ca/blog/learn-how-things-work/)
- Norvig's "know your computer": know the time to run an instruction, fetch from memory, read from disk and send over the network. — [Norvig](https://norvig.com/21-days.html)
- Expert "mental representations" let experts see patterns that novices miss. — [Wikipedia: Peak](https://en.wikipedia.org/wiki/Peak:_Secrets_from_the_New_Science_of_Expertise)

### Inferences
- A repeatable "case study drill" (inferred from the sources above): read the problem section of an AOSA chapter or an engineering-blog post, write your own one-page design first, *then* read theirs and list the differences. This is the chess "compare your move to the grandmaster's" method from section 1, applied to design.
- Keep a personal "latency and capacity numbers" sheet and use it in every design (back-of-the-envelope maths). That habit is what makes intuitions numerical.
- Julia Evans-style experiments (writing a 20-line program to test one assumption) are the cheapest feedback loop there is, and they suit a self-taught learner with no mentor.

### Gaps
- I didn't fetch highscalability.com or specific company engineering blogs. Whether highscalability is still active in 2026 is unverified.
- I found no empirical research on how software architects specifically acquire design intuition (for example, studies of novice versus expert designers) in this pass.

## 4. The role of feedback: code review, mentorship, open source, writing/teaching, journals and decision logs

### Takeaway
Feedback is the scarce ingredient for a self-taught developer. Code review's main proven benefit is knowledge transfer, not catching bugs. Writing (design docs, decision logs, explanations) gives you a record your later self can grade. Spaced self-testing is the best-supported way to retain concepts.

### Cited Findings
- Bacchelli & Bird (ICSE 2013, Microsoft): finding defects is the main *stated* motivation for review, but reviews "are less about defects than expected and instead provide additional benefits such as **knowledge transfer**, increased team awareness, and creation of alternative solutions to problems". "Code and change understanding is the key aspect of code reviewing." A secondary summary reports the method as a survey of 873 programmers and 165 managers, 17 interviews and 570 hand-analysed review comments. — [Microsoft Research](https://microsoft.com/en-us/research/?p=164195); [PDF (UMich)](https://web.eecs.umich.edu/~weimerw/2018-481/readings/codereview.pdf); method figures from [getdx summary](https://getdx.com/research/outcomes-and-challenges-of-code-review/)
- Design docs serve as "organizational memory" (they record why a decision was made) and as a portfolio artefact for the designer. — [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Learning science (Dunlosky et al. 2013, *Psychological Science in the Public Interest* 14(1), 4–58): of 10 techniques, **practice testing** (self-quizzing) and **distributed practice** (spacing study over time; longer intervals beat short ones) got the highest utility rating. **Summarisation, highlighting and rereading were rated low.** Even "stopping during study to think of questions about the material and answering them" helps. — [APS press release](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html); [ScienceDaily](https://www.sciencedaily.com/releases/2013/01/130110111734.htm)
- Dan Luu's Overwatch example: players who finally posted recordings and asked for feedback often jumped several percentile points. Most people never review their own replays. — [Dan Luu](https://danluu.com/p95-skill/)
- Mentorship: Norvig quotes Fred Brooks's plan for growing great designers, which includes assigning a career mentor and letting growing designers interact with each other. Norvig's own advice is to work on projects where you are sometimes the worst programmer. — [Norvig](https://norvig.com/21-days.html)
- Feynman framing ("What I cannot create, I do not understand") is the motto of the build-your-own-x movement. — [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)

### Inferences
- **Code review substitutes for a self-taught learner:** (a) open-source PRs, where maintainers review your code; (b) reviewing *others'* merged PRs in a well-run project and comparing your comments with the maintainers' comments; (c) an AI reviewer asked only to critique, never to rewrite (see section 5); (d) a peer study group swapping PRs weekly.
- An **engineering journal / decision log** (date, decision, alternatives, why, what I expect to happen, later check) is the software version of reviewing your replays. It turns past predictions into feedback. This project's own ADR habit (docs/adr/) is exactly this practice.
- Writing explanations (blog posts, internal notes, teaching a friend in your own language) works like self-testing. Plain rereading or highlighting of docs and books is low-value per Dunlosky.
- Put key concepts (latency numbers, consistency models, Big-O, SQL isolation levels) into spaced-repetition flashcards. The System Design Primer ships ready-made Anki decks.

### Gaps
- I did not retrieve a quantitative study on open-source contribution as a learning method, or on the effect of mentorship on developer skill growth.
- I found no study specifically on engineering journals or decision logs as learning tools; the recommendation rests on the general self-feedback principle.
- Dunlosky's ratings for self-explanation, elaborative interrogation and interleaving (I recall they were rated "moderate") were not confirmed in the sources fetched; [VERIFY].
- I did not fetch anything on the "Feynman technique" beyond the quote.

## 5. Using AI coding assistants to learn rather than become dependent (2024–2026 evidence)

### Takeaway
The best causal evidence (Anthropic's 2026 randomised trial) shows that handing code-writing to AI while learning something new cuts mastery sharply (17 points lower on the quiz, worst on debugging) and barely saves time. *How* you use AI matters: asking conceptual questions and asking for explanations kept learning intact. Use AI as a tutor and critic, not a ghostwriter, and accept some productive struggle.

### Cited Findings
- **Anthropic RCT, "How AI Impacts Skill Formation"** (Judy Hanwen Shen & Alex Tamkin, arXiv:2601.20245, blog 2026-01-29): 52 mostly junior engineers (Python weekly for more than a year, new to the library) learned **Trio** (an async Python library), coded two features, then took a quiz. The AI group was about 2 minutes faster (**not statistically significant**) and scored **50% vs 67%** (17 points lower, "nearly two letter grades", Cohen's d = 0.738, p = 0.01). The **biggest gap was on debugging**. Some participants spent up to 11 minutes (30% of the time) writing up to 15 queries. — [Anthropic research](https://www.anthropic.com/research/AI-assistance-coding-skills); [InfoQ](https://infoq.com/news/2026/02/ai-coding-skill-formation/)
  - Low-scoring patterns (average under 40%): **AI delegation** (fastest, few errors, learned least); **progressive AI reliance** (asked a few questions, then delegated); **iterative AI debugging** (used AI to fix or verify instead of to understand; also slower).
  - High-scoring patterns (65% or more): **generation-then-comprehension** (generate, then ask follow-up questions to understand); **hybrid code-explanation** (ask for code *with* explanations); **conceptual inquiry** (asked only conceptual questions and fixed errors themselves; hit many errors but was the fastest of the high-scoring patterns). These patterns are correlational, not causal.
  - Recommendations: use AI to build understanding; accept "productive struggle" ("cognitive effort, including getting stuck, matters for building mastery"); use learning modes (Claude Code's Learning/Explanatory output styles, ChatGPT Study Mode). Limitations: small sample, short-term quiz, a single library, and a chat sidebar rather than agentic tools (the authors expect agentic tools could have *larger* effects).
- **METR RCT (July 2025):** 16 experienced open-source developers, 246 real tasks in their own large repositories. With early-2025 AI tools allowed, tasks took **19% longer**. Developers had predicted a 24% speed-up and *afterwards still believed* they had been about 20% faster. METR warns against generalising: familiarity with the repository and its size and maturity contributed, and greenfield or unfamiliar-code work may see real speed-ups. A follow-up hinted at speed-ups with newer tools, but selection effects made the size unreliable. — [METR blog](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/); [Simon Willison commentary](https://simonwillison.net/2025/Jul/12/ai-open-source-productivity/); follow-up and Google 96-engineer RCT (about 21% faster, wide confidence interval) reported via search summary only, [VERIFY] against primary sources.
- **Microsoft Research / CMU (Lee et al., CHI 2025):** a survey of 319 knowledge workers with 936 examples. **Higher confidence in GenAI went with less critical thinking**; higher *self*-confidence went with more. GenAI shifts critical thinking toward verifying information, integrating responses and stewarding the task, and "can inhibit critical engagement with work and can potentially lead to long-term overreliance on the tool and diminished skill for independent problem solving". The data are self-reported. — [Microsoft Research](https://www.microsoft.com/en-us/research/?p=1135061); [PDF](https://advait.org/files/lee_2025_ai_critical_thinking_survey.pdf); [The Register](https://www.theregister.com/2025/02/11/microsoft_study_ai_critical_thinking/)
- **MIT Media Lab, "Your Brain on ChatGPT"** (arXiv:2506.08872, 2025, **not peer-reviewed**): 54 students wrote SAT essays as LLM, search-engine or brain-only groups, with EEG recorded. The brain-only group showed the strongest neural connectivity. LLM users felt less ownership and recalled their own essays poorly, and engagement stayed low when they switched to writing without the tool. The authors call this "cognitive debt". Critics cite the small sample and the lack of independent vetting, and one reads the lower activity as possibly efficient adaptation. — [MIT Media Lab](https://www.media.mit.edu/publications/your-brain-on-chatgpt/); [The Decoder](https://the-decoder.com/mit-study-shows-cognitive-debt-through-chatgpt-heres-what-it-means-in-real-world-practice/); [Substack critique](https://mikkelfrimerrasmussen.substack.com/p/your-brain-on-chatgpt-myth-or-mechanism?open=false)
- **Practitioner guidance:** GitHub's 2025 advice to juniors puts "use AI to learn faster, not just code faster" first. CTOs surveyed by Sifted say fundamentals (algorithms, data structures, system design, version control, debugging) "still essential". A common practitioner rule: analyse the root cause yourself before asking AI. — [GitHub blog](https://github.blog/ai-and-ml/generative-ai/junior-developers-arent-obsolete-heres-how-to-thrive-in-the-age-of-ai/); [Sifted](https://sifted.eu/articles/junior-engineers-level-up-ai); [DEV Community guidelines](https://dev.to/hiro0218/ai-utilization-guidelines-for-continuous-engineer-growth-20df)

### Inferences
- **AI rules for learning sessions**, drawn from the high-scoring patterns: (1) try it yourself first, for a fixed time (for example 20–30 minutes) before asking; (2) ask *conceptual* questions ("why does Trio need a nursery?") rather than "write it"; (3) if you do generate code, you must be able to explain every line and rewrite it from memory; (4) debug yourself first. Debugging was the skill most damaged by delegation, so treat the debugger as a no-AI zone in practice sessions; (5) use AI as a reviewer ("critique this design: what fails at 10× load?") and a Socratic tutor, not an author; (6) turn on learning modes where available.
- Separate **"learning mode" days** (mostly no AI, or AI as tutor only) from **"shipping mode" days** (full AI). The skill-formation evidence applies when learning something new. The METR evidence suggests that even when shipping, perceived speed-ups can be illusory, so measure real time.
- METR's perception gap (believed 20% faster, was 19% slower) is a strong argument for keeping a time log or journal rather than trusting your impression.
- For a non-native English speaker, asking the AI to explain concepts in Telugu/Hindi and then restating them in English (or the reverse) is a cheap form of self-explanation. This is my suggestion and has not been tested.

### Gaps
- No long-term (months or more) study of AI use and skill retention among programmers was found. The Anthropic study measured right after the task.
- No RCT on *agentic* tools (Claude Code, Cursor agents) and learning was found; Anthropic's authors flag this as a likely bigger effect.
- I didn't find a Pragmatic Engineer (Gergely Orosz) article specifically on juniors learning with AI in this pass.

## 6. Learning roadmaps from reputable sources (fundamentals)

### Takeaway
The two most credible free roadmaps agree: learn to build a working CRUD/API backend first (roadmap.sh), then systematically study about 9 CS fundamentals at 100–200 hours each (teachyourselfcs). If time is short, prioritise *Computer Systems: A Programmer's Perspective* and *Designing Data-Intensive Applications*.

### Cited Findings
- **teachyourselfcs.com**: 9 subjects, each with a book and a free video course. Programming: SICP + Berkeley CS 61A. Architecture: CS:APP + Berkeley CS 61C. Algorithms: Skiena's *Algorithm Design Manual* + his lectures. Math: MIT 6.042J *Mathematics for CS*. OS: *OSTEP* (free) + Berkeley CS 162. Networking: Kurose & Ross *Top-Down Approach* + Stanford CS 144. Databases: *Readings in Database Systems* (Red Book) + Berkeley CS 186. Languages/compilers: *Crafting Interpreters* (free online) + Aiken's compilers course. Distributed systems: *DDIA* + MIT 6.824. "Aim for 100–200 hours on each topic." Rough order with flexibility; prerequisites are architecture before OS/DB, and networking + OS before distributed systems. It is **not for absolute beginners** ("learn to code first… return to this one in a year or two"). If SICP doesn't suit you, try *Composing Programs*, then *How to Design Programs*. Learning new languages is "much easier and less valuable" than CS concepts. Solve about 100 LeetCode problems along the way. Buy cheap used older editions. — [teachyourselfcs.com](https://teachyourselfcs.com/)
- teachyourselfcs's "Type 1 vs Type 2 engineer" argument: Type 2 engineers know a few high-level tools at surface level, and their supply is growing faster than CS graduates, which threatens their prospects. Type 1 engineers (deep CS) move toward more fulfilling, better-paid work over time. — [teachyourselfcs.com](https://teachyourselfcs.com/)
- **roadmap.sh backend** beginner path: language, package manager, PostgreSQL + CRUD, (framework), REST API + authentication, with Git throughout. "Build many projects while learning"; the roadmap shows "the landscape and what you may be missing". The page gives no time estimate. — [roadmap.sh/backend](https://roadmap.sh/backend)
- **System Design Primer** for the systems layer: DNS, CDN, load balancers, reverse proxies, SQL vs NoSQL, replication, sharding, caching, queues and back pressure, HTTP/TCP/UDP/RPC/REST, with short/medium/long plans. — [System Design Primer](https://github.com/donnemartin/system-design-primer)
- Norvig: languages across paradigms (object-oriented, functional, declarative, concurrency-focused such as Go/Clojure). — [Norvig](https://norvig.com/21-days.html)

### Inferences
- A sensible order for a self-taught developer: (Phase A) roadmap.sh-style practical backend + Git, plus a deployed project; (Phase B) CS:APP and OSTEP and networking alongside "build your own" shell/HTTP server/Redis, so theory and rebuilds reinforce each other; (Phase C) databases + DDIA + System Design Primer, alongside rebuilding a key-value store / SQLite clone and design-doc drills; (Phase D) distributed systems (MIT 6.824 labs are free and test-graded, a strong feedback source).
- 9 subjects × 100–200 hours ≈ **900–1,800 hours**. At 10 hours a week that is about 2–3.5 years; at 15–20 hours a week, about 1–2 years. This is consistent with Norvig's multi-year framing.
- Free-resource note for India: OSTEP, *Crafting Interpreters*, the System Design Primer, AOSA/500 Lines, MIT/Berkeley/Stanford lecture videos, Exercism and the build-your-own-x tutorials are all free. Used Indian editions of CS:APP, Kurose and DDIA are typically cheap (not verified here).

### Gaps
- roadmap.sh's full ordered node list couldn't be extracted (the diagram isn't in the page text). Only the FAQ path is cited.
- I didn't check whether teachyourselfcs has updated any recommendations recently (for example, a DDIA 2nd edition).

## 7. Realistic timelines, milestones and ingredients for a weekly/monthly practice plan

### Takeaway
Plan in years, not weeks: about 2 years of steady improvement for solid competence (Norvig's "24 months") and about 10 years for deep expertise. Progress should be measured by feedback-producing milestones (a shipped project, a passing rebuild test suite, a merged open-source PR, a design doc compared with a real system) rather than hours.

### Cited Findings
- About 10 years for expertise across many fields, at "10 to 20 hours a week" (Ericsson as quoted by Norvig). Norvig's actionable horizon is "continually improve over 24 months". — [Norvig](https://norvig.com/21-days.html)
- 100–200 hours per CS subject across 9 subjects; teachyourselfcs suggests absolute beginners code for "a year or two" first. — [teachyourselfcs.com](https://teachyourselfcs.com/)
- Practice explains much less variance at elite levels (1% among elite athletes) and in professions (under 1% per Macnamara 2014, disputed), so timelines are averages with large individual variation. — [Macnamara 2016](https://hhs.purdue.edu/skill-learning-and-performance-lab/wp-content/uploads/sites/43/2024/08/macnamara-et-al-2016-the-relationship-between-deliberate-practice-and-performance-in-sports-a-meta-analysis.pdf); [New Statesman](https://www.newstatesman.com/science-tech/2014/08/when-it-comes-expertise-10000-hours-practice-isn-t-enough)
- Spaced practice beats massed practice, and longer gaps beat short ones. — [APS](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html)
- Modest but *deliberate* effort puts you ahead of most participants. — [Dan Luu](https://danluu.com/p95-skill/)

### Inferences (practice plan ingredients, built from all sections above)

**Weekly template (about 10–15 hours; scale up or down):**
- **Daily, 30–45 min, "reps":** 1 algorithm/kata problem (LeetCode/Exercism) solved *without AI*, then compared with the best solutions. Plus 10 minutes of Anki review (System Design Primer decks + your own cards from mistakes).
- **3 sessions × 1.5–2 h, "build":** work on the current "build your own X" or real project. Rule: write the test (or the comparison against the real tool) before the feature. Use AI only in "conceptual inquiry / explain" mode on learning days.
- **1 session × 2 h, "theory":** one chapter from the current teachyourselfcs subject (for example, an OSTEP chapter), then close the book and write a half-page explanation from memory (self-testing, not rereading), and do one Julia Evans-style experiment that tests a claim from the chapter.
- **1 session × 1–1.5 h, "design drill":** pick a real system (an AOSA chapter, an engineering-blog post, or a System Design Primer question). Write a 1–2 page mini design doc first (goals/non-goals, design, alternatives, back-of-the-envelope numbers), *then* read the real answer and log the differences.
- **1 session × 1 h, "feedback":** review one merged PR in a quality open-source project (compare your comments with the maintainers'), *or* open/iterate on your own PR, *or* swap code reviews with a peer. Ask an AI to *critique* (never rewrite) one piece of your week's code.
- **Weekly 20-min retro in the engineering journal:** what I built; one bug and its root cause (mini post-mortem); one decision with alternatives (ADR style); time actually spent (from a log, since METR shows self-estimates are unreliable); next week's single focus sub-skill.

**Monthly cadence:**
- Finish (or reach the next stage of) one rebuild project. Write a short public blog post / README explaining how it works (teaching as self-test; public writing also creates feedback).
- One full mock system design (45–60 min, timed, 4-step method), ideally with a peer or recorded and reviewed later (Luu's "watch yourself" method).
- Re-read last month's journal and design docs and grade your past predictions.
- One "no-AI day" of building, to check whether you can still debug and write the code unaided (the skill most damaged in the Anthropic RCT).

**Milestones (inferred; personal pace will vary):**
- **Months 0–3:** a deployed CRUD/REST app with authentication + Postgres + Git (roadmap.sh path); 30+ problems; first rebuild (shell or HTTP server).
- **Months 3–9:** Redis-clone or Git-clone passing a test suite; CS:APP + OSTEP core chapters; first merged open-source PR; 5 design drills logged.
- **Months 9–18:** a SQLite/KV-store rebuild; networking + databases subjects; DDIA read with notes; about 100 problems; 15+ design docs; a real project with users, monitoring and one written post-mortem.
- **Months 18–36:** distributed systems (MIT 6.824 labs); remaining teachyourselfcs subjects (about 900–1,800 hours total); regular open-source reviews or contributions; able to write a 5–10 page design doc with credible alternatives and capacity numbers.

**Guardrails:** count feedback loops, not hours; keep learning-mode AI rules (try first → conceptual questions → explain every line → debug yourself); space topics over time rather than cramming; pick one sub-skill per week (purposeful practice needs "well-defined, specific goals").

### Gaps
- I found no credible source giving empirically measured timelines for self-taught developers to reach junior/mid/senior competence. The milestones above are my inferences from the hour estimates and are not measured data.
- I found no India-specific data (cost of resources, peer communities, hiring expectations) in this pass.
- I didn't find evidence on the best ratio of project work to fundamentals study.
