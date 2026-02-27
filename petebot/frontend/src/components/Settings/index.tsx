import { useState } from 'react'
import { Save, Key, Bell, Palette, Shield, Database } from 'lucide-react'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general')

  const tabs = [
    { id: 'general', name: 'General', icon: Palette },
    { id: 'api', name: 'API Keys', icon: Key },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'data', name: 'Data', icon: Database },
  ]

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle mt-1">Manage your preferences</p>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
        {/* Tabs */}
        <div className="overflow-x-auto lg:w-56">
          <div className="flex gap-2 pb-1 lg:flex-col lg:gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`shrink-0 flex items-center px-4 py-3 rounded-lg transition-colors lg:w-full ${
                  activeTab === tab.id
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'muted-text hover:text-white hover:bg-white/5'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span className="ml-3">{tab.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 card">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h2 className="card-title">General Settings</h2>

              <div>
                <label className="field-label">Theme</label>
                <select className="input w-full max-w-xs">
                  <option>Dark</option>
                  <option>Light</option>
                  <option>System</option>
                </select>
              </div>

              <div>
                <label className="field-label">Default AI Model</label>
                <select className="input w-full max-w-xs">
                  <option>Claude Opus</option>
                  <option>Claude Sonnet</option>
                  <option>GPT-4</option>
                </select>
              </div>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-3" defaultChecked />
                  <span>Enable auto-save</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="space-y-6">
              <h2 className="card-title">API Keys</h2>

              <div>
                <label className="field-label">OpenAI API Key</label>
                <input type="password" className="input w-full max-w-md" placeholder="sk-..." />
              </div>

              <div>
                <label className="field-label">Anthropic API Key</label>
                <input type="password" className="input w-full max-w-md" placeholder="sk-ant-..." />
              </div>

              <div>
                <label className="field-label">Plaid Client ID</label>
                <input type="text" className="input w-full max-w-md" />
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="card-title">Notification Settings</h2>

              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <span>Desktop notifications</span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label className="flex items-center justify-between">
                  <span>Trading alerts</span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label className="flex items-center justify-between">
                  <span>Health reminders</span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label className="flex items-center justify-between">
                  <span>System updates</span>
                  <input type="checkbox" />
                </label>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="card-title">Security Settings</h2>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-3" defaultChecked />
                  <span>Use macOS Keychain for secrets</span>
                </label>
              </div>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-3" defaultChecked />
                  <span>Require confirmation for trades</span>
                </label>
              </div>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-3" />
                  <span>Enable audit logging</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="space-y-6">
              <h2 className="card-title">Data Management</h2>

              <div className="space-y-4">
                <button className="btn-secondary">Export All Data</button>
                <button className="btn-secondary">Clear Cache</button>
                <button className="btn-secondary text-red-400 hover:bg-red-500/20">
                  Delete All Data
                </button>
              </div>
            </div>
          )}

          <div className="mt-8 pt-6 border-t border-white/10">
            <button className="btn-primary flex items-center">
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
