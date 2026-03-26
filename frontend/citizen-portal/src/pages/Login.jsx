import { useState } from "react";

export default function Login() {
  const [mobile, setMobile] = useState("");
  const [error, setError] = useState("");

  async function login() {
    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          mobile_number: mobile
        })
      });

      const data = await res.json();

      if (!data.token) throw new Error("No token");

      localStorage.setItem("token", data.token);
      window.location.href = "/";
    } catch (err) {
      setError("Login failed — Auth service not reachable");
    }
  }

  return (
    <div style={{ padding: 40 }}>
      <h2>Citizen Login</h2>

      <input
        placeholder="Mobile Number"
        value={mobile}
        onChange={(e) => setMobile(e.target.value)}
      />

      <br /><br />

      <button onClick={login}>
        Login
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
