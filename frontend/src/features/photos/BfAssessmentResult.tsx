import { CONFIDENCE_LABEL } from '../onboarding/constants'
import type { BFAssessment } from '../../types/api'

/** What the vision model saw, stated honestly - the range and the confidence are part
 *  of the answer, not a footnote. A low-confidence read is offered, never applied on
 *  its own, because this number drives the macro calculation. */
export function BfAssessmentResult({
  assessment,
  accepted,
  onAccept,
  onRedo,
}: {
  assessment: BFAssessment
  accepted: boolean
  onAccept: () => void
  onRedo: () => void
}) {
  const low = assessment.confidence === 'low'

  return (
    <div className={`card space-y-3 ${low ? 'border-danger-400/40' : 'border-volt-500/40'}`}>
      <div className="flex items-baseline gap-2">
        <span className="stat text-volt-400">{assessment.bf_pct}%</span>
        <span className="num text-sm text-chalk-500">
          ({assessment.range_low}–{assessment.range_high}%)
        </span>
      </div>
      <p className={`text-xs font-semibold ${low ? 'text-danger-400' : 'text-chalk-300'}`}>
        {CONFIDENCE_LABEL[assessment.confidence]} · {assessment.photo_count} сн.
      </p>

      {assessment.reasoning_bg && (
        <p className="text-sm leading-relaxed text-chalk-300">{assessment.reasoning_bg}</p>
      )}
      {assessment.limitations && (
        <p className="text-xs leading-relaxed text-chalk-500">{assessment.limitations}</p>
      )}

      {low && !accepted && (
        <p className="text-sm leading-relaxed text-danger-400">
          Оценката е несигурна - от тези снимки не се вижда достатъчно. По-добре снимай пак
          при по-добра светлина. Ако решиш да я ползваме въпреки това, макросите ти ще
          стъпят на нея.
        </p>
      )}

      <div className="flex gap-2">
        {low && !accepted && (
          <button type="button" onClick={onAccept} className="btn-ghost flex-1">
            Ползвай въпреки това
          </button>
        )}
        <button type="button" onClick={onRedo} className="btn-ghost flex-1">
          Оцени пак
        </button>
      </div>
    </div>
  )
}
