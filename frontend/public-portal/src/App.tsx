import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { MapPin, Activity, ShieldCheck, LogIn, Menu, X, Phone, HeartPulse } from 'lucide-react';
import '../shared/theme.css';
import './App.css';

// Components (defined below for brevity in one file, or imported)
const LandingPage = () => (
  <div className="landing-container">
    <section className="hero">
      <div className="hero-content">
        <h1>Healthcare <span>Decentralized</span></h1>
        <p>Connecting citizens with verified facilities and government health initiatives in real-time.</p>
        <div className="hero-btns">
          <Link to="/map" className="btn-primary">Explore Nearby</Link>
          <Link to="/request" className="btn-secondary">Raise Request</Link>
        </div>
      </div>
    </section>
    
    <section className="features grid">
      <div className="glass-card feature-item">
        <MapPin size={32} color="var(--accent)" />
        <h3>Verified Discovery</h3>
        <p>Only government-approved hospitals and clinics appear on our maps.</p>
      </div>
      <div className="glass-card feature-item">
        <Activity size={32} color="var(--primary)" />
        <h3>Demand-Driven</h3>
        <p>Your requests help health field teams prioritize their routes.</p>
      </div>
      <div className="glass-card feature-item">
        <ShieldCheck size={32} color="var(--success)" />
        <h3>Privacy First</h3>
        <p>Your data is region-scoped and never exposed publicly.</p>
      </div>
    </section>
  </div>
);


const NavBar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

  return (
    <nav className="navbar glass-card">
      <div className="nav-brand">
        <HeartPulse size={28} color="var(--primary)" />
        <span>HealthSaaS</span>
      </div>

      <div className={`nav-links ${isOpen ? 'open' : ''}`}>
        <Link to="/" onClick={closeMenu}>Home</Link>
        <Link to="/map" onClick={closeMenu}>Map</Link>
        <Link to="/request" onClick={closeMenu}>Requests</Link>
        <Link to="/login" className="btn-login" onClick={closeMenu}>
          <LogIn size={18} /> Login
        </Link>
      </div>

      <button
        type="button"
        className="nav-toggle"
        aria-label={isOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X /> : <Menu />}
      </button>
    </nav>
  );
};


const Auth = () => {
  const [mobile, setMobile] = useState('');
  const [otp, setOtp] = useState('');
  const [isSent, setIsSent] = useState(false);
  const navigate = useNavigate();

  const handleSend = () => setIsSent(true);
  const handleVerify = () => {
    localStorage.setItem('access_token', 'mock_token');
    navigate('/');
  };

  return (
    <div className="auth-container">
      <div className="glass-card auth-card">
        <h2>{isSent ? 'Verify OTP' : 'Login'}</h2>
        {!isSent ? (
          <>
            <div className="input-group">
              <Phone size={20} />
              <input 
                type="text" 
                placeholder="Mobile Number" 
                value={mobile} 
                onChange={(e) => setMobile(e.target.value)} 
              />
            </div>
            <button className="btn-primary w-full" onClick={handleSend}>Send OTP</button>
          </>
        ) : (
          <>
            <div className="input-group">
              <ShieldCheck size={20} />
              <input 
                type="text" 
                placeholder="6-digit OTP" 
                value={otp} 
                onChange={(e) => setOtp(e.target.value)} 
              />
            </div>
            <button className="btn-primary w-full" onClick={handleVerify}>Verify & Login</button>
            <button className="btn-text" onClick={() => setIsSent(false)}>Edit Number</button>
          </>
        )}
      </div>
    </div>
  );
};

const MapDiscovery = () => {
  const mapContainer = React.useRef<any>(null);
  const map = React.useRef<any>(null);

  React.useEffect(() => {
    if (map.current) return;
    (window as any).mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
    map.current = new (window as any).mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [78.0322, 30.3165], // Dehradun
      zoom: 12
    });

    // Add mock markers
    new (window as any).mapboxgl.Marker({ color: 'var(--primary)' })
      .setLngLat([78.0322, 30.3165])
      .setPopup(new (window as any).mapboxgl.Popup().setHTML('<h3>Doon City Hospital</h3>'))
      .addTo(map.current);
  }, []);

  return (
    <div className="page-container">
      <div className="section-header">
        <h2>Verified <span>Facilities</span></h2>
        <p>Locate approved hospitals, clinics, and blood banks near you.</p>
      </div>
      <div className="map-wrapper glass-card" style={{ height: '500px', overflow: 'hidden', position: 'relative' }}>
        <div ref={mapContainer} className="map-container" style={{ height: '100%', width: '100%' }} />
        <div className="map-overlay glass-card" style={{ position: 'absolute', bottom: '20px', left: '20px', padding: '15px', zIndex: 1 }}>
          <h3>Dehradun Region</h3>
          <p>Showing 12 verified locations</p>
        </div>
      </div>
    </div>
  );
};

const ServiceRequest = () => {
  const [submitted, setSubmitted] = useState(false);
  return (
    <div className="page-container">
      <div className="section-header">
        <h2>Raise <span>Service Request</span></h2>
        <p>Request help for vaccinations, screenings, or emergency services.</p>
      </div>
      {!submitted ? (
        <div className="glass-card form-card">
          <div className="input-group">
            <Activity size={20} />
            <select>
              <option>Polio Vaccination</option>
              <option>TB Screening</option>
              <option>Blood Requirement</option>
              <option>General Checkup</option>
            </select>
          </div>
          <div className="input-group">
            <MapPin size={20} />
            <input type="text" placeholder="Current Location / Address" />
          </div>
          <button className="btn-primary w-full" onClick={() => setSubmitted(true)}>Submit Request</button>
        </div>
      ) : (
        <div className="glass-card success-card">
          <ShieldCheck size={48} color="var(--success)" />
          <h3>Request Logged</h3>
          <p>Government health teams have been notified. Your request ID is #REQ-1024.</p>
          <button className="btn-secondary" onClick={() => setSubmitted(false)}>Back</button>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app-shell">
        <NavBar />
        <main className="content">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Auth />} />
            <Route path="/map" element={<MapDiscovery />} />
            <Route path="/request" element={<ServiceRequest />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
