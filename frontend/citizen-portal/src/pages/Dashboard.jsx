import { useEffect, useState } from "react";
import api, { setToken } from "../api";
import StatusCard from "../components/StatusCard";

export default function Dashboard() {
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setToken(token);

    api.get("http://localhost:8003/request/open")
      .then(res => setRequests(res.data));
  }, []);

  return (
    <div style={{ padding: 30 }}>
      <h2>My Requests</h2>
      <button onClick={() => window.location.href = "/create"}>
        Create New Request
      </button>

      <div style={{ marginTop: 20 }}>
        {requests.map(r => (
          <StatusCard key={r.id} request={r} />
        ))}
      </div>
    </div>
  );
}
