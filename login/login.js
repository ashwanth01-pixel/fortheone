document.getElementById("login-btn").onclick = async function () {
    const accessKey = document.getElementById("access_key").value.trim();
    const secretKey = document.getElementById("secret_key").value.trim();
    const region = document.getElementById("region").value.trim();

    const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_key: accessKey, secret_key: secretKey, region })
    });

    const data = await res.json();
    if (data.success) {
        window.location.href = "/";
    } else {
        document.getElementById("error-msg").textContent = data.error || "Login failed.";
    }
};

