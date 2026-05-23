import Link from 'next/link';
import { useAuth } from '../context/AuthContext';

export default function NavBar() {
  const { user, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="brand">
        <span className="brand-badge"><span className="dot" /> Task Manager Pro</span>
      </div>
      <nav>
        <Link href="/dashboard">Dashboard</Link>
        <Link href="/projects">Projects</Link>
        {!user ? (
          <>
            <Link href="/login">Login</Link>
            <Link href="/register">Register</Link>
          </>
        ) : (
          <button className="link-button" onClick={logout}>Logout</button>
        )}
      </nav>
    </header>
  );
}
