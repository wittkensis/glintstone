import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Container, Stack, TaskCard, SignMatchTask, Button } from '../../components'
import { useTaskStore } from '../../stores/taskStore'
import { useSessionStore } from '../../stores/sessionStore'

// Fun facts about cuneiform to display every 3rd task
const funFacts = [
  {
    title: 'Did You Know?',
    fact: 'Cuneiform is one of the earliest writing systems, invented over 5,000 years ago in ancient Mesopotamia.',
  },
  {
    title: 'Ancient Accountants',
    fact: 'Most cuneiform tablets are actually ancient receipts, contracts, and administrative records - the spreadsheets of their time!',
  },
  {
    title: 'Massive Archive',
    fact: 'There are over 500,000 known cuneiform tablets, but only a fraction have been fully translated.',
  },
  {
    title: 'Multilingual Writing',
    fact: 'Cuneiform was used to write multiple languages including Sumerian, Akkadian, Babylonian, and Hittite.',
  },
  {
    title: 'Clay Forever',
    fact: 'Clay tablets have survived for millennia. Many were accidentally preserved when libraries burned down - the fire baked them solid!',
  },
]

/**
 * J2 Screen 3-5: Task Loop
 * Main contribution interface - sign matching tasks
 */
export function ContributeTask() {
  const navigate = useNavigate()
  const {
    currentTask,
    taskIndex,
    totalTasks,
    completedTasks,
    loadNextTask,
    completeTask,
    skipTask,
    getAccuracy,
  } = useTaskStore()
  const { endSession } = useSessionStore()

  const [feedback, setFeedback] = useState<{ type: 'correct' | 'incorrect'; message: string } | null>(null)
  const [showFunFact, setShowFunFact] = useState(false)
  const [currentFunFact, setCurrentFunFact] = useState(funFacts[0])

  // Redirect if no task available
  useEffect(() => {
    if (!currentTask && completedTasks === 0) {
      // No tasks loaded - redirect to welcome
      navigate({ to: '/contribute' })
    }
  }, [currentTask, completedTasks, navigate])

  // Handle task completion
  const handleSubmit = useCallback((selectedOptionId: string) => {
    if (!currentTask) return

    const isCorrect = selectedOptionId === currentTask.correctAnswer
    completeTask(selectedOptionId, isCorrect)

    // Find the label of the selected option
    const selectedOption = currentTask.options.find(o => o.id === selectedOptionId)
    const correctOption = currentTask.options.find(o => o.id === currentTask.correctAnswer)

    // Show feedback
    setFeedback({
      type: isCorrect ? 'correct' : 'incorrect',
      message: isCorrect
        ? `Correct! This is "${correctOption?.label}"`
        : `Not quite. The answer was "${correctOption?.label}". You selected "${selectedOption?.label}"`,
    })

    // After feedback, check if we should show fun fact or move on
    setTimeout(() => {
      setFeedback(null)

      // Check if this is every 3rd completed task
      const newCompletedCount = completedTasks + 1
      if (newCompletedCount % 3 === 0 && newCompletedCount < totalTasks) {
        // Show fun fact
        setCurrentFunFact(funFacts[Math.floor(Math.random() * funFacts.length)])
        setShowFunFact(true)
      } else {
        // Move to next task or summary
        advanceTask()
      }
    }, 1500)
  }, [currentTask, completeTask, completedTasks, totalTasks])

  const advanceTask = useCallback(() => {
    const newCompletedCount = completedTasks + 1

    if (newCompletedCount >= totalTasks) {
      // Session complete - go to summary
      const accuracy = getAccuracy()
      endSession(newCompletedCount, accuracy)
      navigate({ to: '/contribute/summary' })
    } else {
      // Load next task
      loadNextTask()
    }
  }, [completedTasks, totalTasks, loadNextTask, navigate, endSession, getAccuracy])

  const handleSkip = useCallback(() => {
    if (taskIndex >= totalTasks) {
      // Last task - go to summary
      const accuracy = getAccuracy()
      endSession(completedTasks, accuracy)
      navigate({ to: '/contribute/summary' })
    } else {
      skipTask()
    }
  }, [taskIndex, totalTasks, skipTask, navigate, endSession, completedTasks, getAccuracy])

  const handleFunFactDismiss = useCallback(() => {
    setShowFunFact(false)
    advanceTask()
  }, [advanceTask])

  // Loading state
  if (!currentTask) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[rgb(var(--accent))] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[rgb(var(--text-secondary))]">Loading task...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] py-8 animate-fadeIn">
      <Container size="default">
        {/* Fun Fact Modal */}
        {showFunFact && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 animate-fadeIn">
            <div className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] rounded-xl p-6 max-w-md w-full animate-slideUp">
              <div className="text-center">
                <span className="text-4xl mb-4 block" role="img" aria-label="Light bulb">
                  💡
                </span>
                <h3 className="text-xl font-bold text-[rgb(var(--accent))] mb-2">
                  {currentFunFact.title}
                </h3>
                <p className="text-[rgb(var(--text-secondary))] mb-6">
                  {currentFunFact.fact}
                </p>
                <Button variant="primary" onClick={handleFunFactDismiss}>
                  Continue
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Feedback Overlay */}
        {feedback && (
          <div className="fixed inset-0 z-40 flex items-center justify-center p-4 pointer-events-none">
            <div className={`
              p-6 rounded-xl shadow-2xl max-w-sm w-full animate-slideUp pointer-events-auto
              ${feedback.type === 'correct'
                ? 'bg-green-500/90 text-white'
                : 'bg-red-500/90 text-white'}
            `}>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                  {feedback.type === 'correct' ? (
                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                  ) : (
                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                  )}
                </div>
                <div>
                  <h3 className="font-bold text-lg">
                    {feedback.type === 'correct' ? 'Great Work!' : 'Nice Try!'}
                  </h3>
                  <p className="text-sm opacity-90">{feedback.message}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Task Interface */}
        <Stack space="lg">
          {/* Session progress header */}
          <div className="flex items-center justify-between text-sm text-[rgb(var(--text-secondary))]">
            <span>Session Progress</span>
            <span className="text-[rgb(var(--accent))] font-medium">
              {completedTasks} completed
            </span>
          </div>

          {/* Task Card */}
          <TaskCard
            title="Match the Sign"
            current={taskIndex}
            total={totalTasks}
            onSkip={handleSkip}
          >
            <SignMatchTask
              task={currentTask}
              onSubmit={handleSubmit}
            />
          </TaskCard>

          {/* Help text */}
          <p className="text-center text-sm text-[rgb(var(--text-muted))]">
            Compare the sign above with the options below. Click to select, then submit.
          </p>
        </Stack>
      </Container>
    </div>
  )
}
