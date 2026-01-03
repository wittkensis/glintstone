# Purpose

This defines how all of the agents will collaborate to bring this project to reality.

# Cross-Agent Communication

Agents should feel free to add comments for other agents when relevant and helpful, based on their expertise and assigned tasks.

# Changes

For each commit made to git, log changes to a change log noting which role made changes. Don't be too granular, just give a high level view of the key changes implemented.

# Phases

For this project to be successful, roles need to collaborate in specific ways at specific moments.

When a release for this project kicks off, the following chain of events will occur:

## Phase 1: Discovery

The assyriology-ecosystem-advisor, assyriology-curriculum-advisor, assyriology-academic-advisor, and assyriology-hobbyist agents think hard about their respective focuses, creating relevant reports that will inform all subsequent phases.

In parallel with this, the product-manager agent needs to come up with a structure for the PRDs, their contents, and how to prioritize tasks. They should propose 3 options for approaches here, each anchored in best practices around Agentic product development.

In parallel with this, the ux-visual-designer will research visual aesthetics most likely to resonate with the core audience. They will share 4 proposals of brand identity and visual design which will be applied to the marketing page as well as the main app.

## Phase 2: Strategy & Roadmapping

The ux-architect agent defines a strategy from which the PRDs can be based off of.

Using this UX-driven strategy, the product-manager agent then composes a prioritized set of PRDs, using the decided structure, to build this out according to each release. Keep things focused on the user story level and not worrying about the technology yet.

## Phase 3: Engineering Architecture

The eng-architect agent looks at the UX strategy and PRDs to come up with 3 proposals for how to architect this solution for the POC, and illustrate its potential for scaling into the full-blown 1.0 version eventually.

Part of this will be a focus on the data model. How will cuneiform tablets be codified in the database? How will the educational layer be codified? What about transcriptions, translations, artifact images, and more? What should be hosted vs cross-linked from external servers?

Meanwhile, the ux-designer agent will get to work crafting the screenflows and components.

## Phase 4: Detailed Implementation

This is where it all comes together. The eng-frontend works closely with the ux-designer and brand-visual-designer to build out the solution. 

## Phase 5: Validation

Once it's built out, the assyriology-academic-advisor and assyriology-hobbyist agents provide feedback on their respective workflows.