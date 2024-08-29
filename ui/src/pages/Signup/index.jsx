import { useState } from 'preact/hooks';
import { useLocation } from 'preact-iso';

export function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const location = useLocation();

    const handleSignup = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('token', data.access_token);
                location.route('/notifications');  // Redirect to notifications
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError('Something went wrong');
        }
    };

    return (
        <section className="section">
            <div className="container">
                <h1 className="title">Signup</h1>
                {error && <div className="notification is-danger">{error}</div>}
                <form onSubmit={handleSignup}>
                    <div className="field">
                        <label className="label">Email</label>
                        <div className="control">
                            <input className="input" type="email" value={email} onInput={(e) => setEmail(e.target.value)} required />
                        </div>
                    </div>
                    <div className="field">
                        <label className="label">Password</label>
                        <div className="control">
                            <input className="input" type="password" value={password} onInput={(e) => setPassword(e.target.value)} required />
                        </div>
                    </div>
                    <div className="field">
                        <div className="control">
                            <button className="button is-link">Signup</button>
                        </div>
                    </div>
                </form>
                <p>
                    Don't have an account? <a href="/signup">Sign up here</a>.
                </p>
            </div>
        </section>
    );
}
