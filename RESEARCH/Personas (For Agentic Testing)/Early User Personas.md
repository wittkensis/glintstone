# Glintstone User Personas

**Purpose:** These personas represent the spectrum of end-users for the Glintstone cuneiform artifact processing platform. They are designed to be used as inputs for simulated user validation, user testing, and product decision-making.

**Based on:** Data Architecture document, Academic Workflow Report, Hobbyist Feedback Report, and cuneiform translation landscape research.

---

## Primary Personas

These are the core users the platform must serve well from launch.

---

### 1. Marcus Chen — "The Weekend Warrior"

**Role:** Hobbyist Volunteer
**Age:** 38
**Location:** Portland, OR
**Occupation:** Senior Software Engineer at a fintech company

#### Background
Marcus has a BA in History (focus on ancient civilizations) but pivoted to software engineering for career stability. He browses r/cuneiform occasionally and has read popular books about Mesopotamia. He has no formal training in Assyriology and cannot read cuneiform, but finds the idea of "helping decode humanity's oldest writing" genuinely exciting. His company gives him 20 hours of volunteer time per year.

#### Time Budget
- 5-10 hours/week for hobbies (shared with woodworking, gaming)
- 2-3 hours/week realistically available for Glintstone
- Prefers 10-15 minute sessions during lunch breaks or before bed

#### Primary Goals
1. Contribute something meaningful during limited free time
2. Learn about ancient history without formal study commitment
3. Escape doom-scrolling with something that feels productive
4. Have something interesting to mention at dinner parties

#### Key Needs from the System
- **Immediate value clarity:** Must understand what he's doing and why within 90 seconds
- **Task duration transparency:** Needs to know if a task fits his available time before starting
- **Low cognitive load:** Visual tasks he can do without learning cuneiform
- **Progress visibility:** Concrete evidence his contributions matter
- **Mobile-first:** Does most hobby activities on his phone

#### Pain Points & Frustrations
- Intimidated by academic jargon ("logograms," "determinatives")
- Fear of "messing up" and wasting expert time
- Uncertainty about whether his work actually helps
- Long tutorials that delay actual contribution
- Lack of clear stopping points in task flows

#### Specific Use Cases for Testing
1. **First-time onboarding:** Can he complete a meaningful task within 5 minutes of landing on the site?
2. **Sign matching task:** Can he successfully match cuneiform signs without prior training?
3. **Session resumption:** If interrupted, can he return and pick up where he left off?
4. **Progress tracking:** Does he understand his cumulative impact after 10 sessions?
5. **Mobile contribution:** Can he complete tasks effectively on an iPhone during a commute?

#### Success Metrics
- Completes first task within 5 minutes of arrival
- Returns for a second session within 7 days
- Reports feeling "my contribution was valuable" in post-session feedback
- Achieves 10+ contributions per active hour
- NPS score > 50

#### Quotes (Simulated)
> "I have 15 minutes before my kid wakes up. Can I actually do something useful in that time?"

> "I don't need to become an expert. I just want to help in whatever way I can."

> "If I can't tell whether my work mattered, I'm not coming back."

---

### 2. Dr. Fatima Al-Rashid — "The Domain Expert"

**Role:** Senior Assyriologist / Expert Reviewer
**Age:** 52
**Location:** Berlin, Germany
**Occupation:** Professor of Ancient Near Eastern Studies, Freie Universität Berlin

#### Background
Dr. Al-Rashid has spent 28 years studying Neo-Assyrian royal inscriptions. She has published extensively in major journals (ZA, JCS, NABU), served on the CDLI advisory board, and collated tablets at the British Museum, Louvre, and Vorderasiatisches Museum. She is skeptical of AI but open to tools that genuinely accelerate her work. She personally knows most of the ~100 specialists in her subfield.

#### Time Budget
- Research: 15-20 hours/week during semester, 30+ during breaks
- Platform engagement: Would dedicate 2-4 hours/week IF the platform proves valuable
- Review tasks: Prefers batching 5-10 reviews in focused 1-hour sessions

#### Primary Goals
1. Accelerate her own research pipeline
2. Ensure quality control on AI-assisted content before it corrupts the scholarly record
3. Maintain attribution standards and protect her intellectual contributions
4. Train the next generation of Assyriologists effectively

#### Key Needs from the System
- **Integration with existing tools:** Must export to ATF format, sync with CDLI P-numbers
- **Granular attribution:** Every contribution type tracked and credited separately
- **Review authority:** Clear mechanisms to accept, reject, or modify proposed content
- **Transparent AI disclosure:** Must know when content is AI-generated and with what confidence
- **Scholarly credibility signals:** Advisory board, peer endorsements, institutional partnerships

#### Pain Points & Frustrations
- AI "hallucinations" that produce plausible-sounding but fabricated content
- Loss of nuance when AI flattens interpretive complexity
- Fear of deskilling among students who rely on AI without understanding
- Unclear attribution when AI and humans collaborate
- Platforms that promise much but disappear after funding ends

#### Specific Use Cases for Testing
1. **Expert review workflow:** Can she efficiently review 10 pending transliterations in one session?
2. **Confidence indicators:** Does she trust the system's confidence scores? Are they calibrated to her expectations?
3. **Attribution tracking:** Can she verify how her contributions are credited in exported content?
4. **Disagreement handling:** When she disputes a reading, is there a clear resolution pathway?
5. **CDLI integration:** Can she import a tablet by P-number and see Glintstone's proposed transcription alongside CDLI's?

#### Success Metrics
- >70% of reviewed AI-assisted content accepted without modification
- Time-to-review reduced by 50% compared to traditional methods
- Would recommend platform to colleagues (target: >60%)
- Cites platform content in her own published research

#### Quotes (Simulated)
> "I don't mind reviewing AI output, but I need to know exactly what it's claiming and why."

> "If this platform produces even one widely-cited error, the field will never trust it."

> "Attribution isn't vanity—it's how scholarship works. Get this wrong and you lose us."

---

### 3. Aisha Okonkwo — "The Aspiring Scholar"

**Role:** Graduate Student (PhD Candidate)
**Age:** 29
**Location:** Philadelphia, PA
**Occupation:** PhD student, Ancient Near Eastern Studies, University of Pennsylvania

#### Background
Aisha is in year 4 of her PhD, working on Ur III administrative tablets from Nippur. She reads Sumerian competently and is developing Akkadian skills. She's digitally native, comfortable with computational tools, and sees AI as potentially transformative for her field. Her dissertation involves transcribing ~200 tablets from Penn Museum storage, many unpublished.

#### Time Budget
- Research: 40-50 hours/week
- Platform engagement: Could integrate into daily workflow if valuable
- Learning new tools: Willing to invest 5-10 hours upfront for significant payoff

#### Primary Goals
1. Accelerate her dissertation transcription work
2. Build professional reputation before job market
3. Contribute to the field while learning from experts
4. Access tablets she can't physically examine

#### Key Needs from the System
- **Workflow acceleration:** AI-generated first drafts she can correct, not blank canvases
- **Learning scaffolding:** Feedback on her transcriptions from expert reviewers
- **Publication pathway:** How does Glintstone work fit into her eventual dissertation?
- **Attribution protection:** Clear credit for her contributions, even if AI-assisted
- **Parallel access:** Compare her readings with CDLI, Oracc, and expert suggestions

#### Pain Points & Frustrations
- Time pressure to produce transcriptions for dissertation
- Limited access to tablets in distant museum collections
- Uncertain how AI contributions will be viewed by hiring committees
- Fear of making errors that damage her professional reputation
- Advisor skepticism about "digital shortcuts"

#### Specific Use Cases for Testing
1. **Bulk transcription workflow:** Can she process 20 tablets per week using AI assistance?
2. **Learning from corrections:** When experts modify her submissions, can she see why?
3. **Export for dissertation:** Can she generate properly formatted editions for her chapters?
4. **Image comparison:** Can she toggle between high-res tablet photos and proposed readings?
5. **Mentor review:** Can she request review from specific experts in her network?

#### Success Metrics
- 5-10x acceleration in first-draft transcription
- >80% of her submissions accepted by expert review
- Would recommend to fellow graduate students
- Contributions cited in her dissertation

#### Quotes (Simulated)
> "I need this to make me faster, not replace my skills. My career depends on demonstrating expertise."

> "If my advisor sees 'AI-assisted' on my transcriptions, will they take my dissertation seriously?"

> "I'd love feedback from Dr. Al-Rashid on my readings, but I don't want to waste her time with beginner mistakes."

---

### 4. Jonathan Hartley — "The Institutional Steward"

**Role:** Museum Curator / Collection Manager
**Age:** 45
**Location:** London, UK
**Occupation:** Curator of Cuneiform Collections, British Museum

#### Background
Jonathan manages access to one of the world's largest cuneiform collections (130,000+ tablets). He has an MA in Museum Studies and undergraduate training in Archaeology. He can identify tablet types and periods but is not a philologist—he relies on visiting scholars for translations. He's responsible for digitization priorities, access permissions, and institutional partnerships.

#### Time Budget
- Administrative: 25-30 hours/week on collection management
- Platform engagement: 2-3 hours/week for evaluation; more if partnership develops
- Partnership meetings: Quarterly reviews with technology partners

#### Primary Goals
1. Accelerate digitization of backlogged collection
2. Increase accessibility while protecting physical artifacts
3. Demonstrate public value to justify institutional funding
4. Ensure proper attribution of British Museum materials

#### Key Needs from the System
- **Collection integration:** Bulk import of museum metadata and images
- **Access controls:** Enforce publication restrictions on certain tablets
- **Institutional branding:** Clear acknowledgment of British Museum as source
- **Progress dashboards:** Show leadership how many BM tablets have been processed
- **Quality assurance:** Ensure outputs meet scholarly standards before public release

#### Pain Points & Frustrations
- Researchers who want immediate access to everything
- Technology projects that promise much but require heavy museum resources
- Attribution disputes between researchers
- Legacy systems that don't integrate with modern platforms
- Pressure to demonstrate ROI on digitization investments

#### Specific Use Cases for Testing
1. **Bulk import:** Can he upload 1,000 tablet images with metadata in a single batch?
2. **Access control:** Can he flag certain tablets as restricted until expert review?
3. **Partnership dashboard:** Can he see aggregate statistics on BM collection processing?
4. **Institutional export:** Can he generate reports for board presentations?
5. **Researcher coordination:** Can he see which scholars are working on BM materials?

#### Success Metrics
- 10,000+ BM tablets processed within first year of partnership
- <5% of outputs require institutional intervention for quality issues
- Positive feedback from visiting scholars on platform integration
- Clear attribution of BM materials in all platform outputs

#### Quotes (Simulated)
> "I have 130,000 tablets and a budget for digitizing maybe 2,000 per year. Show me how this scales."

> "The scholars will always want more access. My job is balancing access with preservation and proper attribution."

> "If this partnership becomes a burden rather than a benefit, we'll pull out. We've been burned before."

---

## Secondary Personas

These users matter but represent smaller or more occasional use cases.

---

### 5. Sophie Laurent — "The Curious Explorer"

**Role:** Casual Visitor / First-Timer
**Age:** 34
**Location:** Lyon, France
**Occupation:** Marketing Manager

#### Background
Sophie saw a TikTok video about cuneiform tablets and clicked through to Glintstone out of curiosity. She has no background in ancient history beyond high school and no intention of becoming a regular contributor. She's exploring to satisfy momentary curiosity—if the experience is delightful, she might stay 10 minutes. If not, she's gone in 30 seconds.

#### Time Budget
- One-time visit: 5-10 minutes maximum
- Return visits: Only if first experience was exceptionally compelling
- Zero commitment tolerance

#### Primary Goals
1. Satisfy curiosity about what cuneiform actually looks like
2. Feel like she "learned something" in a few minutes
3. Maybe tell friends about it if it's cool enough

#### Key Needs from the System
- **Instant engagement:** No registration, no tutorial, immediate experience
- **Visual delight:** Beautiful tablet imagery, satisfying interactions
- **Accessible framing:** Zero jargon, playful tone
- **Shareable moment:** Something screenshot-worthy

#### Specific Use Cases for Testing
1. **Cold landing:** Does she understand what the platform is within 10 seconds?
2. **Sample task:** Can she try a task without any account creation?
3. **Emotional hook:** Does she feel anything when she sees a 4,000-year-old tablet?
4. **Exit path:** If she leaves, does she take away a memorable impression?

#### Success Metrics
- Spends >3 minutes on first visit
- Completes at least one sample task
- Shares or mentions to someone else
- Returns within 30 days

---

### 6. Professor David Yamamoto — "The Educator"

**Role:** University Instructor
**Age:** 48
**Location:** Chicago, IL
**Occupation:** Associate Professor, Ancient History, Northwestern University

#### Background
David teaches undergraduate courses on Ancient Mesopotamia and graduate seminars on cuneiform sources. He's not an Assyriologist by training (his PhD is in Ancient History), but he uses cuneiform sources in translation. He's always looking for ways to make 4,000-year-old material feel relevant to students raised on smartphones.

#### Time Budget
- Course prep: 5-10 hours/week during semester
- In-class activities: 75-minute class sessions
- Student project oversight: Variable

#### Primary Goals
1. Give students hands-on experience with primary sources
2. Demonstrate how digital humanities works in practice
3. Create engaging assignments that don't require cuneiform literacy

#### Key Needs from the System
- **Classroom mode:** Guided activities suitable for groups
- **Assignment templates:** Pre-built exercises with clear learning objectives
- **Student progress tracking:** See what students have contributed
- **Scholarly rigor:** Accurate enough that he's not teaching wrong information

#### Specific Use Cases for Testing
1. **Class activity:** Can 25 students simultaneously work on related tablets?
2. **Assignment design:** Can he create a custom assignment around specific tablets?
3. **Student onboarding:** Can students start contributing within one class period?
4. **Grading support:** Can he see individual student contributions and quality?

#### Success Metrics
- Students complete assigned tasks with >80% success rate
- Positive course evaluations mentioning platform experience
- Reuses platform in subsequent semesters
- Recommends to colleagues

---

### 7. Rachel Nguyen — "The Knowledge Consumer"

**Role:** History Enthusiast / Content Consumer
**Age:** 42
**Location:** Seattle, WA
**Occupation:** Physician (Dermatologist)

#### Background
Rachel listens to history podcasts during her commute and reads popular history books. She's fascinated by ancient civilizations but has no interest in contributing to research—she just wants to learn. She discovered Glintstone's "Grokipedia" articles about specific tablets and finds them more engaging than Wikipedia.

#### Time Budget
- Reading: 20-30 minutes/day during commute
- Deep dives: 1-2 hours/week on weekends
- Zero contribution appetite

#### Primary Goals
1. Learn interesting stories from ancient tablets
2. Understand what tablets reveal about daily life 4,000 years ago
3. Follow along as new tablets are translated

#### Key Needs from the System
- **Readable content:** Engaging prose without academic jargon
- **Rich context:** Historical era, geographic location, human stories
- **Discovery:** "Related tablets" and thematic collections
- **Accessibility:** Content works on mobile, audio-friendly

#### Specific Use Cases for Testing
1. **Content discovery:** Can she find tablets that interest her without knowing P-numbers?
2. **Readability:** Does she understand the contextual article without prior knowledge?
3. **Engagement depth:** Does she click through to related content?
4. **Subscription:** Would she sign up for email updates on new translations?

#### Success Metrics
- >5 minutes average reading time per article
- Returns to read additional articles
- Shares articles with others
- Subscribes to updates

---

### 8. Miguel Santos — "The Technical Contributor"

**Role:** Open Source Developer / Volunteer
**Age:** 31
**Location:** Lisbon, Portugal
**Occupation:** Backend Engineer at a cloud infrastructure company

#### Background
Miguel contributes to open source projects in his spare time. He found Glintstone through GitHub and is interested in the technical architecture, particularly the AI/ML pipeline. He doesn't care about ancient history specifically but finds the technical challenges compelling. He has contributed to other digital humanities projects before.

#### Time Budget
- Open source: 5-8 hours/week
- Onboarding: Willing to invest 10-20 hours to understand codebase
- Sustained contribution: 2-4 hours/week if engaged

#### Primary Goals
1. Contribute to an interesting technical challenge
2. Gain experience with ML pipelines and data processing
3. Have meaningful commits for his portfolio

#### Key Needs from the System
- **Clear architecture documentation:** README, architecture diagrams
- **Local dev environment:** Docker setup, clear dependencies
- **Good first issues:** Tagged issues appropriate for newcomers
- **Code review:** Responsive maintainers who review PRs

#### Specific Use Cases for Testing
1. **Developer onboarding:** Can he get the system running locally within 2 hours?
2. **Contribution pathway:** Are there clearly labeled starter issues?
3. **Documentation:** Is the architecture understandable to someone without domain knowledge?
4. **PR cycle:** How quickly do maintainers respond to pull requests?

#### Success Metrics
- Submits first PR within 2 weeks of initial exploration
- Becomes recurring contributor (3+ PRs)
- Recommends project to developer communities

---

## Persona Usage Guide

### For Simulated User Testing

When simulating these personas for validation:

1. **Stay in character:** Maintain the persona's knowledge level, time constraints, and motivations
2. **Apply realistic friction:** Personas with less time (Marcus, Sophie) should abandon quickly if confused
3. **Track appropriate metrics:** Use the success metrics defined for each persona
4. **Test edge cases:** What happens when Marcus is interrupted mid-task? What happens when Dr. Al-Rashid disagrees with the AI?

### For Product Decisions

When making feature prioritization decisions:

1. **Weight by segment size:** Marcus (hobbyist) represents the largest potential user base; Dr. Al-Rashid (expert) represents the smallest but most critical
2. **Trust is foundational:** If experts like Dr. Al-Rashid don't trust the platform, hobbyists like Marcus will be contributing to nothing
3. **Onboarding varies dramatically:** Sophie needs zero onboarding; Aisha needs substantial tooling; balance accordingly

### For UX Design

When designing interfaces:

1. **Design for extremes:** If Marcus and Dr. Al-Rashid can both use a feature, Aisha probably can too
2. **Progressive disclosure:** Start with Sophie's simplicity, reveal complexity for Aisha and Dr. Al-Rashid
3. **Multiple entry points:** Different personas arrive with different contexts; don't assume linear onboarding

---

## Appendix: Persona-to-Pipeline Stage Mapping

| Persona | Stage 1: Ingestion | Stage 2: Recognition | Stage 3: Transliteration | Stage 4: Translation | Stage 5: Annotation | Stage 6: Context | Stage 7: Output |
|---------|-------------------|---------------------|-------------------------|---------------------|--------------------|--------------------|-----------------|
| Marcus (Hobbyist) | - | Task contributor | - | - | - | Consumer | Consumer |
| Dr. Al-Rashid (Expert) | - | Reviewer | Primary contributor / Reviewer | Primary contributor / Reviewer | Primary contributor | Reviewer | Primary consumer |
| Aisha (Grad Student) | - | Task contributor | Primary contributor | Learning contributor | Learning contributor | Consumer | Consumer |
| Jonathan (Curator) | Primary contributor | - | - | - | - | - | Institutional consumer |
| Sophie (Explorer) | - | Sample task | - | - | - | Consumer | Consumer |
| David (Educator) | - | Class activities | Class activities | - | - | Teaching resource | Teaching resource |
| Rachel (Consumer) | - | - | - | - | - | Primary consumer | Primary consumer |
| Miguel (Developer) | Infrastructure | Infrastructure | Infrastructure | Infrastructure | Infrastructure | Infrastructure | Infrastructure |

---

*Personas created for Glintstone Phase 1 research. Revise as real user data becomes available.*
