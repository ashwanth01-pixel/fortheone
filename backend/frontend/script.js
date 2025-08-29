const header = document.querySelector("header");

// --------------------------
// User info + logout
// --------------------------
const userInfo = document.createElement("div");
userInfo.style.marginLeft = "auto";
userInfo.style.display = "flex";
userInfo.style.alignItems = "center";
userInfo.style.gap = "10px";

const usernameSpan = document.createElement("span");
usernameSpan.style.color = "#a5b4fc";
const logoutBtn = document.createElement("button");
logoutBtn.textContent = "Logout";
logoutBtn.style.background = "#dc2626";
logoutBtn.style.color = "white";
logoutBtn.style.border = "none";
logoutBtn.style.padding = "6px 12px";
logoutBtn.style.borderRadius = "6px";
logoutBtn.style.cursor = "pointer";

logoutBtn.onclick = async function () {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
};

userInfo.appendChild(usernameSpan);
userInfo.appendChild(logoutBtn);
header.appendChild(userInfo);

(async function fetchUser() {
  const res = await fetch("/api/user");
  const data = await res.json();
  if (data.logged_in) {
    usernameSpan.textContent = `Logged in as: ${data.username}`;
  }
})();

const burger = document.getElementById("burger");
const sidebar = document.getElementById("sidebar");
const sendBtn = document.getElementById("send");
const queryInput = document.getElementById("query");
const outputPre = document.getElementById("output");
const confirmationSection = document.getElementById("confirmation-section");
const confirmationText = document.getElementById("confirmation-text");
const acceptBtn = document.getElementById("accept-btn");
const declineBtn = document.getElementById("decline-btn");
const referenceSection = document.getElementById("reference-section");
const referenceBtn = document.getElementById("reference-btn");

let lastQuery = "";
let lastAction = "";
let lastCLICommand = "";
let awsRegion = "us-east-1"; // Default AWS region

// --------------------------
// Sidebar toggle + load history
// --------------------------
burger.onclick = function () {
  if (sidebar.style.display === "block") {
    sidebar.style.display = "none";
  } else {
    sidebar.style.display = "block";
    loadHistory();
  }
};

// --------------------------
// Send button (AshApp) 
// --------------------------
sendBtn.onclick = async function () {
  const query = queryInput.value.trim();
  if (!query) return;

  clearInteraction();

  let res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });

  let data = await res.json();

  lastQuery = data.query || query;
  lastAction = lastQuery.toLowerCase();
  lastCLICommand = data.output || "";

  updateReferenceButton(lastCLICommand || lastAction);

  if (data.confirmation_needed) {
    confirmationText.textContent = getConfirmationMessage(lastAction);
    confirmationSection.classList.remove("hidden");
  } else {
    outputPre.textContent = data.output;
  }

  loadHistory();
};

// --------------------------
// Accept / Decline
// --------------------------
acceptBtn.onclick = async function () {
  confirmationSection.classList.add("hidden");
  outputPre.textContent = "Processing your request...";

  let confirmRes = await fetch("/api/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: lastQuery, decision: "accept" })
  });

  let confirmData = await confirmRes.json();
  outputPre.textContent = confirmData.output;

  lastCLICommand = confirmData.output || lastCLICommand;
  updateReferenceButton(lastCLICommand || lastAction);

  loadHistory();
};

declineBtn.onclick = function () {
  confirmationSection.classList.add("hidden");
  outputPre.textContent = "Action declined.";
};

// --------------------------
// Reference button
// --------------------------
referenceBtn.onclick = function () {
  const url = getReferenceURL(lastCLICommand || lastAction, awsRegion);
  if (url) {
    window.open(url, "_blank");
  } else {
    alert("No reference URL available for this action.");
  }
};

// --------------------------
// Load history
// --------------------------
async function loadHistory() {
  let res = await fetch("/api/history");
  let history = await res.json();
  let list = document.getElementById("history-list");
  list.innerHTML = "";
  history.forEach(item => {
    let timestamp = item.timestamp.split(".")[0].replace("T", " ");
    let li = document.createElement("li");
    li.innerHTML = `<span class="history-time">${timestamp}</span> - <span class="history-query">${item.query}</span>`;
    li.onclick = () => {
      outputPre.textContent = item.output;
      lastQuery = item.query;
      lastAction = item.query.toLowerCase();
      lastCLICommand = item.output;
      updateReferenceButton(lastCLICommand || lastAction);
    };
    list.appendChild(li);
  });
}

// --------------------------
// Auto-refresh every 5 seconds
// --------------------------
setInterval(() => {
  if (sidebar.style.display === "block") {
    loadHistory();
  }
}, 5000);

// --------------------------
// Deployer UI logic
// --------------------------
document.querySelector(".tab[href='/deployer']").onclick = async function (e) {
  e.preventDefault();
  clearInteraction();
  outputPre.textContent = "Opening Deployer UI...";

  // Instead of dumping JSON, actually show deployer.html content
  window.location.href = "/deployer";
};

// Attach handlers when Deployer page is loaded
if (window.location.pathname.startsWith("/deployer")) {
  // Docker login
  document.getElementById("docker-login-btn").onclick = async () => {
    const username = document.getElementById("docker-user").value;
    const password = document.getElementById("docker-token").value;

    const res = await fetch("/deployer-api/docker-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    document.getElementById("docker-login-status").textContent = data.message;

    if (res.ok) {
      document.getElementById("deployer-ui").style.display = "block";
    }
  };

  document.getElementById("logout").onclick = async () => {
    const res = await fetch("/deployer-api/docker-logout", { method: "POST" });
    const data = await res.json();
    alert(data.message);
    location.reload();
  };

  // Validate Flask app
  document.getElementById("validate").onclick = async () => {
    const appName = document.getElementById("app-name").value;
    const code = document.getElementById("code").value;

    const res = await fetch("/deployer-api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_name: appName, code })
    });

    const data = await res.json();
    document.getElementById("valid-status").textContent = data.valid
      ? "✅ Valid"
      : `❌ Invalid: ${data.error}`;

    document.getElementById("deploy").disabled = !data.valid;
  };

  // Deploy to Kubernetes
  document.getElementById("deploy").onclick = async () => {
    const appName = document.getElementById("app-name").value;
    const code = document.getElementById("code").value;
    const kind = document.getElementById("k8s-kind").value;
    const replicas = document.getElementById("replicas").value;
    const serviceType = document.getElementById("service-type").value;
    const namespace = document.getElementById("namespace").value;

    const res = await fetch("/deployer-api/deploy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        app_name: appName,
        code,
        kind,
        replicas,
        service_type: serviceType,
        namespace
      })
    });

    const data = await res.json();
    document.getElementById("result").textContent = JSON.stringify(data, null, 2);

    if (data.manifest) {
      document.getElementById("manifest").textContent = data.manifest;
    }
    if (data.logs) {
      document.getElementById("logs").textContent = data.logs;
    }
  };
}

// --------------------------
// Helpers
// --------------------------
function clearInteraction() {
  outputPre.textContent = "";
  confirmationSection.classList.add("hidden");
}

function getConfirmationMessage(action) {
  if (action.includes("create")) {
    return "This will create AWS resources as requested. Do you want to proceed?";
  } else if (action.includes("delete")) {
    return "This will delete AWS resources as requested. Are you sure to continue?";
  } else if (action.includes("modify") || action.includes("update")) {
    return "This will modify AWS resources. Confirm to proceed.";
  } else {
    return "This action requires confirmation. Proceed?";
  }
}

function updateReferenceButton(action) {
  referenceSection.classList.remove("hidden");
  referenceBtn.onclick = function () {
    const url = getReferenceURL(action, awsRegion);
    if (url) {
      window.open(url, "_blank");
    } else {
      alert("No reference URL available for this action.");
    }
  };
}

function getReferenceURL(actionOrCommand, region = "us-east-1") {
  const awsConsoleBase = "https://console.aws.amazon.com";
  let service = "";

  const match = actionOrCommand.match(/\baws\s+([a-z0-9-]+)/i);
  if (match && match[1]) {
    service = match[1].toLowerCase();
  } else {
    const keywords = ["ec2", "s3", "lambda", "eks", "iam", "rds", "cloudwatch", "vpc", "cloudformation"];
    for (let key of keywords) {
      if (actionOrCommand.includes(key)) {
        service = key;
        break;
      }
    }
  }

  const serviceLinks = {
    ec2: `/ec2/v2/home?region=${region}#Instances:`,
    s3: `/s3/home?region=${region}`,
    lambda: `/lambda/home?region=${region}#/functions`,
    eks: `/eks/home?region=${region}#/clusters`,
    iam: `/iamv2/home?region=${region}#/users`,
    rds: `/rds/home?region=${region}#databases:`,
    cloudwatch: `/cloudwatch/home?region=${region}`,
    vpc: `/vpc/home?region=${region}#vpcs:`,
    cloudformation: `/cloudformation/home?region=${region}#/stacks`
  };

  return serviceLinks[service] ? awsConsoleBase + serviceLinks[service] : null;
}

