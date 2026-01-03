# Start

I need you to take the contents of the capstone folder and turn it into a live, demoable product. This is initially intended to be a proof of concept that catches peoples' eye and illustrates the momentous power of AI in unlocking humanity's ancient past. The first release will be a standalone, simple demo using dummy data – which will then scale into a full-featured application.

# Target Users

Glintstone initially needs to serve two kinds of users:
- Academics who specialize in Assyriology, linguistic archaeology, and other related fields.
- Hobbyists and volunteers who have a very shallow understanding of cuneiform, but want to contribute in small ways.

## Hobbyist Experience
The solution should build on the Zooniverse.org model, which excels at getting volunteers to help with data tagging and transcription. For instance, participants can help transcribe American Civil War-era handwritten notes for handoff to academics to study.

### Key Metrics to Optimize For:
- **Primary (Trust):** User confidence in contribution value (measured through post-session feedback: "Do you believe your contribution was valuable?")
- **Primary (Productivity):** Number of contributions per hour
- **Secondary:** Task completion rate (% of started sessions that reach completion)
- **Trust Validation:** % of users who return for a second session (retention as trust signal)

## Academic Experience
This end of the solution should integrate with the existing academic ecosystem, such as CDLI and ORACC. It needs to integrate not only from a data perspective, but also from a perspective that respects and adheres to norms in the academic fields associated with this. A key part of this is the social layer – Assyriology is a small field, and we want this project to pour rocket fuel on their processes to speed up their time to insights.

**Trust is the foundation of academic adoption.** Scholars will only use a platform they believe produces reliable, citable work. All metrics must support building and measuring this trust.

### Key Metrics to Optimize For:
- **Primary (Trust):** Expert verification rate (% of AI-assisted content that passes expert review without modification)
- **Primary (Trust):** Academic adoption rate (% of surveyed scholars who would use the platform for their research)
- **Primary (Productivity):** Number of newly transcribed artifacts
- **Secondary:** Time reduction in transcription workflow (compared to traditional methods)
- **Trust Validation:** Citation rate (# of times platform content is cited in published research)
- **Trust Validation:** Institutional endorsements (# of academic departments/museums that formally recommend the platform)

## Cross-Audience Trust Metrics

**Trust is the ultimate success metric for Glintstone.** Without trust from both hobbyists and academics, the platform cannot fulfill its mission. These metrics should be tracked rigorously across all releases and prioritized in product decisions:

### Foundational Trust Metrics
- **Platform Trust:** Net Promoter Score (NPS) from both hobbyists and academics (Target: >50 for both groups)
- **Content Trust:** Ratio of Accepted vs. Proposed content (per status taxonomy in academic workflow report) (Target: >70% acceptance rate)
- **Process Transparency:** % of users who understand how their contributions are used and validated (Target: >85%)

### Attribution & Recognition Trust
- **Attribution Trust:** % of users satisfied with credit/attribution mechanisms (Target: >90%)
- **Contributor Visibility:** % of contributors who can find and share their contributions (Target: >95%)

### Institutional & Community Trust
- **Institutional Trust:** Number of formal partnerships with museums, academic institutions, or platforms (CDLI, Oracc, etc.) (Target: 3+ by Release 2, 10+ by Release 4)
- **Community Trust:** Active participation rate in platform governance/feedback (Target: >15% of active users)
- **Peer Validation:** % of academic users who would recommend platform to colleagues (Target: >60%)

### Quality & Reliability Trust
- **Data Quality:** Error rate in platform-assisted transcriptions compared to expert-only work (Target: Within 5% of expert baseline)
- **System Reliability:** Platform uptime and response time (Target: 99.5% uptime, <200ms response)
- **Correction Velocity:** Average time to address reported errors or quality issues (Target: <48 hours)

# Releases

Each release should serve as an iterative stepping stone to the next phase. Effort should not be exerted to build out future features prematurely, such as backend technology. However, structures should be placed with the long-term goal, and we need to be thinking about it and have a plan for scaling and overall architecture for this as an integrated platform.

## Marketing Page
All releases should be coupled with a single-page marketing site.

## Ecosystem Integration
All releases should be coupled with POCs of an integrated experience between Glintstone and CDLI, showing how they can be easily integrated. For CDLI's integration, rebuild the website as static HTML to demonstrate integration opportunities.

## Release 1 (POC Demo for Feedback)
This will exclusively use a library of dummy data, shown in an interface that could be percieved as real. The outcome should be making the vision believable, enticing, and a source for feedback from stakeholders and customers.

## Release 2 (Pilot / ALPHA)
This will iteratively step towards having a minimalistic, live platform. User profiles will be manually handed out and managed by me.

## Release 3 (GA / BETA)
This will have a more full-featured platform. User profiles will be self-service, but gated.

## Release 4 (1.0)
This will be the first version that's capable of integrating directly with the academic landscape. User profiles will be open and immediately available.

# Logo & Brand

Need guidance on this, but it should command a combination of intrigue, trust, and curiosity. Logo should be inspired by the sumerian "dingir" sign.

# Orchestration

Reference Orchestration.md for how the agents will work together to build each release.
