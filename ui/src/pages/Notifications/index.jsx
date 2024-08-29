import { useState, useEffect } from 'preact/hooks';

export function Notifications() {
    const [notifications, setNotifications] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('/api/user/notifications', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                const data = await response.json();
                if (response.ok) {
                    setNotifications(data.notifications);
                } else {
                    setError(data.error);
                }
            } catch (err) {
                setError('Failed to fetch notifications');
            }
        };
        fetchNotifications();
    }, []);

    return (
        <section className="section">
            <div className="container">
                <h1 className="title">Notifications</h1>
                {error && <div className="notification is-danger">{error}</div>}
                <ul>
                    {notifications.map((notification) => (
                        <li key={notification.timestamp}>
                            <div className="card">
                                <div className="card-content">
                                    <p>{notification.text}</p>
                                    <small>{new Date(notification.timestamp).toLocaleString()}</small>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    );
}
