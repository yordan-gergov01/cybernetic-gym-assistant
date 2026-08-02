import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { queryKeys } from '../constants/query-keys'
import { OnboardingWizard } from '../features/onboarding/OnboardingWizard'

export function OnboardingPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return (
    <OnboardingWizard
      onDone={() => {
        // The saved profile drives macros and program generation, so everything
        // downstream must refetch before the user lands on Today.
        queryClient.invalidateQueries({ queryKey: queryKeys.profile })
        navigate('/', { replace: true })
      }}
    />
  )
}
