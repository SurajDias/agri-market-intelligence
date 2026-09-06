import React from 'react';
import { User, Building, Bell, Sliders } from 'lucide-react';
import { MOCK_USER } from '../services/mockData';

const SettingsPage: React.FC = () => {
  return (
    <div className="settings-page flex flex-col gap-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Settings & Preferences</h1>
          <p className="section-subtitle">Manage organization profile, default commodity preferences, and alerts.</p>
        </div>
      </div>

      <div className="card flex flex-col gap-4">
        <h3 className="section-title">User & Organization Profile</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="input-group">
            <label className="input-label">Full Name</label>
            <input type="text" className="input" defaultValue={MOCK_USER.name} />
          </div>
          <div className="input-group">
            <label className="input-label">Email</label>
            <input type="email" className="input" defaultValue={MOCK_USER.email} />
          </div>
          <div className="input-group">
            <label className="input-label">Organization Name</label>
            <input type="text" className="input" defaultValue={MOCK_USER.organization} />
          </div>
          <div className="input-group">
            <label className="input-label">Role</label>
            <input type="text" className="input" defaultValue={MOCK_USER.role} disabled />
          </div>
        </div>
        <button className="btn btn-primary btn-sm w-fit mt-2">Save Profile Changes</button>
      </div>
    </div>
  );
};

export default SettingsPage;
