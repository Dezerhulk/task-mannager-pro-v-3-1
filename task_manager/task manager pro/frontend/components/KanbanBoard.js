import { useEffect, useState } from 'react';
import TaskCard from './TaskCard';
import { apiClient } from '../lib/api';

const columns = [
  { id: 'pending', title: 'Backlog' },
  { id: 'processing', title: 'In Progress' },
  { id: 'done', title: 'Done' },
  { id: 'error', title: 'Errors' },
];

export default function KanbanBoard({ projectId }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    try {
      const data = await apiClient(`/api/projects/${projectId}/tasks`);
      setTasks(data || []);
    } catch (e) {
      setError(e?.message || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [projectId]);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await apiClient(`/api/projects/${projectId}/tasks`, {
        method: 'POST',
        body: JSON.stringify({ title, description }),
      });
      setTitle(''); setDescription('');
      load();
    } catch (err) {
      setError(err?.message || 'Failed to create task');
    }
  }

  const byStatus = columns.reduce((acc, c) => { acc[c.id] = []; return acc; }, {});
  tasks.forEach(t => { (byStatus[t.status] || []).push(t); });

  return (
    <div className="kanban">
      <div className="kanban-header">
        <form onSubmit={handleCreate} className="kanban-form">
          <input placeholder="Task title" value={title} onChange={(e)=>setTitle(e.target.value)} required />
          <input placeholder="Short description" value={description} onChange={(e)=>setDescription(e.target.value)} />
          <button type="submit">Add</button>
        </form>
        <button onClick={load} className="link-button">Refresh</button>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="kanban-board">
        {columns.map(col => (
          <div key={col.id} className="kanban-column">
            <h3>{col.title}</h3>
            <div className="kanban-column-body">
              {loading ? <p>Loading...</p> : (
                byStatus[col.id].length === 0 ? <p className="muted">No tasks</p> : (
                  byStatus[col.id].map(t => <TaskCard key={t.id} task={t} />)
                )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
