import { render } from 'preact';
import { LocationProvider, Router, Route } from 'preact-iso';

import { Header } from './components/Header.jsx';
import { Home } from './pages/Home/index.jsx';
import { Login } from './pages/Login/index.jsx';
import { Signup } from './pages/Signup/index.jsx';
import { Notifications } from './pages/Notifications/index.jsx';
import { Preferences } from './pages/Preferences/index.jsx';
import { NotFound } from './pages/_404.jsx';
import './style.css';
import 'bulma/css/bulma.min.css';

export function App() {
	return (
		<LocationProvider>
			<Header />
			<main>
				<Router>
					<Route path="/" component={Home} />
					<Route path="/login" component={Login} />
					<Route path="/signup" component={Signup} />
					<Route path="/notifications" component={Notifications} />
					<Route path="/preferences" component={Preferences} />
					<Route default component={NotFound} />
				</Router>
			</main>
		</LocationProvider>
	);
}

render(<App />, document.getElementById('app'));
