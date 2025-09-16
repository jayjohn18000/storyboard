import React, { useState } from 'react';
import { getCurrentUser } from '../../utils/auth';
import {
  UserIcon,
  Cog6ToothIcon,
  BellIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
} from '@heroicons/react/24/outline';

export const ProfilePage: React.FC = () => {
  const user = getCurrentUser();
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'preferences', name: 'Preferences', icon: Cog6ToothIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'appearance', name: 'Appearance', icon: PaintBrushIcon },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
        <p className="text-gray-600">Manage your account settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-3" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="card p-6">
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900">Profile Information</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name
                    </label>
                    <input
                      type="text"
                      value={user?.name || ''}
                      className="input-field"
                      readOnly
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      className="input-field"
                      readOnly
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role
                    </label>
                    <input
                      type="text"
                      value={user?.role || ''}
                      className="input-field"
                      readOnly
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900">Preferences</h2>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Auto-save</h3>
                      <p className="text-sm text-gray-500">Automatically save changes</p>
                    </div>
                    <input 
                      type="checkbox" 
                      defaultChecked 
                      className="rounded" 
                      aria-label="Enable auto-save"
                      title="Enable auto-save"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Email notifications</h3>
                      <p className="text-sm text-gray-500">Receive email updates</p>
                    </div>
                    <input 
                      type="checkbox" 
                      defaultChecked 
                      className="rounded" 
                      aria-label="Enable email notifications"
                      title="Enable email notifications"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Dark mode</h3>
                      <p className="text-sm text-gray-500">Use dark theme</p>
                    </div>
                    <input 
                      type="checkbox" 
                      className="rounded" 
                      aria-label="Enable dark mode"
                      title="Enable dark mode"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900">Notification Settings</h2>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Render completion</h3>
                      <p className="text-sm text-gray-500">Notify when renders finish</p>
                    </div>
                    <input 
                      type="checkbox" 
                      defaultChecked 
                      className="rounded" 
                      aria-label="Notify on render completion"
                      title="Notify on render completion"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Evidence processing</h3>
                      <p className="text-sm text-gray-500">Notify when evidence is processed</p>
                    </div>
                    <input 
                      type="checkbox" 
                      defaultChecked 
                      className="rounded" 
                      aria-label="Notify on evidence processing"
                      title="Notify on evidence processing"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Validation errors</h3>
                      <p className="text-sm text-gray-500">Notify about validation issues</p>
                    </div>
                    <input 
                      type="checkbox" 
                      defaultChecked 
                      className="rounded" 
                      aria-label="Notify on validation errors"
                      title="Notify on validation errors"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900">Security Settings</h2>
                
                <div className="space-y-4">
                  <button className="btn-secondary">
                    Change Password
                  </button>
                  
                  <button className="btn-secondary">
                    Enable Two-Factor Authentication
                  </button>
                  
                  <button className="btn-secondary">
                    View Login History
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900">Appearance</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Theme
                    </label>
                    <select 
                      className="input-field"
                      aria-label="Select theme"
                      title="Select theme"
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="auto">Auto</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Font Size
                    </label>
                    <select 
                      className="input-field"
                      aria-label="Select font size"
                      title="Select font size"
                    >
                      <option value="small">Small</option>
                      <option value="medium" selected>Medium</option>
                      <option value="large">Large</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Density
                    </label>
                    <select 
                      className="input-field"
                      aria-label="Select density"
                      title="Select density"
                    >
                      <option value="compact">Compact</option>
                      <option value="comfortable" selected>Comfortable</option>
                      <option value="spacious">Spacious</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
