import NavBar from '../components/NavBar';
import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

export default function Profile() {
  const [me, setMe] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      const data = await apiClient('/api/auth/me');
      setMe(data);
    } catch (err) {
      setError(err?.message || 'Failed to load profile');
    }
  }

  return (
    <div>
      <NavBar />
      <main className="page">
        <div className="card">
          <h1>Profile</h1>
          {me ? (
            <div>
              <p><strong>Username:</strong> {me.username}</p>
              <p><strong>Role:</strong> {me.role}</p>
            </div>
          ) : (
            <p className="muted">{error || 'Loading...'}</p>
          )}
        </div>
      </main>
    </div>
  );
}
