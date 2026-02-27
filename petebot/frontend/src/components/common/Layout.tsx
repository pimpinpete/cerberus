import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Activity,
  LayoutDashboard,
  TrendingUp,
  MessageSquare,
  Heart,
  Settings,
  Zap
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Trading', href: '/trading', icon: TrendingUp },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Health', href: '/health', icon: Heart },
  { name: 'Settings', href: '/settings', icon: Settings },
]

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const activeItem = navigation.find((item) => item.href === location.pathname) ?? navigation[0]

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-dark-950 text-white">
      {/* Mobile top bar */}
      <header className="fixed inset-x-0 top-0 z-40 border-b border-white/10 bg-black/50 backdrop-blur-xl lg:hidden pt-[env(safe-area-inset-top)]">
        <div className="flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-primary-500" />
            <div>
              <p className="text-sm font-semibold gradient-text">PeteBot</p>
              <p className="text-xs muted-text">{activeItem.name}</p>
            </div>
          </div>
          <div className="muted-text flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs">
            <Activity className="h-3.5 w-3.5 text-green-400" />
            Online
          </div>
        </div>
      </header>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/5 glass-dark lg:flex lg:flex-col">
        <div className="h-16 flex items-center px-6 border-b border-white/5">
          <Zap className="w-8 h-8 text-primary-500" />
          <span className="ml-3 text-xl font-bold gradient-text">PeteBot</span>
          <span className="ml-2 text-xs bg-primary-500/20 text-primary-400 px-2 py-0.5 rounded-full">V2</span>
        </div>

        <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center px-4 py-3 rounded-lg transition-all duration-200',
                  isActive
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'muted-text hover:text-white hover:bg-white/5'
                )}
              >
                <item.icon className="w-5 h-5" />
                <span className="ml-3 font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>

        <div className="mt-auto p-4 border-t border-white/5">
          <div className="glass p-3 rounded-lg">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="ml-2 muted-text">System Online</span>
            </div>
            <div className="mt-2 text-xs muted-text">
              Last sync: just now
            </div>
          </div>
        </div>
      </aside>

      <main className="pb-[calc(5rem+env(safe-area-inset-bottom))] pt-[calc(4rem+env(safe-area-inset-top))] lg:pb-0 lg:pl-64 lg:pt-0">
        <div className="p-4 sm:p-6 lg:p-8">
          {children}
        </div>
      </main>

      {/* Mobile tab bar */}
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-black/60 backdrop-blur-xl pb-[env(safe-area-inset-bottom)] lg:hidden">
        <div className="grid h-20 grid-cols-5">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex flex-col items-center justify-center gap-1 text-xs transition-colors',
                  isActive ? 'text-primary-400' : 'muted-text'
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
