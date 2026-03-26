
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { BarChart3, ShieldAlert, Cpu, Database, UserCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import '../shared/theme.css';
import './App.css';

const Metrics = () => {
  const data = [
    { name: 'Compute', value: 400, color: 'var(--primary)' },
    { name: 'Storage', value: 300, color: 'var(--secondary)' },
    { name: 'Network', value: 200, color: 'var(--accent)' },
    { name: 'AI/ML', value: 150, color: 'var(--success)' },
  ];

  return (
    <div className="metrics-page">
      <div className="section-header">
        <h1>Cloud <span>Intel</span></h1>
        <p>Real-time cross-cloud resource monitoring and operational savings.</p>
      </div>
      <div className="metrics-grid">
        <div className="glass-card stat-detail">
          <h3>Cost Distribution</h3>
          <div style={{ height: 300 }}>
             <ResponsiveContainer width="100%" height="100%">
               <BarChart data={data}>
                  <XAxis dataKey="name" stroke="var(--text-muted)" />
                  <YAxis stroke="var(--text-muted)" />
                  <Tooltip cursor={{fill: 'var(--surface)'}} contentStyle={{background: 'var(--surface)', border: '1px solid var(--glass-border)'}} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {data.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Bar>
               </BarChart>
             </ResponsiveContainer>
          </div>
        </div>
        <div className="glass-card savings-highlight">
           <Cpu size={48} color="var(--accent)" />
           <h2>$12,450</h2>
           <span>Projected Monthly Savings</span>
           <p>Optimized via TSP routing and cluster-based resource allocation.</p>
        </div>
      </div>
    </div>
  );
};

const Verification = () => {
  const pending = [
    { id: 1, name: 'Himalayan Clinic', type: 'Clinic', region: 'Dehradun', date: '2026-03-24' },
    { id: 2, name: 'Doon Blood Bank', type: 'Blood Bank', region: 'Dehradun', date: '2026-03-23' },
  ];

  return (
    <div className="page-container">
      <div className="section-header">
        <h1>Verification <span>Queue</span></h1>
        <p>Review and verify healthcare facilities before they go live on the public portal.</p>
      </div>
      <div className="table-container glass-card">
         <table className="admin-table">
           <thead>
             <tr>
               <th>Facility Name</th>
               <th>Type</th>
               <th>Region</th>
               <th>Actions</th>
             </tr>
           </thead>
           <tbody>
             {pending.map(f => (
               <tr key={f.id}>
                 <td>{f.name}</td>
                 <td>{f.type}</td>
                 <td>{f.region}</td>
                 <td className="actions">
                    <button className="btn-approve">Approve</button>
                    <button className="btn-reject">Reject</button>
                 </td>
               </tr>
             ))}
           </tbody>
         </table>
      </div>
    </div>
  );
};

const NavBar = () => (
  <nav className="nav-sidebar glass-card">
    <div className="nav-brand">
      <ShieldAlert size={28} color="var(--primary)" />
      <span>AdminPanel</span>
    </div>
    <div className="nav-menu">
      <Link to="/"><BarChart3 size={20} /> Metrics</Link>
      <Link to="/verify"><UserCheck size={20} /> Verifications</Link>
      <Link to="/audit"><Database size={20} /> Audit Logs</Link>
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
            <Route path="/" element={<Metrics />} />
            <Route path="/verify" element={<Verification />} />
            <Route path="/audit" element={<div className="glass-card p-20">Audit Log Viewer (Coming Soon)</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
