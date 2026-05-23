import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { apiClient } from '../lib/api';
import NavBar from '../components/NavBar';
import { useAuth } from '../context/AuthContext';

function Register() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setSuccess('');

    try {
      await apiClient('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      });
      // Login via AuthContext to set user state
      await login({ username, password });
      router.push('/dashboard');
    } catch (err) {
      setError(err?.message || 'Registration failed.');
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h1>Register</h1>
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
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
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
          {success && <p className="success">{success}</p>}
          <button type="submit">Create account</button>
        </form>
        <p>
          Already have an account? <Link href="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}

// Wrap page with NavBar for consistent navigation
export default function RegisterPageWrapper(props) {
  return (
    <div>
      <NavBar />
      <Register {...props} />
    </div>
  );
}
