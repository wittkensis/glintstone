# Capstone Part 2

# Accelerating Cuneiform Tablet Transcription & Translation

## 1. Need & Problem Statement

According to CDLI, we have an estimated 500,000 to 2,000,000 cuneiform tablets have been excavated from archeological sites, covering Akkadian, Sumerian, and other extinct ancient languages in ancient mesopotamia.

Of these, over 175,000 have been cataloged digitally. Assuming the 2mm denominator, only an estimaged 5-6% have been translated (cite: CDLI). Similarly, only 2-4% have been fully translated once transcribed. (cite: Revue d’Assyriologie and The Babylonian World)

These numbers are shocking.

Cuneiform tablets are keys to a vital era in our ancient human past. And there appears to be a bottleneck of only a narrow group of people who are able to understand and make sense of these artifacts.

Previously, I’d explored two key directions to help this bottleneck:

1. Knowledge Integration & Analysis, which would help with the bottom of this knowledge funnel, by integrating existing knowledge more closely with new knowledge. It would also help identify knowledge gaps to know what to look for among the 94-95% of untranslated tablets.
2. AI-Assisted Transcription & Translation, which would facilitate digitizing the knowledge from these tablet images. This would support the entire knowledge pipeline.

After reflection (but sadly a lack of further research input, despite attempts), I’m going to focus my capstone on **AI-Assisted Transcription & Translation**. I’ve chosen this direction because I have first hand experience with AI-assisted transcription as it relates to American Civil War era hand-written letters.

The framework provided by this solution, if executed, could then extend to a multitude of across other archeological zones, such as Latin America and South Asia.

## 2. Design Considerations

Some design needs I’ve identified, and ultimately drove the wireframes you’re about to see:

1. **Levels of Expertise** – This is a solution that will leverage not only AI, but also Hobbyists/Learners to safely support the field with human-in-the-loop transcription and translation. This means that there’s a more abstracted layer of in-app education needed to help amateurs make contributions with AI to be handed off to experts.
2. **Social Layer** – People form the fabric of this knowledge generation, but much more for the Expert users than the other ones.
3. Backtraceable – Each step in the decoding of a tablet must be able to be captured. If a tablet was collected, we must know where, when, by whom, and what the likely context of this tablet was. If it’s been transcribed, we must know by when, by whom, and how reliable the transcription might be. Same for translation. If there are competing answers for any of these, those should be shown transparently.
4. **No Blank Canvases** – Users should never start with a blank canvas; the app should make a guess at the content, whether it’s a transcription or translation.

## 3. Balancing User Control & Automation

We’ll need to leverage AI here primarily as an accelerator and as a guide. Meaning that AI will make the first stab at transcription and translation, but humans will need to refine and guide the output for accuracy and navigate any ambiguities.

For instance, if there’s uncertainty around a specific cuneiform symbol or clause, a user can be asked to provide the final judgement on how to codify it, and with how much certainty.

A tagging system may be another key piece of the design here, and AI can accelerate the tagging of certain tablets with helpful information, for better model training as well as manual browsing and inventory of artifacts. These tags would be balanced in that both humans and AI would curate them.

A good model experience for this is Zooniverse, which provides a crowdsource volunteer-based experience for transcribing written words. Their solution focuses on very granular, specific use-cases that require little or no prior knowledge, but strangely does not currently leverage AI as it could.

## 4. User Trust & Over-Reliance

Preventing people from developing algorithm aversion as well as over-reliance will be essential for this, on a foundational level.

1. Expert Sign-Off – This is a non-negotiable consideration for our solution. Specialists with the deepest knowledge of the languages and time periods must have final say in any transcriptions or translations.
2. Explainable – Sometimes there is ambiguity in markings or meanings. In such cases, provide clear explanations to any AI-recommendations, and allow people to override or vote on answers.
3. Trainable – Similar to CAPTCHA and other methods, human input should serve to help steer the AI in the right direction.
4. Levels of Confidence – When there is uncertainty, this should be codified in the recommendation as well as the final output, so that low-confidence areas can be ironed out in the future and backtraced.
5. Accepted vs Rejected Translation Score – Being able to see the value that this is producing for an individual, but as well as all users combined, will be important for establishing trust.
6. Status Pipelines – Being able to see the pipeline status at a glance of a translation will be a structural reminder that AI is only assisting in certain ways and at certain steps, with humans kept in the loop at each step in the pipeline.

## 5. Wireframes

![Capstone Part 2.jpeg](Capstone%20Part%202/Capstone_Part_2.jpeg)

In the wireframe sketch ideation above (and attached, for higher resolution), I present a possible architecture for a deep focus on AI-Assisted Translation and Transcription, with 3 sub-flows corresponding to varying levels of user expertise:

1. **Passerby Experience** – These users are essentially corporate workers who have volunteer time they need to spend, like many of my colleagues at Salesforce. We often spend time using tools like Zooniverse, so this is largely mirroring that experience, but with AI assisting the decision selection for vague/unmatched cuneiform symbols.
2. **Early Learner Experience** – People like myself who are eager to learn more and contribute to the body of work, but don’t know where to start. Through a variety of features noted in the sketch, this would have AI help guide them through some of the more mechanical aspects of transcription and translation, and provide just enough context to help them make first-pass decisions along the way. Once these decisions are made, they would be handed off to an Expert for final review.
3. **Expert/Specialist** – Professional academics at research institutions looking for ways to boost their quality work output. This would largely mirror the Early Learner Experience, but with three key distinctions:
    1. **Cross-Tablet View** – While the Early Learner Experience would be pigeon-holed through a repeating series of tablets, experts will need to look across tablets as they review larger bodies of work. AI will be a driver here in helping triage and navigate this work pipeline.
    2. **Detailed Context Summaries** – A more nuanced, citation-centric, and detailed summaries provided by the LLM for each tablet.
    3. **Social Layer** – An AI-facilitated social layer that suggests researchers to connect with for input, verification, and sharing of work.

## 6. Summary

In brief summary, this is a large undertaking that requires creating pathways for more people to become contributors, providing superpowers to the existing experts, and seamlessly bringing those groups together.

AI has the potential to be a big driver for progress here, not just in accelerating workflows, but in expanding the social collaboration layer as well.