import { ToastHost } from './components/ui'
import { AppRouter } from './router'

export default function App() {
  return (
    <>
      <AppRouter />
      {/* Outside the router: a failed request has to be reported wherever it happened,
          including the screens that live outside the signed-in shell. */}
      <ToastHost />
    </>
  )
}
