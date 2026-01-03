import { useState, useEffect } from 'react'
import { Link } from '@tanstack/react-router'
import { Container, Stack, Grid, ExpertCard, InstitutionBadge } from '../components'
import type { Expert, Institution } from '../types'

/**
 * J1: Marketing Page - Homepage
 * 6 sections: Hero, Social Proof, How You Can Help, How It Works, For Scholars, Final CTA + Footer
 */
export function MarketingPage() {
  const [experts, setExperts] = useState<Expert[]>([])
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [contributionCount, setContributionCount] = useState(0)

  // Load data on mount
  useEffect(() => {
    // Fetch experts
    fetch('/data/experts.json')
      .then(res => res.json())
      .then(data => setExperts(data.slice(0, 3))) // Take first 3 for testimonials
      .catch(console.error)

    // Fetch institutions
    fetch('/data/institutions.json')
      .then(res => res.json())
      .then(data => setInstitutions(data.filter((i: Institution) => i.partnered)))
      .catch(console.error)
  }, [])

  // Animate contribution counter
  useEffect(() => {
    const target = 50000
    const duration = 2000
    const steps = 60
    const increment = target / steps
    let current = 0

    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        setContributionCount(target)
        clearInterval(timer)
      } else {
        setContributionCount(Math.floor(current))
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [])

  return (
    <div className="animate-fadeIn">
      {/* Section 1: Hero */}
      <HeroSection contributionCount={contributionCount} />

      {/* Section 2: Social Proof */}
      <SocialProofSection institutions={institutions} />

      {/* Section 3: How You Can Help */}
      <HowYouCanHelpSection />

      {/* Section 4: How It Works */}
      <HowItWorksSection />

      {/* Section 5: For Scholars */}
      <ForScholarsSection experts={experts} institutions={institutions} />

      {/* NEW SECTION: Mysteries Waiting to Be Unlocked */}
      <MysteriesSection />

      {/* Section 6: Final CTA + Footer */}
      <FinalCTASection />
    </div>
  )
}

/**
 * Section 1: Hero - V3 Enhanced
 */
function HeroSection({ contributionCount }: { contributionCount: number }) {
  return (
    <section className="relative min-h-[85vh] flex items-center overflow-hidden">
      {/* Authentic tablet background with gold gradient overlay */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--background))] via-[rgb(var(--surface))] to-[rgb(var(--background))]"
        aria-hidden="true"
      >
        {/* Authentic tablet image */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-15"
          style={{
            backgroundImage: "url('/images/tablets/authentic/P005377.jpg')",
            backgroundBlendMode: 'multiply'
          }}
        />

        {/* Gold gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[rgb(var(--accent-gold)/0.08)] via-transparent to-[rgb(var(--accent-gold-ember)/0.12)]" />

        {/* Starfield effect */}
        <div className="absolute inset-0 starlight-particles" />
      </div>

      <Container size="wide" className="relative z-10 py-16 md:py-24">
        <div className="max-w-4xl mx-auto text-center">
          {/* Floating cuneiform characters */}
          <div className="absolute -top-8 left-1/4 text-4xl md:text-6xl font-cuneiform text-[rgb(var(--accent-gold))] opacity-20 animate-pulse">
            𒀭
          </div>
          <div className="absolute top-12 right-1/4 text-3xl md:text-5xl font-cuneiform text-[rgb(var(--accent-gold-glow))] opacity-15 animate-pulse" style={{ animationDelay: '0.5s' }}>
            𒊏
          </div>
          <div className="absolute bottom-16 left-1/3 text-4xl md:text-6xl font-cuneiform text-[rgb(var(--accent-gold))] opacity-20 animate-pulse" style={{ animationDelay: '1s' }}>
            𒄠
          </div>
          <div className="absolute top-24 right-1/3 text-3xl md:text-5xl font-cuneiform text-[rgb(var(--accent-gold-ember))] opacity-15 animate-pulse" style={{ animationDelay: '1.5s' }}>
            𒂗
          </div>

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

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Link to="/contribute">
              <button className="btn-primary text-lg px-8 py-4 rounded-lg shadow-lg hover:shadow-xl transition-all">
                Start Your First Contribution
              </button>
            </Link>
            <button
              className="btn-tertiary text-lg px-8 py-4 rounded-lg"
              onClick={() => {
                document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Learn More
            </button>
          </div>

          {/* Enhanced contribution counter with ember glow */}
          <div className="inline-flex items-center gap-4 px-8 py-4 card-clay-elevated rounded-full animate-emberGlow">
            <span className="w-3 h-3 bg-[rgb(var(--accent-gold-ember))] rounded-full animate-pulse" aria-hidden="true" />
            <span className="text-[rgb(var(--text))]">
              <strong className="text-4xl font-mono text-transparent bg-clip-text bg-gradient-to-r from-[rgb(var(--accent-gold))] to-[rgb(var(--accent-gold-glow))]">
                {contributionCount.toLocaleString()}+
              </strong>
              <span className="ml-2 text-[rgb(var(--text-secondary))]">contributions and counting</span>
            </span>
          </div>
        </div>
      </Container>
    </section>
  )
}

/**
 * Section 2: Social Proof - V3 Enhanced
 */
function SocialProofSection({ institutions }: { institutions: Institution[] }) {
  const stats = [
    { value: '50,000+', label: 'Contributions', icon: '𒀭' },
    { value: '1,200+', label: 'Tablets Transcribed', icon: '𒊏' },
    { value: '150+', label: 'Expert Reviewers', icon: '𒄠' },
  ]

  // Filter key partners
  const keyPartners = institutions.filter(i =>
    ['inst-yale', 'inst-british-museum', 'inst-cdli'].includes(i.id) ||
    i.name.includes('Yale') ||
    i.name.includes('British Museum') ||
    i.name.includes('CDLI')
  ).slice(0, 4)

  return (
    <section className="py-20 bg-[rgb(var(--surface))] relative overflow-hidden">
      {/* Background rotating tablet images */}
      <div className="absolute inset-0 opacity-5" aria-hidden="true">
        <div
          className="absolute top-10 left-10 w-32 h-32 bg-cover bg-center rounded-lg animate-pulse"
          style={{ backgroundImage: "url('/images/tablets/authentic/P212322.jpg')" }}
        />
        <div
          className="absolute bottom-20 right-20 w-40 h-40 bg-cover bg-center rounded-lg animate-pulse"
          style={{ backgroundImage: "url('/images/tablets/authentic/P001251.jpg')", animationDelay: '1s' }}
        />
      </div>

      <Container className="relative z-10">
        <Stack space="xl">
          {/* Stats grid with gold shimmer */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-12 text-center">
            {stats.map((stat) => (
              <div key={stat.label} className="relative">
                <div className="font-cuneiform text-5xl text-[rgb(var(--accent-gold))] opacity-20 mb-2">
                  {stat.icon}
                </div>
                <span className="block text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[rgb(var(--accent-gold))] via-[rgb(var(--accent-gold-glow))] to-[rgb(var(--accent-gold))] animate-goldShimmer">
                  {stat.value}
                </span>
                <span className="text-lg text-[rgb(var(--text-secondary))] mt-2 block">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>

          {/* Partner logos with "Trusted by" text */}
          <div>
            <p className="text-center text-xl text-[rgb(var(--text))] mb-8 font-medium">
              Trusted by{' '}
              <span className="text-[rgb(var(--accent-gold-glow))]">Yale</span>,{' '}
              <span className="text-[rgb(var(--accent-gold-glow))]">Oxford</span>,{' '}
              <span className="text-[rgb(var(--accent-gold-glow))]">British Museum</span>
            </p>
            <div className="flex flex-wrap justify-center items-center gap-6">
              {keyPartners.length > 0 ? (
                keyPartners.map((institution) => (
                  <div key={institution.id} className="transform hover:scale-105 transition-transform">
                    <InstitutionBadge
                      institution={institution}
                      variant="default"
                    />
                  </div>
                ))
              ) : (
                // Fallback placeholders
                <>
                  <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                    Yale University
                  </div>
                  <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                    Oxford
                  </div>
                  <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                    British Museum
                  </div>
                  <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                    CDLI
                  </div>
                </>
              )}
            </div>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 3: How You Can Help - V3 Enhanced
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
      cuneiform: '𒀭',
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
      cuneiform: '𒊏',
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
      cuneiform: '𒄠',
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
                  card-clay clay-texture relative overflow-hidden p-8
                  transition-all border-2
                  ${path.available
                    ? 'border-[rgb(var(--accent-blue))] hover:border-[rgb(var(--accent-blue-bright))] hover:shadow-lg hover:shadow-[rgb(var(--accent-blue)/.2)]'
                    : 'border-[rgb(var(--border))] opacity-75'
                  }
                `}
              >
                {/* Cuneiform decorative element */}
                <div className="absolute top-4 right-4 font-cuneiform text-6xl text-[rgb(var(--accent-blue))] opacity-10">
                  {path.cuneiform}
                </div>

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
 * Section 4: How It Works - V3 Visual Storytelling
 */
function HowItWorksSection() {
  const steps = [
    {
      number: 1,
      title: 'View Ancient Tablet',
      description: 'We show you a photograph of a cuneiform tablet from a major museum collection.',
      image: '/images/tablets/authentic/P005377.jpg',
      cuneiform: '',
      transliteration: '',
    },
    {
      number: 2,
      title: 'Identify Cuneiform Signs',
      description: 'Match highlighted signs from the tablet with reference examples using visual comparison.',
      image: '/images/tablets/authentic/P010012.jpg',
      cuneiform: '𒀭',
      transliteration: 'DINGIR (god)',
    },
    {
      number: 3,
      title: 'AI Validates Your Work',
      description: 'Our AI compares your input with consensus data and prior expert transcriptions.',
      image: '/images/tablets/authentic/P003512.jpg',
      cuneiform: '𒂗',
      transliteration: 'EN (lord)',
    },
    {
      number: 4,
      title: 'Experts Review & Publish',
      description: 'Scholars verify crowdsourced data and publish verified transcriptions to CDLI.',
      image: '/images/tablets/authentic/P001251.jpg',
      cuneiform: '✓',
      transliteration: 'Verified',
    },
  ]

  return (
    <section id="how-it-works" className="py-20 bg-[rgb(var(--surface))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              How It Works
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              A visual journey from ancient tablet to verified transcription.
              Watch as your contributions become part of the scholarly record.
            </p>
          </div>

          <div className="relative">
            {/* Flowing gold connecting lines */}
            <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[rgb(var(--accent-gold))] to-transparent opacity-30" aria-hidden="true" />

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {steps.map((step, index) => (
                <article
                  key={step.number}
                  className="relative group"
                >
                  {/* Step number badge */}
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20 w-12 h-12 rounded-full bg-gradient-to-br from-[rgb(var(--accent-gold))] to-[rgb(var(--accent-gold-glow))] text-black font-bold text-lg flex items-center justify-center shadow-lg">
                    {step.number}
                  </div>

                  {/* Card with tablet image */}
                  <div className="card-clay-elevated overflow-hidden transition-all group-hover:shadow-xl group-hover:shadow-[rgb(var(--accent-gold)/.2)] group-hover:-translate-y-1">
                    {/* Tablet image fragment */}
                    <div className="relative h-48 bg-cover bg-center" style={{ backgroundImage: `url('${step.image}')` }}>
                      <div className="absolute inset-0 bg-gradient-to-t from-[rgb(var(--surface))] to-transparent" />

                      {/* Cuneiform overlay */}
                      {step.cuneiform && step.cuneiform !== '✓' && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-8xl font-cuneiform text-[rgb(var(--accent-gold-glow))] opacity-80 animate-pulse">
                            {step.cuneiform}
                          </div>
                        </div>
                      )}

                      {/* Verified checkmark */}
                      {step.cuneiform === '✓' && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-8xl text-[rgb(var(--accent-gold))] animate-pulse">
                            ✓
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="p-6">
                      <h3 className="text-xl font-bold text-[rgb(var(--text))] mb-3">
                        {step.title}
                      </h3>
                      <p className="text-[rgb(var(--text-secondary))] mb-4 leading-relaxed">
                        {step.description}
                      </p>

                      {/* Transliteration */}
                      {step.transliteration && (
                        <div className="pt-4 border-t border-[rgb(var(--border))]">
                          <span className="text-sm font-mono text-[rgb(var(--accent-blue-bright))]">
                            {step.transliteration}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Arrow connector for desktop */}
                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-4 z-10 text-[rgb(var(--accent-gold))] opacity-50" aria-hidden="true">
                      <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                      </svg>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 5: For Scholars - V3 Enhanced
 */
function ForScholarsSection({ experts, institutions }: { experts: Expert[]; institutions: Institution[] }) {
  // Filter for research platforms
  const platforms = institutions.filter(i =>
    i.id === 'inst-cdli' || i.id === 'inst-oracc' ||
    i.name.includes('CDLI') || i.name.includes('ORACC')
  )

  return (
    <section className="py-20 bg-[rgb(var(--background))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              For Scholars
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              Glintstone integrates with established scholarly infrastructure
              and is built with input from leading Assyriologists.
            </p>
          </div>

          {/* Featured tablet example - P003512 Old Babylonian literary work */}
          <div className="card-clay-elevated overflow-hidden max-w-5xl mx-auto">
            <div className="grid md:grid-cols-2 gap-0">
              {/* Tablet image side */}
              <div className="relative h-96 md:h-auto">
                <div
                  className="absolute inset-0 bg-cover bg-center"
                  style={{ backgroundImage: "url('/images/tablets/authentic/P003512.jpg')" }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[rgb(var(--surface-elevated))] md:to-[rgb(var(--surface-elevated))]" />
                </div>
              </div>

              {/* Analysis side */}
              <div className="p-8 bg-[rgb(var(--surface-elevated))]">
                <h3 className="text-2xl font-bold text-[rgb(var(--text))] mb-6">
                  Old Babylonian Literary Work
                </h3>

                {/* Cuneiform → Transliteration → Translation */}
                <div className="space-y-6">
                  <div>
                    <span className="text-sm text-[rgb(var(--text-muted))] uppercase tracking-wide mb-2 block">
                      Cuneiform Script
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

                  {/* AI Confidence Scoring */}
                  <div className="pt-6 border-t border-[rgb(var(--border))]">
                    <span className="text-sm text-[rgb(var(--text-muted))] uppercase tracking-wide mb-3 block">
                      AI Confidence Scoring
                    </span>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-[rgb(var(--text-secondary))]">𒀭 DINGIR</span>
                          <span className="text-sm text-[rgb(var(--accent-blue-bright))]">96%</span>
                        </div>
                        <div className="progress-lapis">
                          <div className="progress-lapis-fill" style={{ width: '96%' }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-[rgb(var(--text-secondary))]">𒂗 EN</span>
                          <span className="text-sm text-[rgb(var(--accent-blue-bright))]">89%</span>
                        </div>
                        <div className="progress-lapis">
                          <div className="progress-lapis-fill" style={{ width: '89%' }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-[rgb(var(--text-secondary))]">𒊏 RA</span>
                          <span className="text-sm text-[rgb(var(--accent-blue-bright))]">92%</span>
                        </div>
                        <div className="progress-lapis">
                          <div className="progress-lapis-fill" style={{ width: '92%' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CDLI Partnership Badge */}
          <div className="flex justify-center">
            <div className="inline-flex items-center gap-3 px-6 py-3 card-lapis rounded-full">
              <svg className="w-6 h-6 text-[rgb(var(--accent-blue-bright))]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              <span className="text-[rgb(var(--text))] font-medium">
                Published in collaboration with CDLI
              </span>
            </div>
          </div>

          {/* Integration badges */}
          <div className="flex flex-wrap justify-center gap-6">
            {platforms.length > 0 ? (
              platforms.map((platform) => (
                <div key={platform.id} className="transform hover:scale-105 transition-transform">
                  <InstitutionBadge
                    institution={platform}
                    variant="default"
                  />
                </div>
              ))
            ) : (
              <>
                <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                  CDLI Integration
                </div>
                <div className="px-6 py-3 card-lapis rounded-lg text-[rgb(var(--text))] font-medium">
                  ORACC Compatible
                </div>
              </>
            )}
          </div>

          {/* Expert testimonials */}
          <div>
            <h3 className="text-center text-2xl font-semibold text-[rgb(var(--text))] mb-8">
              What Experts Say
            </h3>
            <Grid columns={3} gap="md">
              {experts.length > 0 ? (
                experts.map((expert) => (
                  <div key={expert.id} className="flex flex-col gap-4">
                    <blockquote className="card-clay p-6 italic text-[rgb(var(--text-secondary))] leading-relaxed">
                      "Glintstone's approach to crowdsourced transcription could revolutionize
                      how we process the vast corpus of untranscribed tablets."
                    </blockquote>
                    <ExpertCard expert={expert} variant="compact" />
                  </div>
                ))
              ) : (
                // Fallback testimonials
                [1, 2, 3].map((i) => (
                  <div key={i} className="card-clay p-6">
                    <p className="italic text-[rgb(var(--text-secondary))] mb-4 leading-relaxed">
                      "Glintstone's approach to crowdsourced transcription could revolutionize
                      how we process the vast corpus of untranscribed tablets."
                    </p>
                    <p className="text-sm text-[rgb(var(--text-muted))]">
                      - Expert Reviewer
                    </p>
                  </div>
                ))
              )}
            </Grid>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * NEW SECTION: Mysteries Waiting to Be Unlocked
 */
function MysteriesSection() {
  const mysteries = [
    {
      id: 'P005377',
      image: '/images/tablets/authentic/P005377.jpg',
      caption: 'Administrative records from Ur III',
      description: 'Tracking ancient commerce',
      remaining: '2,847',
    },
    {
      id: 'P010012',
      image: '/images/tablets/authentic/P010012.jpg',
      caption: 'Royal inscriptions of the Neo-Assyrian Empire',
      description: 'Kings and conquests carved in clay',
      remaining: '1,523',
    },
    {
      id: 'P001251',
      image: '/images/tablets/authentic/P001251.jpg',
      caption: 'Old Babylonian legal documents',
      description: '4,000-year-old contracts',
      remaining: '3,214',
    },
    {
      id: 'P212322',
      image: '/images/tablets/authentic/P212322.jpg',
      caption: 'Literary masterpieces',
      description: 'Waiting to reveal their secrets',
      remaining: '987',
    },
  ]

  return (
    <section className="py-20 bg-[rgb(var(--surface))] relative overflow-hidden">
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[rgb(var(--accent-gold)/0.05)] to-transparent" aria-hidden="true" />

      <Container className="relative z-10">
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-5xl font-bold text-[rgb(var(--text))] mb-6">
              Mysteries Waiting to Be{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[rgb(var(--accent-gold))] to-[rgb(var(--accent-gold-glow))]">
                Unlocked
              </span>
            </h2>
            <p className="text-xl text-[rgb(var(--text-secondary))] max-w-3xl mx-auto leading-relaxed">
              Thousands of tablets still hold untold stories.
              Your contribution could be the key to unlocking ancient wisdom.
            </p>
          </div>

          {/* Tablet grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {mysteries.map((mystery) => (
              <article
                key={mystery.id}
                className="group relative overflow-hidden rounded-xl border-2 border-[rgb(var(--border))] hover:border-[rgb(var(--accent-gold))] transition-all cursor-pointer"
              >
                {/* Tablet image */}
                <div className="relative h-72 bg-cover bg-center" style={{ backgroundImage: `url('${mystery.image}')` }}>
                  {/* Overlay gradient */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent opacity-80 group-hover:opacity-70 transition-opacity" />

                  {/* Hover reveal - signs remaining */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <div className="text-center">
                      <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-[rgb(var(--accent-gold-glow))] to-[rgb(var(--accent-gold))] animate-goldShimmer mb-2">
                        {mystery.remaining}
                      </div>
                      <div className="text-sm text-[rgb(var(--accent-gold-glow))] font-medium uppercase tracking-wide">
                        signs remaining to transcribe
                      </div>
                    </div>
                  </div>

                  {/* Caption overlay */}
                  <div className="absolute bottom-0 left-0 right-0 p-6 z-10">
                    <h3 className="text-lg font-bold text-white mb-1">
                      {mystery.caption}
                    </h3>
                    <p className="text-sm text-[rgb(var(--accent-gold-glow))]">
                      {mystery.description}
                    </p>
                  </div>

                  {/* Cuneiform decoration */}
                  <div className="absolute top-4 right-4 font-cuneiform text-4xl text-[rgb(var(--accent-gold))] opacity-30 group-hover:opacity-60 transition-opacity">
                    𒀭
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Call to action */}
          <div className="text-center pt-8">
            <p className="text-2xl text-[rgb(var(--text))] mb-6 font-medium">
              These ancient voices are waiting.{' '}
              <span className="text-[rgb(var(--accent-gold-glow))]">Will you answer the call?</span>
            </p>
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 6: Final CTA + Footer - V3 Enhanced
 */
function FinalCTASection() {
  return (
    <>
      {/* Final CTA with starfield */}
      <section className="relative py-28 overflow-hidden">
        {/* Starfield background */}
        <div className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--background))] via-[rgb(var(--surface))] to-[rgb(var(--background))]">
          <div className="starlight-particles absolute inset-0" />

          {/* Tablet constellation pattern overlay */}
          <div className="absolute inset-0 opacity-5" aria-hidden="true">
            <div
              className="absolute top-1/4 left-1/4 w-24 h-24 bg-cover bg-center rounded-lg rotate-12"
              style={{ backgroundImage: "url('/images/tablets/authentic/P005377.jpg')" }}
            />
            <div
              className="absolute top-1/3 right-1/4 w-20 h-20 bg-cover bg-center rounded-lg -rotate-6"
              style={{ backgroundImage: "url('/images/tablets/authentic/P010012.jpg')" }}
            />
            <div
              className="absolute bottom-1/3 left-1/3 w-28 h-28 bg-cover bg-center rounded-lg rotate-3"
              style={{ backgroundImage: "url('/images/tablets/authentic/P003512.jpg')" }}
            />
            <div
              className="absolute bottom-1/4 right-1/3 w-22 h-22 bg-cover bg-center rounded-lg -rotate-12"
              style={{ backgroundImage: "url('/images/tablets/authentic/P001251.jpg')" }}
            />
          </div>

          {/* Floating cuneiform characters */}
          <div className="absolute top-1/4 left-1/4 font-cuneiform text-7xl text-[rgb(var(--accent-gold))] opacity-10 animate-pulse">
            𒀭
          </div>
          <div className="absolute top-1/3 right-1/3 font-cuneiform text-6xl text-[rgb(var(--accent-gold-glow))] opacity-8 animate-pulse" style={{ animationDelay: '1s' }}>
            𒊏
          </div>
          <div className="absolute bottom-1/3 right-1/4 font-cuneiform text-8xl text-[rgb(var(--accent-gold))] opacity-10 animate-pulse" style={{ animationDelay: '2s' }}>
            𒈠
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
              Join thousands of citizen scholars helping to unlock 3,000 years of human history,
              one cuneiform sign at a time.
            </p>

            {/* Dual CTA */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Link to="/contribute">
                <button className="btn-primary text-xl px-10 py-5 rounded-lg shadow-2xl hover:shadow-[rgb(var(--accent-gold)/.4)] transition-all">
                  Begin Contributing
                </button>
              </Link>
              <button
                className="btn-tertiary text-xl px-10 py-5 rounded-lg"
                onClick={() => {
                  document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Learn More About Cuneiform
              </button>
            </div>

            {/* Attribution */}
            <p className="text-sm text-[rgb(var(--text-muted))] italic">
              Images courtesy of CDLI and respective museums
            </p>
          </div>
        </Container>
      </section>

      {/* Footer */}
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
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--accent-gold-glow))] transition-colors font-medium">
                About
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--accent-gold-glow))] transition-colors font-medium">
                Contact
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--accent-gold-glow))] transition-colors font-medium">
                Privacy
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--accent-gold-glow))] transition-colors font-medium">
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
