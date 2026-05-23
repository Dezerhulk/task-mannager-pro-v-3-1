import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import NavBar from '../components/NavBar';
import { useAuth } from '../context/AuthContext';
import { apiClient, ApiError } from '../lib/api';

export default function Dashboard() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (user) {
      loadProjects();
    }
  }, [user]);

  async function loadProjects() {
    setError('');
    try {
      const data = await apiClient('/api/projects');
      setProjects(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout();
        router.replace('/login');
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setError('You do not have permission to view projects.');
        return;
      }
      setError(err?.message || 'Unable to load projects.');
    }
  }

  if (isLoading) {
    return <div className="page"><div className="card"><p>Loading dashboard...</p></div></div>;
  }

  return (
    <div>
      <NavBar />
      <main className="page">
        <div className="card wide">
          <h1>Dashboard</h1>
          {user && (
            <div className="info">
              <p>Signed in as <strong>{user.username}</strong></p>
              <p>Role: {user.role}</p>
            </div>
          )}
          <button className="logout-button" onClick={() => { logout(); router.push('/login'); }}>
            Logout
          </button>
          {error && <p className="error">{error}</p>}
          <section className="projects">
            <h2>Projects</h2>
            {projects.length === 0 ? (
              <p>No projects available yet.</p>
            ) : (
              <ul>
                {projects.map((project) => (
                  <li key={project.id}>
                    <strong>{project.title}</strong>
                    <p>{project.description || 'No description provided.'}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
