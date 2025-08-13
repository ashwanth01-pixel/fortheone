const usernameSpan = document.getElementById("username");
const logoutBtn = document.getElementById("logout");
const appNameEl = document.getElementById("app-name");
const codeEl = document.getElementById("code");
const validateBtn = document.getElementById("validate");
const validStatus = document.getElementById("valid-status");
const deployBtn = document.getElementById("deploy");
const k8sKindEl = document.getElementById("k8s-kind");
const replicasEl = document.getElementById("replicas");
const serviceTypeEl = document.getElementById("service-type");
const containerPortEl = document.getElementById("container-port");
const namespaceEl = document.getElementById("namespace");
const resultPre = document.getElementById("result");
const manifestPre = document.getElementById("manifest");
const logsPre = document.getElementById("logs");

logoutBtn.onclick = async () => {
  await fetch("/api/logout", { method: "POST" });
  location.href = "/login";
};

(async function fetchUser() {
  const res = await fetch("/api/user");
  const data = await res.json();
  if (data.logged_in) {
    usernameSpan.textContent = `Logged in as: ${data.username} (${data.region})`;
  } else {
    location.href = "/login";
  }
})();

validateBtn.onclick = async () => {
  validStatus.textContent = "";
  resultPre.textContent = "";
  manifestPre.textContent = "";
  logsPre.textContent = "";

  const payload = {
    app_name: appNameEl.value || "flaskapp",
    code: codeEl.value || ""
  };

  const res = await fetch("/deployer-api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.success) {
    validStatus.style.color = "#f87171";
    validStatus.textContent = data.error || data.reason || "Invalid";
    deployBtn.disabled = true;
    return;
  }
  if (data.valid) {
    validStatus.style.color = "#34d399";
    validStatus.textContent = `Valid ✓ (app: ${data.app_name})`;
    deployBtn.disabled = false;
  } else {
    validStatus.style.color = "#f87171";
    validStatus.textContent = data.reason || "Invalid";
    deployBtn.disabled = true;
  }
};

deployBtn.onclick = async () => {
  resultPre.textContent = "Deploying… this will build Docker, push to ECR, then kubectl apply.";
  manifestPre.textContent = "";
  logsPre.textContent = "";

  const payload = {
    app_name: appNameEl.value || "flaskapp",
    code: codeEl.value || "",
    k8s_kind: k8sKindEl.value,
    replicas: parseInt(replicasEl.value || "2"),
    service_type: serviceTypeEl.value,
    container_port: parseInt(containerPortEl.value || "8080"),
    namespace: namespaceEl.value || "default"
  };

  const res = await fetch("/deployer-api/deploy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();

  if (!data.success) {
    resultPre.textContent = `❌ ${data.error || "Deployment failed"}`;
    if (data.manifest) manifestPre.textContent = data.manifest;
    if (data.logs) logsPre.textContent = Array.isArray(data.logs) ? data.logs.join("\n---\n") : String(data.logs);
    return;
  }

  resultPre.textContent = `✅ Deployed image: ${data.image}\n${data.service_url_hint || ""}`;
  manifestPre.textContent = data.manifest || "";
  logsPre.textContent = Array.isArray(data.logs) ? data.logs.join("\n---\n") : String(data.logs);
};

