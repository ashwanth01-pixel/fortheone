import React, { useState } from "react";
import "./Login.css";

function Login() {
  const [accessKey, setAccessKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [region, setRegion] = useState("us-east-1");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setError("");
    if (!accessKey || !secretKey) {
      setError("Access Key and Secret Key are required.");
      return;
    }

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_key: accessKey, secret_key: secretKey, region }),
      });

      const data = await res.json();
      if (data.success) {
        window.location.href = "/";
      } else {
        setError(data.error || "Login failed.");
      }
    } catch (err) {
      setError("Network error: " + err.message);
    }
  };

  return (
    <div className="login-container">
      <h1>Login to AWS</h1>
      <input
        type="text"
        placeholder="AWS Access Key ID"
        value={accessKey}
        onChange={(e) => setAccessKey(e.target.value)}
      />
      <input
        type="password"
        placeholder="AWS Secret Access Key"
        value={secretKey}
        onChange={(e) => setSecretKey(e.target.value)}
      />
      <input
        type="text"
        placeholder="AWS Region (e.g., us-east-1)"
        value={region}
        onChange={(e) => setRegion(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
      {error && <p className="error-msg">{error}</p>}
    </div>
  );
}

export default Login;

