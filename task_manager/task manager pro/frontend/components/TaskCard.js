import Link from 'next/link';

export default function TaskCard({ task }) {
  return (
    <div className="task-card">
      <h4>{task.title || 'Untitled'}</h4>
      <p className="muted">{task.description || ''}</p>
      <div className="meta">
        <small>{task.assignee ? `Assignee: ${task.assignee}` : 'Unassigned'}</small>
        <Link href={`/tasks/${task.id}`} className="link-button" style={{ marginLeft: 8 }}>
          View
        </Link>
      </div>
    </div>
  );
}
