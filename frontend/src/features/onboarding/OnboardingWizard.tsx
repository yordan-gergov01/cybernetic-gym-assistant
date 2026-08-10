import { ErrorNote, Icon } from '../../components/ui'
import { STEP_COMPONENTS } from './steps'
import { useOnboarding } from './useOnboarding'

export function OnboardingWizard({ onDone }: { onDone: () => void }) {
  const wizard = useOnboarding(onDone)
  const StepComponent = STEP_COMPONENTS[wizard.step]

  return (
    <div className="flex min-h-dvh flex-col bg-ink-950">
      {/* Progress chrome.
          The inset is applied via calc() rather than the `safe-top` utility: both set
          padding-top, so combining them with pt-* silently drops one of the two and
          the progress bar ends up flush against the screen edge. */}
      <header
        className="sticky top-0 z-20 border-b border-ink-700 bg-ink-950/95 px-4 pb-3 backdrop-blur"
        style={{ paddingTop: 'calc(env(safe-area-inset-top) + 12px)' }}
      >
        <div className="mx-auto max-w-lg">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={wizard.back}
              disabled={wizard.index === 0}
              className="tap -ml-2 flex h-11 w-11 items-center justify-center rounded-xl text-chalk-300 active:bg-ink-800 disabled:opacity-0"
              aria-label="Назад"
            >
              <Icon name="chevronLeft" size={22} />
            </button>

            {/* The section name is what makes sixteen questions feel finite. */}
            <span className="font-display text-lg font-bold tracking-[0.14em] uppercase">
              {wizard.group}
            </span>

            <span className="label-micro w-11 text-right tabular-nums">
              {wizard.index + 1}/{wizard.total}
            </span>
          </div>

          <div
            className="mt-3 flex gap-1"
            role="progressbar"
            aria-label="Напредък по настройката"
            aria-valuenow={wizard.index + 1}
            aria-valuemin={1}
            aria-valuemax={wizard.total}
          >
            {Array.from({ length: wizard.total }, (_, i) => (
              <span
                key={i}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  i < wizard.index ? 'bg-volt-600' : i === wizard.index ? 'bg-volt-400' : 'bg-ink-700'
                }`}
              />
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-lg flex-1 px-4 pb-32">
        <StepComponent draft={wizard.draft} update={wizard.update} />
        {wizard.saveError && (
          <div className="mt-6">
            <ErrorNote error={wizard.saveError} />
          </div>
        )}
      </main>

      {/* Same reason as the header: the inset is folded into a calc() so it adds to the
          padding instead of replacing it. */}
      <div
        className="fixed inset-x-0 bottom-0 border-t border-ink-700 bg-ink-950/95 px-4 pt-3 backdrop-blur"
        style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 12px)' }}
      >
        <div className="mx-auto max-w-lg">
          <button
            onClick={wizard.next}
            disabled={!wizard.canAdvance || wizard.isSaving}
            className="btn-primary w-full"
          >
            {wizard.isSaving ? 'Създаваме плана…' : wizard.isLast ? 'Готово' : 'Напред'}
          </button>
          {!wizard.canAdvance && (
            <p className="mt-2 text-center text-xs text-chalk-500">Попълни всички полета, за да продължиш.</p>
          )}
        </div>
      </div>
    </div>
  )
}
