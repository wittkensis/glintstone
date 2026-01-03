# Capstone Part 3

---

## Ethical & Societal Risk Assessment

Being historically-oriented, I believe this project will present a unique set of societal and ethical considerations. Unique in the broader space of AI-driven products.

However, perhaps these considerations aren’t as unique to considerations already in place within the archaeology space. What’s more interesting to me is that these considerations should apply to humans as much as their AI counterparts within the solution. The saying “what’s good for the goose is good for the gander” may apply in this case.

### Accuracy: Hallucination

This solutions will always have the possibility of completely fabricating answers that bear no resemblance to what the true answer should be. In such cases, identifying such situations may not be obvious to users, and thus requires an intentional solution.

### Inclusivity Risk: Meeting people on their level

If someone goes to the doctor, and the doctor only communicates using the most advanced medical terminology without explaining it, or ensuring that the recipient understands it, then I would argue that doctor is being unethical.

Similar to our case, since we’re including non-experts in our solution, there is an ethical mandate to communicate to them in a way that they will understand. This has implications for the end results too, in that the better they’re communicated to, the better output users can provide.

### Overconfidence & Assumptions of Context

A piece of writing without context becomes can take on more potential interpretations than one with full context. For instance, and SMS message that reads “where r u” could be an angry spouse, or could be a jolly grandparent who just happens to type that way. In this case, the context, as well as the medium of SMS, fundamentally alters the interpretation.

This is no different for ancient writings.

### History Written through Elite Voices

Cuneiform and early writing systems were not the tools of the common people — they were the tools of the highest levels of society and pertained only to their wishes and interests. Thus, our view of history, through the lens of written artifacts, is fundamentally skewed.

The accepted solution to this is to integrate historical writings with the story that non-linguistic artifacts (such as pottery, pollen samples, etc) themselves tell. Our solution should take this same approach to the extent possible.

### Data Protection & Privacy

Historical artifacts have modern owners and protectors. Sometimes these owners are institutions, sometimes wealthy collectors, and sometimes they are loaned for study. I’m not a legal expect, but we should assume that some owners may have different licensing to the information on the artifact and possibly the information contained within the artifact. Given that archaeology is an international collaborative effort across state boundaries, this could get very complicated.

In such cases, legal restraints must be respected to the extent possible.

### Academic Affordability

I personally view the profoundly expensive paywalls around academic journals to be an unethical practice that hinders progress on all fronts, including archeology. While this may always be the case, we have an opportunity to offset this to some extent through AI synthesis, and connecting published research to the relevant artifacts, even if it remains behind a paywall.

---

## Design Strategy

The following pillars give us a framework to make sure all of the above risks and considerations are accounted for. As a friend of mine says, “smart people think in terms of 3’s”, so I’ll try to be smart here and distill solutions to a 3-Pronged Design Strategy:

### 1) Trustworthy Communication

Our design must first of all know its **audience**. Once identified, it must communicate ideas, feedback, and messages in a manner that they will understand.

The contents of this communication can vary in terms of both its precision and accuracy.

For **precision**, areas of low confidence must be identified as such, and allowed to be made more precise (such as character recognition or translation results).

For **accuracy**, the solution must provide opportunities for both humans and potential AI to identify and correct any hallucinations. This can be done in the form of review pipelines, but also leveraging “Deep Research” reasoning models that check their own thinking before sharing responses.

### 2) Holistic Ecosystem Integration

As far as users go, support the entire ecosystem of people who want to contribute to the historical body of work, at all levels of expertise.

For the historical viewpoints themselves, heavily weighted towards the historical elite, include relevant references to academic writings and non-linguistic historical artifacts that round out the perspective that the tablet may be driving. For instance, if a tablet writing says that there was a grain shortage during a season, but other evidence contradicts this as propaganda, then that should be surfaced to round out the perspective.

As far as the academic ecosystem itself, leverage the opportunity to make journals more accessible to a wider audience.

### 3) Legal Ownership & Licensing

This principle is a bit more straightforward and narrow. Any artifacts with licensing or other agreements bound to their usage should have those called out and respected, such as Creative Commons, MIT licensing, or whatever might be relevant to this use-case.