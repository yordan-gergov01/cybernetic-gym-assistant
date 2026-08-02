import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ErrorNote, Icon, Stat } from '../../components/ui'
import { queryKeys } from '../../constants/query-keys'
import { profileApi } from '../onboarding/api'
import { programsApi } from './api'
import { GeneratingState } from './GeneratingState'

/**
 * Shown on Today when the user has a profile but no program yet - the state right
 * after onboarding. It also repairs the case where the calculators did not run, since
 * program generation depends on their output.
 */
export function StartProgramCard() {
  const queryClient = useQueryClient()
  const profile = useQuery({ queryKey: queryKeys.profile, queryFn: profileApi.get })
  const energy = profile.data?.calculator_results?.energy

  const recalculate = useMutation({
    mutationFn: programsApi.recalculate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.profile }),
  })

  const generate = useMutation({
    mutationFn: () => programsApi.generate(8),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs })
      queryClient.invalidateQueries({ queryKey: queryKeys.profile })
    },
  })

  if (generate.isPending) return <GeneratingState />

  // Macros missing means the calculators never ran - generating now would produce a
  // program with no numbers behind it, so fix that first.
  if (profile.data && !energy) {
    return (
      <div className="card">
        <div className="mb-3 flex items-center gap-2">
          <Icon name="alert" size={18} className="text-warn-400" />
          <p className="font-semibold text-warn-400">Липсват изчисленията</p>
        </div>
        <p className="mb-4 text-sm leading-relaxed text-chalk-300">
          Профилът ти е записан, но калориите и макросите не са изчислени. Без тях програмата няма
          на какво да стъпи.
        </p>
        {recalculate.error && (
          <div className="mb-3">
            <ErrorNote error={recalculate.error} />
          </div>
        )}
        <button
          onClick={() => recalculate.mutate()}
          disabled={recalculate.isPending}
          className="btn-primary w-full"
        >
          {recalculate.isPending ? 'Изчислявам…' : 'Изчисли отново'}
        </button>
      </div>
    )
  }

  return (
    <div className="card">
      <p className="mb-1 font-semibold text-chalk-50">Готов си за програма</p>
      <p className="mb-4 text-sm leading-relaxed text-chalk-500">
        Ще съставим 8-седмична програма - спрямо целта, нивото,
        оборудването и възстановяването ти.
      </p>

      {energy && (
        <div className="mb-4 flex items-end gap-6 border-y border-ink-700 py-4">
          <Stat value={Math.round(energy.target_kcal ?? 0)} unit="ккал" label="дневна цел" tone="accent" size="sm" />
          <Stat value={Math.round(energy.protein_g ?? 0)} unit="г" label="протеин" tone="ok" size="sm" />
        </div>
      )}

      {generate.error && (
        <div className="mb-3">
          <ErrorNote error={generate.error} />
        </div>
      )}

      <button onClick={() => generate.mutate()} className="btn-primary w-full">
        Създай програмата ми
      </button>
    </div>
  )
}
