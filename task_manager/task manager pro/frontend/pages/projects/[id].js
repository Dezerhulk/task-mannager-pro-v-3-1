import { useRouter } from 'next/router';
import NavBar from '../../components/NavBar';
import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import KanbanBoard from '../../components/KanbanBoard';

export default function ProjectDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [project, setProject] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) load();
  }, [id]);

  async function load() {
    setError('');
    try {
      const p = await apiClient(`/api/projects/${id}`);
      setProject(p);
    } catch (err) {
      setError(err?.message || 'Failed to load project');
    }
  }

  return (
    <div>
      <NavBar />
      <main className="page">
        <div className="card wide">
          {project ? (
            <>
              <h1>{project.title}</h1>
              <p className="muted">{project.description}</p>
              <KanbanBoard projectId={id} />
            </>
          ) : (
            <p>{error || 'Loading project...'}</p>
          )}
        </div>
      </main>
    </div>
  );
}
