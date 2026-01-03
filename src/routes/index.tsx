import { useState, useEffect } from 'react'
import { Link } from '@tanstack/react-router'
import { Container, Stack, Grid, Button, ExpertCard, InstitutionBadge } from '../components'
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

      {/* Section 6: Final CTA + Footer */}
      <FinalCTASection />
    </div>
  )
}

/**
 * Section 1: Hero
 */
function HeroSection({ contributionCount }: { contributionCount: number }) {
  return (
    <section className="relative min-h-[80vh] flex items-center overflow-hidden">
      {/* Background with tablet image effect */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--background))] via-[rgb(var(--surface))] to-[rgb(var(--background))]"
        aria-hidden="true"
      >
        {/* Decorative tablet pattern */}
        <div className="absolute inset-0 opacity-10 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%22100%22%20height%3D%22100%22%20viewBox%3D%220%200%20100%20100%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20x%3D%2210%22%20y%3D%2210%22%20width%3D%2280%22%20height%3D%2280%22%20fill%3D%22none%22%20stroke%3D%22%23f6ad55%22%20stroke-width%3D%221%22%20rx%3D%224%22%2F%3E%3Cline%20x1%3D%2220%22%20y1%3D%2230%22%20x2%3D%2280%22%20y2%3D%2230%22%20stroke%3D%22%23f6ad55%22%20stroke-width%3D%220.5%22%2F%3E%3Cline%20x1%3D%2220%22%20y1%3D%2250%22%20x2%3D%2270%22%20y2%3D%2250%22%20stroke%3D%22%23f6ad55%22%20stroke-width%3D%220.5%22%2F%3E%3Cline%20x1%3D%2220%22%20y1%3D%2270%22%20x2%3D%2260%22%20y2%3D%2270%22%20stroke%3D%22%23f6ad55%22%20stroke-width%3D%220.5%22%2F%3E%3C%2Fsvg%3E')]" />
      </div>

      <Container size="wide" className="relative z-10 py-16 md:py-24">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[rgb(var(--text))] mb-6 leading-tight">
            Unlock Ancient{' '}
            <span className="text-[rgb(var(--accent))]">Mesopotamia</span>
          </h1>

          <p className="text-lg sm:text-xl text-[rgb(var(--text-secondary))] mb-8 max-w-2xl mx-auto">
            Join thousands of contributors using AI-powered transcription to decode
            humanity's earliest written records. No expertise required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Link to="/contribute">
              <Button size="lg" variant="primary">
                Start Contributing
              </Button>
            </Link>
            <Button size="lg" variant="secondary" onClick={() => {
              document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
            }}>
              Learn More
            </Button>
          </div>

          {/* Live contribution counter */}
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-[rgb(var(--surface))] rounded-full border border-[rgb(var(--border))]">
            <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" aria-hidden="true" />
            <span className="text-[rgb(var(--text))]">
              <strong className="text-[rgb(var(--accent))] font-mono">
                {contributionCount.toLocaleString()}
              </strong>
              {' '}contributions and counting
            </span>
          </div>
        </div>
      </Container>
    </section>
  )
}

/**
 * Section 2: Social Proof
 */
function SocialProofSection({ institutions }: { institutions: Institution[] }) {
  const stats = [
    { value: '50,000+', label: 'Contributions' },
    { value: '1,200+', label: 'Tablets Transcribed' },
    { value: '150+', label: 'Expert Reviewers' },
  ]

  // Filter key partners
  const keyPartners = institutions.filter(i =>
    ['inst-yale', 'inst-british-museum', 'inst-cdli'].includes(i.id) ||
    i.name.includes('Yale') ||
    i.name.includes('British Museum') ||
    i.name.includes('CDLI')
  ).slice(0, 4)

  return (
    <section className="py-16 bg-[rgb(var(--surface))]">
      <Container>
        <Stack space="xl">
          {/* Stats grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            {stats.map((stat) => (
              <div key={stat.label}>
                <span className="block text-4xl md:text-5xl font-bold text-[rgb(var(--accent))]">
                  {stat.value}
                </span>
                <span className="text-[rgb(var(--text-secondary))]">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>

          {/* Partner logos */}
          <div>
            <p className="text-center text-sm text-[rgb(var(--text-muted))] mb-6 uppercase tracking-wide">
              Trusted by Leading Institutions
            </p>
            <div className="flex flex-wrap justify-center items-center gap-4">
              {keyPartners.length > 0 ? (
                keyPartners.map((institution) => (
                  <InstitutionBadge
                    key={institution.id}
                    institution={institution}
                    variant="default"
                  />
                ))
              ) : (
                // Fallback placeholders
                <>
                  <div className="px-4 py-2 bg-[rgb(var(--background))] rounded-lg text-[rgb(var(--text-secondary))]">
                    Yale University
                  </div>
                  <div className="px-4 py-2 bg-[rgb(var(--background))] rounded-lg text-[rgb(var(--text-secondary))]">
                    British Museum
                  </div>
                  <div className="px-4 py-2 bg-[rgb(var(--background))] rounded-lg text-[rgb(var(--text-secondary))]">
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
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
      ),
    },
  ]

  return (
    <section className="py-16">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-[rgb(var(--text))] mb-4">
              How You Can Help
            </h2>
            <p className="text-[rgb(var(--text-secondary))] max-w-2xl mx-auto">
              Choose your path to contribute to decoding ancient Mesopotamian texts.
              Every contribution advances our understanding of human history.
            </p>
          </div>

          <Grid columns={3} gap="lg">
            {paths.map((path) => (
              <article
                key={path.id}
                className={`
                  bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl p-6
                  transition-all hover:border-[rgb(var(--accent)/.5)]
                  ${path.available ? 'hover:shadow-lg hover:shadow-[rgb(var(--accent)/.1)]' : 'opacity-75'}
                `}
              >
                <div className="text-[rgb(var(--accent))] mb-4">
                  {path.icon}
                </div>
                <h3 className="text-xl font-semibold text-[rgb(var(--text))] mb-2">
                  {path.title}
                </h3>
                <p className="text-[rgb(var(--text-secondary))] mb-4 text-sm">
                  {path.description}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-muted))]">
                    {path.timeCommitment}
                  </span>
                  {path.available ? (
                    <Link to={path.href}>
                      <Button size="sm" variant="primary">
                        {path.cta}
                      </Button>
                    </Link>
                  ) : (
                    <Button size="sm" variant="secondary" disabled>
                      {path.cta}
                    </Button>
                  )}
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
 * Section 4: How It Works
 */
function HowItWorksSection() {
  const steps = [
    {
      number: 1,
      title: 'View Ancient Tablet',
      description: 'We show you a photograph of a cuneiform tablet from a major museum collection.',
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <line x1="7" y1="8" x2="17" y2="8"/>
          <line x1="7" y1="12" x2="15" y2="12"/>
          <line x1="7" y1="16" x2="12" y2="16"/>
        </svg>
      ),
    },
    {
      number: 2,
      title: 'Identify Cuneiform Signs',
      description: 'Match highlighted signs from the tablet with reference examples using visual comparison.',
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          <path d="M8 11h6"/>
          <path d="M11 8v6"/>
        </svg>
      ),
    },
    {
      number: 3,
      title: 'AI Validates Your Work',
      description: 'Our AI compares your input with consensus data and prior expert transcriptions.',
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 2a10 10 0 1 0 10 10H12V2z"/>
          <path d="M12 2a10 10 0 0 1 10 10"/>
          <circle cx="12" cy="12" r="4" fill="currentColor" fillOpacity="0.2"/>
        </svg>
      ),
    },
    {
      number: 4,
      title: 'Experts Review & Publish',
      description: 'Scholars verify crowdsourced data and publish verified transcriptions to CDLI.',
      icon: (
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
      ),
    },
  ]

  return (
    <section id="how-it-works" className="py-16 bg-[rgb(var(--surface))]">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-[rgb(var(--text))] mb-4">
              How It Works
            </h2>
            <p className="text-[rgb(var(--text-secondary))] max-w-2xl mx-auto">
              A simple four-step process transforms your quick contributions
              into verified scholarly data.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, index) => (
              <article
                key={step.number}
                className="relative text-center p-6"
              >
                {/* Connector line for desktop */}
                {index < steps.length - 1 && (
                  <div
                    className="hidden lg:block absolute top-12 left-1/2 w-full h-px bg-[rgb(var(--border))]"
                    aria-hidden="true"
                  />
                )}

                {/* Step icon */}
                <div className="relative z-10 inline-flex items-center justify-center w-20 h-20 rounded-full bg-[rgb(var(--background))] border-2 border-[rgb(var(--accent))] text-[rgb(var(--accent))] mb-4">
                  {step.icon}
                </div>

                {/* Step number badge */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[rgb(var(--accent))] text-black font-bold text-sm flex items-center justify-center">
                  {step.number}
                </div>

                <h3 className="text-lg font-semibold text-[rgb(var(--text))] mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-[rgb(var(--text-secondary))]">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </Stack>
      </Container>
    </section>
  )
}

/**
 * Section 5: For Scholars
 */
function ForScholarsSection({ experts, institutions }: { experts: Expert[]; institutions: Institution[] }) {
  // Filter for research platforms
  const platforms = institutions.filter(i =>
    i.id === 'inst-cdli' || i.id === 'inst-oracc' ||
    i.name.includes('CDLI') || i.name.includes('ORACC')
  )

  return (
    <section className="py-16">
      <Container>
        <Stack space="xl">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-[rgb(var(--text))] mb-4">
              For Scholars
            </h2>
            <p className="text-[rgb(var(--text-secondary))] max-w-2xl mx-auto">
              Glintstone integrates with established scholarly infrastructure
              and is built with input from leading Assyriologists.
            </p>
          </div>

          {/* Integration badges */}
          <div className="flex flex-wrap justify-center gap-4">
            {platforms.length > 0 ? (
              platforms.map((platform) => (
                <InstitutionBadge
                  key={platform.id}
                  institution={platform}
                  variant="default"
                />
              ))
            ) : (
              <>
                <div className="px-4 py-2 bg-[rgb(var(--surface))] rounded-lg border border-[rgb(var(--border))] text-[rgb(var(--text-secondary))]">
                  CDLI Integration
                </div>
                <div className="px-4 py-2 bg-[rgb(var(--surface))] rounded-lg border border-[rgb(var(--border))] text-[rgb(var(--text-secondary))]">
                  ORACC Compatible
                </div>
              </>
            )}
          </div>

          {/* Expert testimonials */}
          <div>
            <h3 className="text-center text-lg font-semibold text-[rgb(var(--text))] mb-6">
              What Experts Say
            </h3>
            <Grid columns={3} gap="md">
              {experts.length > 0 ? (
                experts.map((expert) => (
                  <div key={expert.id} className="flex flex-col gap-4">
                    <blockquote className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-lg p-4 italic text-[rgb(var(--text-secondary))]">
                      "Glintstone's approach to crowdsourced transcription could revolutionize
                      how we process the vast corpus of untranscribed tablets."
                    </blockquote>
                    <ExpertCard expert={expert} variant="compact" />
                  </div>
                ))
              ) : (
                // Fallback testimonials
                [1, 2, 3].map((i) => (
                  <div key={i} className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-lg p-4">
                    <p className="italic text-[rgb(var(--text-secondary))] mb-4">
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
 * Section 6: Final CTA + Footer
 */
function FinalCTASection() {
  return (
    <>
      {/* Final CTA */}
      <section className="py-20 bg-gradient-to-b from-[rgb(var(--surface))] to-[rgb(var(--background))]">
        <Container size="narrow">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-[rgb(var(--text))] mb-4">
              Ready to Contribute?
            </h2>
            <p className="text-lg text-[rgb(var(--text-secondary))] mb-8">
              Join our community of citizen scholars and help unlock
              the secrets of ancient Mesopotamia.
            </p>
            <Link to="/contribute">
              <Button size="lg" variant="primary">
                Start Contributing Now
              </Button>
            </Link>
          </div>
        </Container>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-[rgb(var(--border))]">
        <Container>
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-[rgb(var(--text))]">
              <svg
                className="w-6 h-6 text-[rgb(var(--accent))]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <path d="M9 3v18"/>
                <path d="M3 9h6"/>
              </svg>
              <span className="font-semibold">Glintstone</span>
            </div>

            <nav className="flex flex-wrap justify-center gap-6 text-sm">
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text))] transition-colors">
                About
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text))] transition-colors">
                Contact
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text))] transition-colors">
                Privacy
              </a>
              <a href="#" className="text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text))] transition-colors">
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
