import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, Map as MapIcon, Route as RouteIcon, LogOut, CheckCircle, AlertCircle, TrendingUp, Navigation } from 'lucide-react';
import '../shared/theme.css';
import './App.css';

const Dashboard = () => {
  const mapContainer = React.useRef<any>(null);
  const map = React.useRef<any>(null);

  React.useEffect(() => {
    if (map.current) return;
    (window as any).mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
    map.current = new (window as any).mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [78.0322, 30.3165],
      zoom: 11
    });

    map.current.on('load', () => {
      // Add mock cluster data
      map.current.addSource('requests', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [
            { type: 'Feature', geometry: { type: 'Point', coordinates: [78.0322, 30.3165] }, properties: { id: 1 } },
            { type: 'Feature', geometry: { type: 'Point', coordinates: [78.04, 30.32] }, properties: { id: 2 } },
            { type: 'Feature', geometry: { type: 'Point', coordinates: [78.02, 30.31] }, properties: { id: 3 } }
          ]
        },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50
      });

      map.current.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'requests',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': ['step', ['get', 'point_count'], '#51bbd6', 100, '#f1f075', 750, '#f28cb1'],
          'circle-radius': ['step', ['get', 'point_count'], 20, 100, 30, 750, 40]
        }
      });
    });
  }, []);

  const stats = [
    { label: 'Active Requests', value: 42, icon: AlertCircle, color: 'var(--primary)' },
    { label: 'Routes Planned', value: 8, icon: RouteIcon, color: 'var(--secondary)' },
    { label: 'Resolved Today', value: 15, icon: CheckCircle, color: 'var(--success)' },
    { label: 'Efficiency', value: '88%', icon: TrendingUp, color: 'var(--accent)' },
  ];

  return (
    <div className="dashboard-container">
      <div className="section-header">
        <h1>Operations <span>Dashboard</span></h1>
        <p>Real-time overview of regional healthcare demands and task progress.</p>
      </div>
      <div className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="glass-card stat-card">
            <s.icon size={24} color={s.color} />
            <div className="stat-info">
              <span className="stat-value">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="grid">
        <div className="glass-card p-0 col-span-2" style={{ height: '400px', overflow: 'hidden', position: 'relative' }}>
           <div ref={mapContainer} style={{ height: '100%', width: '100%' }} />
           <div style={{ position: 'absolute', top: '20px', left: '20px', zIndex: 1 }}>
              <h3 style={{ margin: 0, textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>Live Demand Mapping</h3>
           </div>
        </div>
        <div className="glass-card p-20">
           <h3>Recent Activity</h3>
           <ul className="activity-list" style={{ listStyle: 'none', padding: 0 }}>
             <li style={{ marginBottom: '10px' }}><span className="badge success">Closed</span> Request #REQ-098</li>
             <li style={{ marginBottom: '10px' }}><span className="badge primary">Route</span> New plan for TB Screening</li>
             <li style={{ marginBottom: '10px' }}><span className="badge secondary">Alert</span> 5 new Polio requests</li>
           </ul>
        </div>
      </div>
    </div>
  );
};

const RoutePlanner = () => {
  const [generating, setGenerating] = useState(false);
  const [route, setRoute] = useState<any>(null);

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
       setRoute({ id: 'R-762', nodes: 8, distance: '12.4km' });
       setGenerating(false);
    }, 2000);
  };

  return (
    <div className="page-container">
      <div className="section-header">
        <h1>Route <span>Intelligence</span></h1>
        <p>Generate optimized visit paths based on TSP algorithm and current demand.</p>
      </div>
      <div className="planner-shell">
        <div className="glass-card planner-controls">
           <h3>New Route Plan</h3>
           <div className="input-field">
             <label>Service Category</label>
             <select>
               <option>Polio Vaccination</option>
               <option>TB Screening</option>
             </select>
           </div>
           <button className="btn-primary w-full" onClick={handleGenerate} disabled={generating}>
             {generating ? 'Optimizing...' : 'Generate Route'}
           </button>
        </div>
        <div className="glass-card route-preview">
           {!route ? (
             <div className="empty-state">
                <Navigation size={48} color="var(--text-muted)" />
                <p>No route generated yet.</p>
             </div>
           ) : (
             <div className="route-details">
                <div className="route-header">
                   <h3>Plan {route.id}</h3>
                   <span className="badge primary">Optimized</span>
                </div>
                <div className="route-stats">
                   <div className="r-stat"><span>Nodes</span> <strong>{route.nodes}</strong></div>
                   <div className="r-stat"><span>Distance</span> <strong>{route.distance}</strong></div>
                </div>
                <div className="node-list">
                  <div className="node-item"><span>1</span> Patient A (0.5km)</div>
                  <div className="node-item"><span>2</span> Patient B (1.2km)</div>
                  <div className="node-item"><span>3</span> Clinic C (2.8km)</div>
                </div>
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

const NavBar = () => (
  <nav className="nav-sidebar glass-card">
    <div className="nav-brand">
      <LayoutDashboard size={28} color="var(--primary)" />
      <span>GovtOps</span>
    </div>
    <div className="nav-menu">
      <Link to="/"><LayoutDashboard size={20} /> Dashboard</Link>
      <Link to="/map"><MapIcon size={20} /> Field Map</Link>
      <Link to="/routes"><RouteIcon size={20} /> Planning</Link>
    </div>
    <div className="nav-footer">
      <button className="btn-logout"><LogOut size={20} /> Sign Out</button>
    </div>
  </nav>
);

function App() {
  return (
    <Router>
      <div className="app-shell govt">
        <NavBar />
        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/routes" element={<RoutePlanner />} />
            <Route path="/map" element={<div className="glass-card p-20">Full Regional Map (Coming Soon)</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
