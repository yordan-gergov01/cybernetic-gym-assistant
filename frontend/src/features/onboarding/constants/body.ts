import type { BFAssessment, PhotoAngle } from '../../../types/api'

/** Angles asked for in the body-fat step. Front and side carry most of the visual
 *  markers the rubric relies on; back is optional but sharpens the read. */
export const BF_PHOTO_ANGLES: { angle: PhotoAngle; label: string; hint: string }[] = [
  { angle: 'front', label: 'Отпред', hint: 'отпуснат корем, ръце до тялото' },
  { angle: 'side', label: 'Отстрани', hint: 'профил, без да се извиваш' },
  { angle: 'back', label: 'Отзад', hint: 'по избор, но помага' },
]

export const CONFIDENCE_LABEL: Record<BFAssessment['confidence'], string> = {
  high: 'висока сигурност',
  medium: 'средна сигурност',
  low: 'ниска сигурност',
}
