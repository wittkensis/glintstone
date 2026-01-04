import { useState, useEffect } from 'react'
import { Link } from '@tanstack/react-router'
import { Container, Stack, Grid } from '../components'
import type { Institution } from '../types'

/**
 * J1: Marketing Page - Homepage
 * Cleaned up version: removed fake stats, floating unicode, excessive hover effects
 */
export function MarketingPage() {
  const [institutions, setInstitutions] = useState<Institution[]>([])

  // Load institutions on mount
  useEffect(() => {
    fetch('/data/institutions.json')
      .then(res => res.json())
      .then(data => setInstitutions(data.filter((i: Institution) => i.partnered)))
      .catch(console.error)
  }, [])

  return (
    <div className="animate-fadeIn">
      {/* Section 1: Hero */}
      <HeroSection />

      {/* Section 2: The Challenge */}
      <ChallengeSection />

      {/* Section 3: How You Can Help */}
      <HowYouCanHelpSection />

      {/* Section 4: How It Works */}
      <HowItWorksSection />

      {/* Section 5: For Scholars */}
      <ForScholarsSection institutions={institutions} />

      {/* Section 6: Final CTA + Footer */}
      <FinalCTASection />
    </div>
  )
}

/**
 * Section 1: Hero - Cleaned up
 */
function HeroSection() {
  return (
    <section className="relative min-h-[85vh] flex items-center overflow-hidden">
      {/* Background with authentic tablet */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--background))] via-[rgb(var(--surface))] to-[rgb(var(--background))]"
        aria-hidden="true"
      >
        <div
          className="absolute inset-0 bg-cover bg-center opacity-15"
          style={{
            backgroundImage: "url('/images/tablets/authentic/P005377.jpg')",
            backgroundBlendMode: 'multiply'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-[rgb(var(--accent-gold)/0.08)] via-transparent to-[rgb(var(--accent-gold-ember)/0.12)]" />
      </div>

      <Container size="wide" className="relative z-10 py-16 md:py-24">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-[rgb(var(--text))] mb-6 leading-tight">
            Decipher{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[rgb(var(--accent-gold))] via-[rgb(var(--accent-gold-glow))] to-[rgb(var(--accent-gold))]">
              3,000 Years
            </span>
            {' '}of Human History
          </h1>

          <p className="text-xl sm:text-2xl text-[rgb(var(--text-secondary))] mb-10 max-w-3xl mx-auto leading-relaxed">
            Every cuneiform sign tells a story. Help unlock the mysteries of ancient Mesopotamia with AI-powered transcription.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/contribute">
              <button className="btn-primary text-lg px-8 py-4 rounded-lg">
                Start Your First Contribution
              </button>
            </Link>
            <button
              className="btn-tertiary text-lg px-8 py-4 rounded-lg"
              onClick={() => {
                document.getElementById('the-challenge')?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Learn More
            </button>
          </div>
        </div>
      </Container>
    </section>
  )
}

/**
 * Section 2: The Challenge - Replacing fake stats with honest framing
 */
function ChallengeSection() {
  return (
    <section id="the-challenge" className="py-20 bg-[rgb(var(--surface))]">
      <Container>
        <Stack space="xl">
          <div className="text-center max-w-4xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              The Work That Remains
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] leading-relaxed mb-8">
              Museums and universities hold over <strong className="text-[rgb(var(--accent-gold))]">500,000 cuneiform tablets</strong> -
              the largest collection of written records from the ancient world.
              Yet the vast majority remain untranslated, their stories still waiting to be told.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="card-clay p-8 text-center">
              <div className="text-4xl font-bold text-[rgb(var(--accent-gold))] mb-3">500,000+</div>
              <div className="text-lg text-[rgb(var(--text))] mb-2">Tablets in Collections</div>
              <p className="text-sm text-[rgb(var(--text-muted))]">
                Held in museums worldwide, from the British Museum to Yale
              </p>
            </div>
            <div className="card-clay p-8 text-center">
              <div className="text-4xl font-bold text-[rgb(var(--accent-gold))] mb-3">~200</div>
              <div className="text-lg text-[rgb(var(--text))] mb-2">Active Assyriologists</div>
              <p className="text-sm text-[rgb(var(--text-muted))]">
                Specialists who can read cuneiform at an expert level
              </p>
            </div>
            <div className="card-clay p-8 text-center">
              <div className="text-4xl font-bold text-[rgb(var(--accent-gold))] mb-3">Centuries</div>
              <div className="text-lg text-[rgb(var(--text))] mb-2">At Current Pace</div>
              <p className="text-sm text-[rgb(var(--text-muted))]">
                The estimated time to process the backlog using traditional methods
              </p>
            </div>
          </div>

          <div className="text-center">
            <p className="text-lg text-[rgb(var(--text-secondary))] italic max-w-2xl mx-auto">
              What if we could accelerate this work? What if anyone could contribute to unlocking the ancient past?
            </p>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 3: How You Can Help
 */
function HowYouCanHelpSection() {
  const paths = [
    {
      id: 'passerby',
      title: 'Passerby',
      description: 'Quick 3-minute contributions. Match cuneiform signs using visual comparison - no training required.',
      timeCommitment: '3 minutes',
      cta: 'Start Contributing',
      href: '/contribute',
      available: true,
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 8v4l3 3"/>
        </svg>
      ),
    },
    {
      id: 'learner',
      title: 'Early Learner',
      description: 'Learn cuneiform basics while contributing. Structured lessons combined with real transcription work.',
      timeCommitment: '15-30 minutes',
      cta: 'Coming Soon',
      href: '#',
      available: false,
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
      ),
    },
    {
      id: 'expert',
      title: 'Expert',
      description: 'Advanced transcription and verification for specialists in Assyriology and related fields.',
      timeCommitment: 'Flexible',
      cta: 'Coming Soon',
      href: '#',
      available: false,
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
      ),
    },
  ]

  return (
    <section className="py-20 bg-[rgb(var(--background))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              How You Can Help
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              Choose your path to contribute to decoding ancient Mesopotamian texts.
              Every contribution advances our understanding of human history.
            </p>
          </div>

          <Grid columns={3} gap="lg">
            {paths.map((path) => (
              <article
                key={path.id}
                className={`
                  card-clay clay-texture relative overflow-hidden p-8 border-2
                  ${path.available
                    ? 'border-[rgb(var(--accent-blue))]'
                    : 'border-[rgb(var(--border))] opacity-75'
                  }
                `}
              >
                <div className="relative z-10">
                  <div className="text-[rgb(var(--accent-blue-bright))] mb-6">
                    {path.icon}
                  </div>
                  <h3 className="text-2xl font-bold text-[rgb(var(--text))] mb-3">
                    {path.title}
                  </h3>
                  <p className="text-[rgb(var(--text-secondary))] mb-6 leading-relaxed">
                    {path.description}
                  </p>
                  <div className="flex items-center justify-between pt-4 border-t border-[rgb(var(--border))]">
                    <span className="text-sm text-[rgb(var(--text-muted))] font-medium">
                      {path.timeCommitment}
                    </span>
                    {path.available ? (
                      <Link to={path.href}>
                        <button className="btn-primary px-5 py-2.5 text-sm">
                          {path.cta}
                        </button>
                      </Link>
                    ) : (
                      <button className="btn-secondary px-5 py-2.5 text-sm opacity-50 cursor-not-allowed" disabled>
                        {path.cta}
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </Grid>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 4: How It Works - Redesigned as Pipeline
 */
function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20 bg-[rgb(var(--surface))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              The Transcription Pipeline
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              From museum collection to verified transcription - a collaborative process
              combining crowdsourced effort, AI assistance, and expert validation.
            </p>
          </div>

          {/* Pipeline visualization */}
          <div className="max-w-5xl mx-auto">
            {/* Pipeline stages */}
            <div className="relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-16 left-0 right-0 h-0.5 bg-gradient-to-r from-[rgb(var(--accent-blue))] via-[rgb(var(--accent-gold))] to-[rgb(var(--accent-blue-bright))]" aria-hidden="true" />

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
                {/* Stage 1: Source */}
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[rgb(var(--accent-blue))] text-white flex items-center justify-center text-xl font-bold">
                    1
                  </div>
                  <h3 className="text-lg font-bold text-[rgb(var(--text))] mb-2">Source</h3>
                  <p className="text-sm text-[rgb(var(--text-secondary))]">
                    Tablet photographs from CDLI, museums, and university collections
                  </p>
                </div>

                {/* Stage 2: Crowd */}
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[rgb(var(--accent-gold))] text-black flex items-center justify-center text-xl font-bold">
                    2
                  </div>
                  <h3 className="text-lg font-bold text-[rgb(var(--text))] mb-2">Crowd</h3>
                  <p className="text-sm text-[rgb(var(--text-secondary))]">
                    Contributors identify individual signs through visual matching
                  </p>
                </div>

                {/* Stage 3: AI */}
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[rgb(var(--accent-gold-glow))] text-black flex items-center justify-center text-xl font-bold">
                    3
                  </div>
                  <h3 className="text-lg font-bold text-[rgb(var(--text))] mb-2">AI Assist</h3>
                  <p className="text-sm text-[rgb(var(--text-secondary))]">
                    Machine learning validates consensus and suggests corrections
                  </p>
                </div>

                {/* Stage 4: Expert */}
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[rgb(var(--accent-blue-bright))] text-black flex items-center justify-center text-xl font-bold">
                    4
                  </div>
                  <h3 className="text-lg font-bold text-[rgb(var(--text))] mb-2">Expert Review</h3>
                  <p className="text-sm text-[rgb(var(--text-secondary))]">
                    Assyriologists verify and publish to scholarly databases
                  </p>
                </div>
              </div>
            </div>

            {/* Detailed breakdown */}
            <div className="mt-16 card-clay-elevated p-8">
              <h3 className="text-xl font-bold text-[rgb(var(--text))] mb-6 text-center">
                What Happens at Each Stage
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="font-semibold text-[rgb(var(--accent-blue-bright))] mb-2">Crowdsourced Input</h4>
                  <ul className="space-y-2 text-sm text-[rgb(var(--text-secondary))]">
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      Multiple contributors review each sign independently
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      Visual comparison with sign reference library
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      Consensus builds through agreement between contributors
                    </li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-[rgb(var(--accent-blue-bright))] mb-2">Quality Assurance</h4>
                  <ul className="space-y-2 text-sm text-[rgb(var(--text-secondary))]">
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      AI flags signs with low consensus for expert review
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      Scholarly validation before publication
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[rgb(var(--accent-gold))]">•</span>
                      Integration with CDLI and other research platforms
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 5: For Scholars
 */
function ForScholarsSection({ institutions }: { institutions: Institution[] }) {
  return (
    <section className="py-20 bg-[rgb(var(--background))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              For Scholars
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              Glintstone is designed to integrate with established scholarly infrastructure
              and is being developed with input from the Assyriology community.
            </p>
          </div>

          {/* Featured tablet example */}
          <div className="card-clay-elevated overflow-hidden max-w-5xl mx-auto">
            <div className="grid md:grid-cols-2 gap-0">
              <div className="relative h-96 md:h-auto">
                <div
                  className="absolute inset-0 bg-cover bg-center"
                  style={{ backgroundImage: "url('/images/tablets/authentic/P003512.jpg')" }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[rgb(var(--surface-elevated))]" />
                </div>
              </div>

              <div className="p-8 bg-[rgb(var(--surface-elevated))]">
                <h3 className="text-2xl font-bold text-[rgb(var(--text))] mb-6">
                  Sample Transcription Flow
                </h3>

                <div className="space-y-6">
                  <div>
                    <span className="text-sm text-[rgb(var(--text-muted))] uppercase tracking-wide mb-2 block">
                      Original Script
                    </span>
                    <p className="text-3xl font-cuneiform text-[rgb(var(--accent-gold))]">
                      𒀭 𒂗 𒊏 𒄠
                    </p>
                  </div>

                  <div>
                    <span className="text-sm text-[rgb(var(--text-muted))] uppercase tracking-wide mb-2 block">
                      Transliteration
                    </span>
                    <p className="text-lg font-mono text-[rgb(var(--text-secondary))]">
                      DINGIR EN-ra-ma
                    </p>
                  </div>

                  <div>
                    <span className="text-sm text-[rgb(var(--text-muted))] uppercase tracking-wide mb-2 block">
                      Translation
                    </span>
                    <p className="text-lg text-[rgb(var(--text))] italic">
                      "The god, the lord..."
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Partner text (no logos) */}
          <div className="text-center">
            <p className="text-lg text-[rgb(var(--text-secondary))]">
              Designed for integration with{' '}
              <span className="text-[rgb(var(--accent-gold))] font-medium">CDLI</span>,{' '}
              <span className="text-[rgb(var(--accent-gold))] font-medium">ORACC</span>, and major university collections
            </p>
          </div>

          {/* Testimonial placeholder - anonymized */}
          <div className="max-w-2xl mx-auto">
            <blockquote className="card-clay p-8 text-center">
              <p className="text-lg italic text-[rgb(var(--text-secondary))] mb-4 leading-relaxed">
                "The potential for crowdsourced transcription assistance could help address
                the enormous backlog of unpublished cuneiform tablets in museum collections."
              </p>
              <p className="text-sm text-[rgb(var(--text-muted))]">
                — Feedback from academic consultation
              </p>
            </blockquote>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 6: Final CTA + Footer
 */
function FinalCTASection() {
  return (
    <>
      <section className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--background))] via-[rgb(var(--surface))] to-[rgb(var(--background))]">
          {/* Subtle tablet overlay */}
          <div className="absolute inset-0 opacity-5" aria-hidden="true">
            <div
              className="absolute top-1/4 left-1/4 w-24 h-24 bg-cover bg-center rounded-lg rotate-12"
              style={{ backgroundImage: "url('/images/tablets/authentic/P005377.jpg')" }}
            />
            <div
              className="absolute bottom-1/3 left-1/3 w-28 h-28 bg-cover bg-center rounded-lg rotate-3"
              style={{ backgroundImage: "url('/images/tablets/authentic/P003512.jpg')" }}
            />
          </div>
        </div>

        <Container size="narrow" className="relative z-10">
          <div className="text-center">
            <h2 className="text-4xl md:text-6xl font-bold text-[rgb(var(--text))] mb-6 leading-tight">
              Your contribution matters.
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[rgb(var(--accent-gold))] via-[rgb(var(--accent-gold-glow))] to-[rgb(var(--accent-gold))]">
                Ancient voices await.
              </span>
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] mb-12 max-w-2xl mx-auto leading-relaxed">
              Help unlock 3,000 years of human history, one cuneiform sign at a time.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Link to="/contribute">
                <button className="btn-primary text-xl px-10 py-5 rounded-lg">
                  Begin Contributing
                </button>
              </Link>
              <button
                className="btn-tertiary text-xl px-10 py-5 rounded-lg"
                onClick={() => {
                  document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Learn More
              </button>
            </div>

            <p className="text-sm text-[rgb(var(--text-muted))] italic">
              Images courtesy of CDLI and respective museums
            </p>
          </div>
        </Container>
      </section>

      <footer className="py-12 border-t border-[rgb(var(--border))] bg-[rgb(var(--background))]">
        <Container>
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3 text-[rgb(var(--text))]">
              <svg
                className="w-8 h-8 text-[rgb(var(--accent-gold))]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <path d="M9 3v18"/>
                <path d="M3 9h6"/>
              </svg>
              <span className="text-xl font-bold">Glintstone</span>
            </div>

            <nav className="flex flex-wrap justify-center gap-8 text-sm">
              <a href="#" className="text-[rgb(var(--text-secondary))] font-medium">
                About
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] font-medium">
                Contact
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] font-medium">
                Privacy
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] font-medium">
                Terms
              </a>
            </nav>

            <p className="text-sm text-[rgb(var(--text-muted))]">
              &copy; {new Date().getFullYear()} Glintstone Project
            </p>
          </div>
        </Container>
      </footer>
    </>
  )
}
