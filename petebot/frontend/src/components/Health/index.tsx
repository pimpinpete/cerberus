import { Heart, Moon, Activity, Zap } from 'lucide-react'

const healthMetrics = [
  { name: 'Recovery', value: 78, unit: '%', icon: Heart, color: 'text-green-400' },
  { name: 'Sleep', value: 7.5, unit: 'hrs', icon: Moon, color: 'text-blue-400' },
  { name: 'Strain', value: 12.5, unit: '', icon: Activity, color: 'text-orange-400' },
  { name: 'HRV', value: 45, unit: 'ms', icon: Zap, color: 'text-purple-400' },
]

export default function Health() {
  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Health & Fitness</h1>
        <p className="page-subtitle mt-1">WHOOP data and health insights</p>
      </div>

      {/* Today's Metrics */}
      <div className="section-grid section-grid--4">
        {healthMetrics.map((metric) => (
          <div key={metric.name} className="card">
            <div className="flex items-center justify-between mb-4">
              <metric.icon className={`w-8 h-8 ${metric.color}`} />
              <span className="metric-pill">Today</span>
            </div>
            <p className="metric-value">
              {metric.value}
              <span className="text-lg font-normal muted-text ml-1">{metric.unit}</span>
            </p>
            <p className="muted-text text-sm mt-1">{metric.name}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="card-title mb-4">Recovery Trend</h2>
          <div className="h-64 flex items-center justify-center muted-text">
            Recovery chart - integrate Recharts
          </div>
        </div>

        <div className="card">
          <h2 className="card-title mb-4">Sleep History</h2>
          <div className="h-64 flex items-center justify-center muted-text">
            Sleep chart - integrate Recharts
          </div>
        </div>
      </div>

      {/* Recent Workouts */}
      <div className="card">
        <h2 className="card-title mb-4">Recent Workouts</h2>
        <div className="space-y-4">
          {[
            { activity: 'Running', strain: 15.5, duration: '45 min', calories: 450 },
            { activity: 'Strength Training', strain: 12.0, duration: '60 min', calories: 380 },
            { activity: 'Cycling', strain: 10.5, duration: '30 min', calories: 280 },
          ].map((workout, i) => (
            <div key={i} className="flex items-center justify-between p-4 surface-row">
              <div>
                <p className="metric-pill">{workout.activity}</p>
                <p className="muted-text text-sm">{workout.duration}</p>
              </div>
              <div className="text-right">
                <p className="text-primary-400 font-medium">{workout.strain} strain</p>
                <p className="muted-text text-sm">{workout.calories} cal</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
