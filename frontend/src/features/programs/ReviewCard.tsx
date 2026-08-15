import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Callout, ErrorNote, type CalloutTone } from '../../components/ui'
import { muscleLabel } from '../../constants/muscles'
import { queryKeys } from '../../constants/query-keys'
import type { ProgramAction, ProgramReview } from '../../types/api'
import { programsApi } from './api'

/** Tone follows the verdict, not the layout: "keep going" and "your recovery is the
 *  problem" must not look the same at a glance. Each one is paired with a title that
 *  says it in words too. */
const TONES: Record<ProgramAction, CalloutTone> = {
  extend: 'ok',
  adjust_exercise: 'warn',
  adjust_muscle: 'warn',
  check_recovery: 'danger',
  complete: 'accent',
}

const TITLES: Record<ProgramAction, string> = {
  extend: 'Програмата продължава',
  adjust_exercise: 'Смени или интензифицирай упражнението',
  adjust_muscle: 'Вдигни честотата на групата',
  check_recovery: 'Провери възстановяването',
  complete: 'Време е за нова програма',
}

/**
 * The plateau engine's verdict for this program, plus the one action it allows.
 *
 * Nothing is decided here: the wording of the reason comes from the backend, and
 * extending is refused there when something is stalling, so the button is offered
 * whenever the verdict is `extend` and the API gets the final say.
 */
export function ReviewCard({ programId, review }: { programId: string; review: ProgramReview }) {
  const queryClient = useQueryClient()

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.program(programId) })
    queryClient.invalidateQueries({ queryKey: queryKeys.programReview(programId) })
    queryClient.invalidateQueries({ queryKey: queryKeys.programs })
    // Today reads the same prescription: week count, sets and rep ranges all show there.
    queryClient.invalidateQueries({ queryKey: queryKeys.today })
  }

  const extend = useMutation({ mutationFn: () => programsApi.extend(programId), onSuccess: refresh })

  const intensify = useMutation({
    mutationFn: () => programsApi.intensifyExercise(programId, review.exercise_name ?? ''),
    onSuccess: refresh,
  })

  const adjustMuscle = useMutation({
    mutationFn: () => programsApi.adjustMuscle(programId, review.muscle_group ?? ''),
    onSuccess: refresh,
  })

  const applied = intensify.data ?? adjustMuscle.data
  const applyError = intensify.error ?? adjustMuscle.error

  const muscle = muscleLabel(review.muscle_group)
  const title =
    review.action === 'adjust_muscle' && muscle ? `${TITLES.adjust_muscle}: ${muscle}` : TITLES[review.action]

  return (
    <Callout tone={TONES[review.action]} title={title}>
      <p>{review.reason_bg}</p>

      {review.action === 'adjust_exercise' && (
        <p className="mt-2">
          {review.new_rep_target
            ? `Свали целта до ${review.new_rep_target} повторения на серия. Ако това не сработи, смени упражнението.`
            : 'Повторенията вече не могат да се свалят под минимума - остава смяна с алтернатива.'}
        </p>
      )}

      <p className="mt-2 text-xs text-chalk-500">
        {review.sessions_analysed} анализирани сесии · {review.total_weeks} от максимум{' '}
        {review.max_weeks} седмици
      </p>

      {review.action === 'extend' && (
        <>
          {extend.error && (
            <div className="mt-3">
              <ErrorNote error={extend.error} />
            </div>
          )}
          <button
            type="button"
            onClick={() => extend.mutate()}
            disabled={extend.isPending}
            className="btn-primary mt-3 w-full"
          >
            {extend.isPending ? 'Удължавам…' : 'Удължи с 1 седмица'}
          </button>
        </>
      )}

      {review.action === 'check_recovery' && (
        <Link to="/check-in" className="btn-outline mt-3 w-full">
          Направи чек-ин
        </Link>
      )}

      {applied && <p className="mt-3 text-sm text-ok-400">{applied.summary_bg}</p>}
      {applyError && (
        <div className="mt-3">
          <ErrorNote error={applyError} />
        </div>
      )}

      {/* Intensifying is the first of the two options the course gives for a single
          stalled lift; replacing it is the other, and lives on the exercise itself. */}
      {review.action === 'adjust_exercise' && review.new_rep_target && (
        <button
          type="button"
          onClick={() => intensify.mutate()}
          disabled={intensify.isPending}
          className="btn-primary mt-3 w-full"
        >
          {intensify.isPending ? 'Прилагам…' : `Свали целта до ${review.new_rep_target} повторения`}
        </button>
      )}

      {review.action === 'adjust_muscle' && review.muscle_group && (
        <button
          type="button"
          onClick={() => adjustMuscle.mutate()}
          disabled={adjustMuscle.isPending}
          className="btn-primary mt-3 w-full"
        >
          {/* Not "raise the frequency": the backend raises it only if the week has room
              for another session, and otherwise adds a set, so the label cannot promise
              which of the two happens. */}
          {adjustMuscle.isPending ? 'Прилагам…' : `Приложи промяната за ${muscle}`}
        </button>
      )}

      {(review.action === 'adjust_exercise' || review.action === 'adjust_muscle') &&
        review.muscle_group && (
          <Link
            to={`/exercises?muscle=${encodeURIComponent(review.muscle_group)}`}
            className="btn-outline mt-3 w-full"
          >
            Виж упражнения за {muscle}
          </Link>
        )}
    </Callout>
  )
}
