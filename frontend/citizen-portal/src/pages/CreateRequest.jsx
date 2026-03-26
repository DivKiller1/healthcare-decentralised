import { useState } from "react";
import api, { setToken } from "../api";

export default function CreateRequest() {
  const [form, setForm] = useState({
    category: "blood",
    address: "",
    region: "Dehradun",
    description: ""
  });

  function update(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit() {
    const token = localStorage.getItem("token");
    setToken(token);

    await api.post("http://localhost:8003/request/create", form);
    window.location.href = "/";
  }

  return (
    <div style={{ padding: 40 }}>
      <h2>Create Request</h2>

      <select name="category" onChange={update}>
        <option value="blood">Blood</option>
        <option value="polio">Polio</option>
        <option value="clinic">Clinic</option>
      </select>
      <br /><br />

      <input
        name="address"
        placeholder="Address"
        onChange={update}
      />
      <br /><br />

      <textarea
        name="description"
        placeholder="Description"
        onChange={update}
      />
      <br /><br />

      <button onClick={submit}>Submit Request</button>
    </div>
  );
}
