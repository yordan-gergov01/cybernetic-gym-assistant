import { useRef } from 'react'
import { Icon } from '../../components/ui'
import type { BfPhoto } from '../onboarding/types'

/** One angle of the body-fat set: tap to shoot or pick, then the thumbnail. */
export function BfPhotoSlot({
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
