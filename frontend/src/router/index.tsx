import { useQuery } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { Loading } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { useAuth } from '../features/auth/useAuth'
import { profileApi } from '../features/onboarding/api'
import { CoachPage } from '../pages/CoachPage'
import { LoginPage } from '../pages/LoginPage'
import { NutritionPage } from '../pages/NutritionPage'
import { OnboardingPage } from '../pages/OnboardingPage'
import { ProgressPage } from '../pages/ProgressPage'
import { TodayPage } from '../pages/TodayPage'

/** A profile row is created empty at registration, so "has a profile" is not enough —
 *  the setup counts as done only once the fields the calculators need are present. */
function useProfileComplete() {
  const query = useQuery({
    queryKey: queryKeys.profile,
    queryFn: profileApi.get,
    retry: false,
  })
  const p = query.data
  const complete = !!(p?.age && p?.sex && p?.height_cm && p?.bodyweight_kg && p?.goal && p?.training_status)
  return { isLoading: query.isLoading, complete }
}

function AuthedRoutes() {
  const { isLoading, complete } = useProfileComplete()

  if (isLoading) {
    return (
      <div className="grid min-h-dvh place-items-center bg-ink-950">
        <Loading />
      </div>
    )
  }

  if (!complete) {
    return (
      <Routes>
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="*" element={<Navigate to="/onboarding" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/onboarding" element={<Navigate to="/" replace />} />
      <Route element={<AppShell />}>
        <Route index element={<TodayPage />} />
        <Route path="nutrition" element={<NutritionPage />} />
        <Route path="progress" element={<ProgressPage />} />
        <Route path="coach" element={<CoachPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

/** Auth is a hard gate: unauthenticated users only ever see the login screen. */
export function AppRouter() {
  const { isAuthed } = useAuth()

  return (
    <BrowserRouter>
      {isAuthed ? (
        <AuthedRoutes />
      ) : (
        <Routes>
          <Route path="*" element={<LoginPage />} />
        </Routes>
      )}
    </BrowserRouter>
  )
}
