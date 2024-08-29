import { useState, useEffect } from 'preact/hooks';

export function Preferences() {
    const [preferences, setPreferences] = useState({ topic: '', min_distance: '', min_angle: '' });
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        const fetchPreferences = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('/api/user/preferences', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                const data = await response.json();
                if (response.ok) {
                    setPreferences(data);
                } else {
                    setError(data.error);
                }
            } catch (err) {
                setError('Failed to fetch preferences');
            }
        };
        fetchPreferences();
    }, []);

    const updatePreferences = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/user/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(preferences),
            });
            const data = await response.json();
            if (response.ok) {
                setMessage('Preferences updated successfully');
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError('Failed to update preferences');
        }
    };

    return (
        <section className="section">
            <div className="container">
                <h1 className="title">Preferences</h1>
                {error && <div className="notification is-danger">{error}</div>}
                {message && <div className="notification is-success">{message}</div>}
                <form onSubmit={updatePreferences}>
                    <div className="field">
                        <label className="label">Topic</label>
                        <div className="control">
                            <input className="input" type="text" value={preferences.topic} onInput={(e) => setPreferences({ ...preferences, topic: e.target.value })} />
                        </div>
                    </div>
                    <div className="field">
                        <label className="label">Minimum Distance</label>
                        <div className="control">
                            <input className="input" type="number" value={preferences.min_distance} onInput={(e) => setPreferences({ ...preferences, min_distance: e.target.value })} />
                        </div>
                    </div>
                    <div className="field">
                        <label className="label">Minimum Angle</label>
                        <div className="control">
                            <input className="input" type="number" value={preferences.min_angle} onInput={(e) => setPreferences({ ...preferences, min_angle: e.target.value })} />
                        </div>
                    </div>
                    <div className="field">
                        <div className="control">
                            <button className="button is-link">Save Preferences</button>
                        </div>
                    </div>
                </form>
            </div>
        </section>
    );
}
