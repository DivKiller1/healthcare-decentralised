export default function StatusCard({ request }) {
  const colors = {
    1: "#dc2626",
    2: "#facc15",
    3: "#2563eb"
  };

  return (
    <div style={{
      padding: 15,
      borderRadius: 8,
      background: "#111827",
      color: "white",
      marginBottom: 10,
      borderLeft: `6px solid ${colors[request.priority] || "#999"}`
    }}>
      <h4>{request.category.toUpperCase()}</h4>
      <p>{request.address}</p>
      <p>Status: {request.assigned_to ? "ASSIGNED" : "OPEN"}</p>
      <p>Priority: {request.priority}</p>
    </div>
  );
}
