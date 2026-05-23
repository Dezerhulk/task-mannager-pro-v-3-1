import Link from 'next/link';
import NavBar from '../components/NavBar';
import { useEffect, useState } from 'react';
import { apiClient, ApiError } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function Projects() {
  const { user, isLoading, logout } = useAuth();
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoading && !user) return;
    load();
  }, [user, isLoading]);

  async function load() {
    setError('');
    try {
      const data = await apiClient('/api/projects');
      setProjects(data || []);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout();
        return;
      }
      setError(err?.message || 'Failed to load projects');
    }
  }

  return (
    <div>
      <NavBar />
      <main className="page">
        <div className="card wide">
          <h1>Projects</h1>
          {error && <p className="error">{error}</p>}
          {projects.length === 0 ? (
            <p>No projects yet.</p>
          ) : (
            <ul>
              {projects.map(p => (
                <li key={p.id}>
                  <strong><Link href={`/projects/${p.id}`}>{p.title}</Link></strong>
                  <p>{p.description}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
