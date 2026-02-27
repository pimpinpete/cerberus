import { TrendingUp, TrendingDown, DollarSign, Activity, Heart, Brain } from 'lucide-react'

const stats = [
  {
    name: 'Portfolio Value',
    value: '$127,432',
    change: '+2.5%',
    trend: 'up',
    icon: DollarSign
  },
  {
    name: 'Day P&L',
    value: '+$1,234',
    change: '+0.98%',
    trend: 'up',
    icon: TrendingUp
  },
  {
    name: 'Recovery Score',
    value: '78%',
    change: '+5%',
    trend: 'up',
    icon: Heart
  },
  {
    name: 'AI Queries Today',
    value: '47',
    change: '-12%',
    trend: 'down',
    icon: Brain
  },
]

export default function Dashboard() {
  return (
    <div className="stack">
      {/* Header */}
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle mt-1">Welcome back, Andrew</p>
      </div>

      {/* Stats Grid */}
      <div className="section-grid section-grid--4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center justify-between">
              <stat.icon className="w-8 h-8 text-primary-500" />
              <span className={`flex items-center text-sm font-medium ${
                stat.trend === 'up' ? 'text-green-400' : 'text-red-400'
              }`}>
                {stat.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 mr-1" />
                )}
                {stat.change}
              </span>
            </div>
            <div className="mt-4">
              <p className="metric-value">{stat.value}</p>
              <p className="muted-text text-sm">{stat.name}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="section-grid section-grid--2 lg:grid-cols-3 gap-6">
        {/* Portfolio Chart */}
        <div className="lg:col-span-2 card">
          <h2 className="card-title mb-4">Portfolio Performance</h2>
          <div className="h-64 flex items-center justify-center muted-text">
            Chart placeholder - integrate Recharts
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h2 className="card-title mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center p-3 surface-row">
                <Activity className="w-5 h-5 text-primary-500" />
                <div className="ml-3">
                  <p className="metric-pill">Activity {i}</p>
                  <p className="muted-text text-xs">Just now</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="card-title mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-4">
          <button className="btn-primary">New Trade</button>
          <button className="btn-secondary">Ask AI</button>
          <button className="btn-secondary">View Portfolio</button>
          <button className="btn-secondary">Check Health</button>
        </div>
      </div>
    </div>
  )
}
