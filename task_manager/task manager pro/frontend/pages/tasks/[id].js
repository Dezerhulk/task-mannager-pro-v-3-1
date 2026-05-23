import NavBar from '../../components/NavBar';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiClient } from '../../lib/api';

export default function TaskDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [task, setTask] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { if (id) load(); }, [id]);

  async function load() {
    setError('');
    try {
      const t = await apiClient(`/tasks/${id}`);
      setTask(t);
    } catch (err) {
      setError(err?.message || 'Failed to load task');
    }
  }

  return (
    <div>
      <NavBar />
      <main className="page">
        <div className="card wide">
          {task ? (
            <>
              <h1>{task.title || 'Task'}</h1>
              <p>Status: <strong>{task.status}</strong></p>
              <p>Result: {task.result || '—'}</p>
              <p>{task.description}</p>
            </>
          ) : (
            <p>{error || 'Loading...'}</p>
          )}
        </div>
      </main>
    </div>
  );
}
