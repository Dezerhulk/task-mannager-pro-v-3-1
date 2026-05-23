import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import NavBar from '../components/NavBar';

export default function Login() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoading && user) {
      router.replace('/dashboard');
    }
  }, [user, isLoading, router]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');

    try {
      await login({ username, password });
      router.push('/dashboard');
    } catch (err) {
      setError(err?.message || 'Login failed, please check your credentials.');
    }
  }

  return (
    <div>
      <NavBar />
      <div className="page">
        <div className="card">
        <h1>Login</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={10}
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Sign in</button>
        </form>
        <p>
          New here? <Link href="/register">Create an account</Link>
        </p>
        </div>
      </div>
    </div>
  );
}
