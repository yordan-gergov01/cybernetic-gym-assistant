import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ErrorNote, Icon } from '../../components/ui'
import { photosApi } from '../photos/api'
import type { BfPhoto, ProfileDraft } from './types'
import type { BFAssessment, PhotoAngle } from '../../types/api'

const ANGLES: { angle: PhotoAngle; label: string; hint: string }[] = [
  { angle: 'front', label: 'Отпред', hint: 'отпуснат корем, ръце до тялото' },
  { angle: 'side', label: 'Отстрани', hint: 'профил, без да се извиваш' },
  { angle: 'back', label: 'Отзад', hint: 'по избор, но помага' },
]

const CONFIDENCE_BG: Record<BFAssessment['confidence'], string> = {
  high: 'висока сигурност',
  medium: 'средна сигурност',
  low: 'ниска сигурност',
}

/** Body-fat estimate from photos, taken here and now.
 *
 *  The estimate has to be final before the wizard ends: the profile value feeds the
 *  deterministic calculators (LBM -> BMR -> macros), and recalculating them later with
 *  a corrected number would mean the user got wrong targets in between. So the step
 *  uploads, assesses, and only then writes `body_fat_pct` into the draft. A
 *  low-confidence read is never written silently - the user decides. */
export function BfPhotoCapture({ draft, update }: { draft: ProfileDraft; update: (patch: ProfileDraft) => void }) {
  const photos = draft.bf_photos ?? []
  const assessment = draft.bf_assessment
  const [pending, setPending] = useState<PhotoAngle | null>(null)

  const upload = useMutation({
    mutationFn: ({ file, angle }: { file: File; angle: PhotoAngle }) => photosApi.upload(file, angle),
    onMutate: ({ angle }) => setPending(angle),
    onSettled: () => setPending(null),
    onSuccess: (photo, { angle }) => {
      const next: BfPhoto = { angle, id: photo.id, url: photo.url }
      // Re-shooting an angle replaces it, and invalidates any estimate made from the
      // previous set - otherwise the shown number would not match the shown photos.
      update({ bf_photos: [...photos.filter((p) => p.angle !== angle), next], bf_assessment: undefined })
    },
  })

  const assess = useMutation({
    mutationFn: () =>
      photosApi.assessBf({
        photo_ids: photos.map((p) => p.id),
        apply_to_profile: false,
        sex: draft.sex,
      }),
    onSuccess: (result) => {
      update({
        bf_assessment: result,
        // A low-confidence estimate is offered, not applied - see the prompt below.
        body_fat_pct: result.confidence === 'low' ? undefined : result.bf_pct,
      })
    },
  })

  const removePhoto = (photo: BfPhoto) => {
    photosApi.remove(photo.id).catch(() => {
      /* The row is orphaned in storage at worst; the wizard must not get stuck on it. */
    })
    update({ bf_photos: photos.filter((p) => p.id !== photo.id), bf_assessment: undefined, body_fat_pct: undefined })
  }

  const busy = upload.isPending || assess.isPending

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        {ANGLES.map(({ angle, label, hint }) => (
          <PhotoSlot
            key={angle}
            label={label}
            hint={hint}
            photo={photos.find((p) => p.angle === angle)}
            uploading={pending === angle}
            disabled={busy}
            onPick={(file) => upload.mutate({ file, angle })}
            onRemove={removePhoto}
          />
        ))}
      </div>

      {upload.error && <ErrorNote error={upload.error} />}

      {photos.length > 0 && !assessment && (
        <button
          type="button"
          onClick={() => assess.mutate()}
          disabled={busy}
          className="btn-primary w-full"
        >
          {assess.isPending ? 'Оценяваме снимките…' : 'Оцени процента мазнини'}
        </button>
      )}

      {assess.error && <ErrorNote error={assess.error} onRetry={() => assess.mutate()} />}

      {assessment && (
        <AssessmentResult
          assessment={assessment}
          accepted={draft.body_fat_pct !== undefined}
          onAccept={() => update({ body_fat_pct: assessment.bf_pct })}
          onRedo={() => update({ bf_assessment: undefined, body_fat_pct: undefined })}
        />
      )}
    </div>
  )
}

function PhotoSlot({
  label,
  hint,
  photo,
  uploading,
  disabled,
  onPick,
  onRemove,
}: {
  label: string
  hint: string
  photo?: BfPhoto
  uploading: boolean
  disabled: boolean
  onPick: (file: File) => void
  onRemove: (photo: BfPhoto) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className={`tap relative flex aspect-3/4 w-full items-center justify-center overflow-hidden rounded-2xl border disabled:opacity-40 ${
          photo ? 'border-volt-500' : 'border-dashed border-ink-600 bg-ink-800'
        }`}
        aria-label={`Снимка ${label}`}
      >
        {photo?.url ? (
          <img src={photo.url} alt="" className="h-full w-full object-cover" />
        ) : photo ? (
          <Icon name="check" size={22} />
        ) : uploading ? (
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink-600 border-t-volt-500" />
        ) : (
          <Icon name="camera" size={22} />
        )}
        {uploading && photo && <span className="absolute inset-0 bg-ink-950/60" />}
      </button>

      <p className="mt-1.5 text-center text-xs font-semibold text-chalk-300">{label}</p>
      <p className="text-center text-[11px] leading-tight text-chalk-500">{hint}</p>

      {photo && (
        <button
          type="button"
          onClick={() => onRemove(photo)}
          disabled={disabled}
          className="tap mt-1 w-full text-center text-[11px] text-chalk-500 underline disabled:opacity-40"
        >
          Премахни
        </button>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          // Reset so picking the same file twice still fires a change event.
          e.target.value = ''
          if (file) onPick(file)
        }}
      />
    </div>
  )
}

function AssessmentResult({
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
        {CONFIDENCE_BG[assessment.confidence]} · {assessment.photo_count} сн.
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
