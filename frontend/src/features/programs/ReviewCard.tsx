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

  const extend = useMutation({
    mutationFn: () => programsApi.extend(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.program(programId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.programReview(programId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.programs })
      // Today shows "седмица N от M" - the M just changed.
      queryClient.invalidateQueries({ queryKey: queryKeys.today })
    },
  })

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
