import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { useAuth } from '../features/auth/useAuth'
import { CoachPage } from '../pages/CoachPage'
import { LoginPage } from '../pages/LoginPage'
import { NutritionPage } from '../pages/NutritionPage'
import { ProgressPage } from '../pages/ProgressPage'
import { TodayPage } from '../pages/TodayPage'

/** Auth is a hard gate: unauthenticated users only ever see the login screen, so no
 *  protected route needs its own guard. */
export function AppRouter() {
  const { isAuthed } = useAuth()

  return (
    <BrowserRouter>
      {isAuthed ? (
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<TodayPage />} />
            <Route path="nutrition" element={<NutritionPage />} />
            <Route path="progress" element={<ProgressPage />} />
            <Route path="coach" element={<CoachPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      ) : (
        <Routes>
          <Route path="*" element={<LoginPage />} />
        </Routes>
      )}
    </BrowserRouter>
  )
}
