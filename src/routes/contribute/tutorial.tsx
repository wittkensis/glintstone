import { useState, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Container, Stack, Button, Grid, SignCard } from '../../components'
import type { TaskOption } from '../../types'

// Demo task for tutorial
const demoTask = {
  id: 'demo-task',
  signImage: '/images/signs/sign-001.png',
  options: [
    { id: 'demo-a', label: 'KUR', image: '/images/signs/sign-034.png' },
    { id: 'demo-b', label: 'GAL', image: '/images/signs/sign-015.png' },
    { id: 'demo-c', label: 'UR', image: '/images/signs/sign-001.png' },
    { id: 'demo-d', label: 'GI', image: '/images/signs/sign-042.png' },
  ] as TaskOption[],
  correctAnswer: 'demo-c',
}

/**
 * J2 Screen 2: Mini Tutorial
 * Shows an animated example of sign matching
 */
export function ContributeTutorial() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [autoAdvanceTimer, setAutoAdvanceTimer] = useState(15)

  // Auto-advance countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setAutoAdvanceTimer((prev) => {
        if (prev <= 1) {
          navigate({ to: '/contribute/task' })
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [navigate])

  // Tutorial steps animation
  useEffect(() => {
    if (step === 0) {
      // Step 1: Show the sign to match (after 1s)
      const timer1 = setTimeout(() => setStep(1), 1000)
      return () => clearTimeout(timer1)
    }
    if (step === 1) {
      // Step 2: Highlight options (after 2s)
      const timer2 = setTimeout(() => setStep(2), 2000)
      return () => clearTimeout(timer2)
    }
    if (step === 2) {
      // Step 3: Auto-select correct answer (after 2s)
      const timer3 = setTimeout(() => {
        setSelectedOption('demo-c')
        setStep(3)
      }, 2000)
      return () => clearTimeout(timer3)
    }
    if (step === 3) {
      // Step 4: Show feedback (after 1s)
      const timer4 = setTimeout(() => {
        setShowFeedback(true)
        setStep(4)
      }, 1000)
      return () => clearTimeout(timer4)
    }
  }, [step])

  const handleSkip = () => {
    navigate({ to: '/contribute/task' })
  }

  const handleGotIt = () => {
    navigate({ to: '/contribute/task' })
  }

  return (
    <div className="min-h-[60vh] py-8 animate-fadeIn">
      <Container size="narrow">
        <Stack space="xl">
          {/* Header */}
          <div className="text-center">
            <span className="inline-block px-3 py-1 bg-[rgb(var(--accent)/.1)] text-[rgb(var(--accent))] text-sm rounded-full mb-4">
              Quick Tutorial
            </span>
            <h1 className="text-2xl md:text-3xl font-bold text-[rgb(var(--text))] mb-2">
              How Sign Matching Works
            </h1>
            <p className="text-[rgb(var(--text-secondary))]">
              Watch the example below - it takes just a few seconds
            </p>
          </div>

          {/* Demo task card */}
          <div className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl overflow-hidden">
            {/* Progress indicator */}
            <div className="h-1 bg-[rgb(var(--background))]">
              <div
                className="h-full bg-[rgb(var(--accent))] transition-all duration-1000"
                style={{ width: `${(step / 4) * 100}%` }}
              />
            </div>

            <div className="p-6">
              <Stack space="lg">
                {/* Step 1: Source sign */}
                <div className={`transition-opacity duration-500 ${step >= 1 ? 'opacity-100' : 'opacity-30'}`}>
                  <div className="flex flex-col items-center gap-4 p-4 bg-[rgb(var(--background))] rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-[rgb(var(--accent))] text-black text-sm font-bold flex items-center justify-center">
                        1
                      </span>
                      <p className="text-sm text-[rgb(var(--text-secondary))]">
                        Look at this sign from the tablet
                      </p>
                    </div>
                    <div className={`w-32 h-32 bg-[#f8f4f0] rounded-lg flex items-center justify-center shadow-[inset_0_0_10px_rgba(0,0,0,0.05)] transition-all duration-300 ${step >= 1 ? 'ring-2 ring-[rgb(var(--accent))]' : ''}`}>
                      <img
                        src={demoTask.signImage}
                        alt="Sign to match"
                        className="max-w-[80%] max-h-[80%] object-contain"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"%3E%3Crect fill="%23f8f4f0" width="100" height="100"/%3E%3Ctext x="50" y="55" text-anchor="middle" fill="%23666" font-size="40"%3E%E2%9C%A6%3C/text%3E%3C/svg%3E'
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Step 2: Options */}
                <div className={`transition-opacity duration-500 ${step >= 2 ? 'opacity-100' : 'opacity-30'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-6 h-6 rounded-full bg-[rgb(var(--accent))] text-black text-sm font-bold flex items-center justify-center">
                      2
                    </span>
                    <p className="text-sm text-[rgb(var(--text-secondary))]">
                      Find the matching option
                    </p>
                  </div>
                  <Grid columns={4} gap="sm">
                    {demoTask.options.map((option) => (
                      <div
                        key={option.id}
                        className={`
                          relative transition-all
                          ${showFeedback && option.id === demoTask.correctAnswer ? 'ring-2 ring-green-500 rounded-lg' : ''}
                        `}
                      >
                        <SignCard
                          option={option}
                          selected={selectedOption === option.id}
                          onSelect={() => {}}
                        />
                        {showFeedback && option.id === demoTask.correctAnswer && (
                          <span className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center z-10">
                            <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <path d="M20 6L9 17l-5-5"/>
                            </svg>
                          </span>
                        )}
                      </div>
                    ))}
                  </Grid>
                </div>

                {/* Step 3: Feedback */}
                {showFeedback && (
                  <div className="animate-slideUp">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-6 h-6 rounded-full bg-[rgb(var(--accent))] text-black text-sm font-bold flex items-center justify-center">
                        3
                      </span>
                      <p className="text-sm text-[rgb(var(--text-secondary))]">
                        Get instant feedback
                      </p>
                    </div>
                    <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <path d="M20 6L9 17l-5-5"/>
                        </svg>
                      </div>
                      <div>
                        <p className="font-semibold text-green-400">Correct!</p>
                        <p className="text-sm text-[rgb(var(--text-secondary))]">
                          This is the sign "UR" meaning "dog" or "servant"
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </Stack>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-[rgb(var(--surface)/.5)] rounded-lg p-4 border border-[rgb(var(--border))]">
            <h3 className="font-semibold text-[rgb(var(--text))] mb-2">Quick Tips</h3>
            <ul className="text-sm text-[rgb(var(--text-secondary))] space-y-1">
              <li className="flex items-start gap-2">
                <span className="text-[rgb(var(--accent))]">*</span>
                Look for similar wedge patterns and angles
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[rgb(var(--accent))]">*</span>
                Don't worry about making mistakes - AI validates your work
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[rgb(var(--accent))]">*</span>
                You can skip any task you're unsure about
              </li>
            </ul>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <Button size="lg" variant="primary" onClick={handleGotIt}>
              Got It - Start Tasks
            </Button>
            <button
              onClick={handleSkip}
              className="text-sm text-[rgb(var(--text-muted))] hover:text-[rgb(var(--text-secondary))] transition-colors"
            >
              Skip tutorial ({autoAdvanceTimer}s)
            </button>
          </div>
        </Stack>
      </Container>
    </div>
  )
}
