import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ErrorNote } from '../../../components/ui'
import { photosApi } from '../../photos/api'
import { BF_PHOTO_ANGLES } from '../constants'
import { BfAssessmentResult } from '../../photos/BfAssessmentResult'
import { BfPhotoSlot } from '../../photos/BfPhotoSlot'
import type { BfPhoto, ProfileDraft } from '../types'
import type { PhotoAngle } from '../../../types/api'

/** Body-fat estimate from photos, taken here and now.
 *
 *  The estimate has to be final before the wizard ends: the profile value feeds the
 *  deterministic calculators (LBM -> BMR -> macros), and recalculating them later with
 *  a corrected number would mean the user got wrong targets in between. So the step
 *  uploads, assesses, and only then writes `body_fat_pct` into the draft. A
 *  low-confidence read is never written silently - the user decides. */
export function BfPhotoCapture({
  draft,
  update,
}: {
  draft: ProfileDraft
  update: (patch: ProfileDraft) => void
}) {
  const photos = draft.bf_photos ?? []
  const assessment = draft.bf_assessment
  const [pending, setPending] = useState<PhotoAngle | null>(null)

  const upload = useMutation({
    // This step is inside the wizard: the slot that failed is the only thing that says
    // which photo has to be taken again.
    meta: { inlineError: true },
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
    meta: { inlineError: true },
    mutationFn: () =>
      photosApi.assessBf({
        photo_ids: photos.map((p) => p.id),
        apply_to_profile: false,
        sex: draft.sex,
      }),
    onSuccess: (result) => {
      update({
        bf_assessment: result,
        // A low-confidence estimate is offered, not applied - see BfAssessmentResult.
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
        {BF_PHOTO_ANGLES.map(({ angle, label, hint }) => (
          <BfPhotoSlot
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
        <button type="button" onClick={() => assess.mutate()} disabled={busy} className="btn-primary w-full">
          {assess.isPending ? 'Оценяваме снимките…' : 'Оцени процента мазнини'}
        </button>
      )}

      {assess.error && <ErrorNote error={assess.error} onRetry={() => assess.mutate()} />}

      {assessment && (
        <BfAssessmentResult
          assessment={assessment}
          accepted={draft.body_fat_pct !== undefined}
          onAccept={() => update({ body_fat_pct: assessment.bf_pct })}
          onRedo={() => update({ bf_assessment: undefined, body_fat_pct: undefined })}
        />
      )}
    </div>
  )
}
