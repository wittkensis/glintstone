import { useState } from 'react'
import type { Task, TaskOption } from '../../types'
import { SignCard } from '../tablet/SignCard'
import { Grid } from '../layout/Grid'

interface SignMatchTaskProps {
  task: Task
  onSubmit: (selectedOptionId: string) => void
  className?: string
}

/**
 * SignMatchTask - Complete sign-matching task UI.
 * The primary task type for J2 (Passerby) contributions.
 */
export function SignMatchTask({
  task,
  onSubmit,
  className = ''
}: SignMatchTaskProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null)

  const handleSelect = (option: TaskOption) => {
    setSelectedOption(option.id)
  }

  const handleSubmit = () => {
    if (selectedOption) {
      onSubmit(selectedOption)
      setSelectedOption(null) // Reset for next task
    }
  }

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      {/* Source sign to match */}
      <div className="flex flex-col items-center gap-4 p-6 bg-[rgb(var(--background))] rounded-lg">
        <p className="m-0 text-sm text-[rgb(var(--text-secondary))]">
          Find the matching sign
        </p>
        <figure className="flex flex-col items-center gap-2">
          <div className="w-32 h-32 bg-[#f8f4f0] rounded-lg flex items-center justify-center shadow-[inset_0_0_10px_rgba(0,0,0,0.05)]">
            <img
              src={task.signImage}
              alt="Sign to match"
              className="max-w-[80%] max-h-[80%] object-contain"
            />
          </div>
          <figcaption className="sr-only">
            The cuneiform sign you need to identify
          </figcaption>
        </figure>
      </div>

      {/* Options grid */}
      <div role="group" aria-label="Select the matching sign">
        <p className="m-0 mb-3 text-sm text-[rgb(var(--text-secondary))]">
          Select the matching option:
        </p>
        <Grid columns={4} gap="md">
          {task.options.map((option) => (
            <SignCard
              key={option.id}
              option={option}
              selected={selectedOption === option.id}
              onSelect={() => handleSelect(option)}
            />
          ))}
        </Grid>
      </div>

      {/* Submit button */}
      <div className="flex justify-center pt-4">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selectedOption}
          className={`
            px-8 py-3 rounded-lg text-base font-semibold cursor-pointer
            transition-all focus:outline-none focus:ring-2 focus:ring-offset-2
            ${selectedOption
              ? 'bg-[rgb(var(--accent))] text-black hover:brightness-110 focus:ring-[rgb(var(--accent))]'
              : 'bg-[rgb(var(--border))] text-[rgb(var(--text-muted))] cursor-not-allowed'
            }
          `}
          aria-disabled={!selectedOption}
        >
          Submit Answer
        </button>
      </div>
    </div>
  )
}
