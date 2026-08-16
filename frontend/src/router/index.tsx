import { useQuery } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { Loading } from '../components/ui'
import { queryKeys } from '../constants/query-keys'
import { useAuth } from '../features/auth/useAuth'
import { profileApi } from '../features/onboarding/api'
import { CheckInPage } from '../pages/CheckInPage'
import { CoachPage } from '../pages/CoachPage'
import { ExercisesPage } from '../pages/ExercisesPage'
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage'
import { LandingPage } from '../pages/LandingPage'
import { LoginPage } from '../pages/LoginPage'
import { NotificationsPage } from '../pages/NotificationsPage'
import { NutritionPage } from '../pages/NutritionPage'
import { OnboardingPage } from '../pages/OnboardingPage'
import { PhotosPage } from '../pages/PhotosPage'
import { ProfilePage } from '../pages/ProfilePage'
import { ProgramPage } from '../pages/ProgramPage'
import { ProgressPage } from '../pages/ProgressPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ResetPasswordPage } from '../pages/ResetPasswordPage'
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
        <Route path="program" element={<ProgramPage />} />
        <Route path="exercises" element={<ExercisesPage />} />
        <Route path="nutrition" element={<NutritionPage />} />
        <Route path="progress" element={<ProgressPage />} />
        <Route path="coach" element={<CoachPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="photos" element={<PhotosPage />} />
        <Route path="check-in" element={<CheckInPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

/** Auth is a hard gate: signed-out users only ever see the landing page and the two
 *  ways in. Any other path lands on the pitch rather than a dead end. */
export function AppRouter() {
  const { isAuthed, sessionExpired } = useAuth()

  return (
    <BrowserRouter>
      {isAuthed ? (
        <AuthedRoutes />
      ) : (
        <Routes>
          {/* Someone whose session just died is not a visitor to be pitched to - send
              them straight to the way back in, where the reason is explained. */}
          <Route
            path="/"
            element={sessionExpired ? <Navigate to="/login" replace /> : <LandingPage />}
          />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          {/* Reachable only while signed out - which is the state a forgotten password
              leaves you in. Someone already signed in changes it from the profile. */}
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </BrowserRouter>
  )
}
