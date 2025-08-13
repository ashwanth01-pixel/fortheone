const header = document.querySelector("header");

// User info + logout
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

burger.onclick = function () {
    if (sidebar.style.display === "block") {
        sidebar.style.display = "none";
    } else {
        sidebar.style.display = "block";
        loadHistory();
    }
};

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
};

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
};

declineBtn.onclick = function () {
    confirmationSection.classList.add("hidden");
    outputPre.textContent = "Action declined.";
};

referenceBtn.onclick = function () {
    const url = getReferenceURL(lastCLICommand || lastAction, awsRegion);
    if (url) {
        window.open(url, "_blank");
    } else {
        alert("No reference URL available for this action.");
    }
};

async function loadHistory() {
    let res = await fetch("/api/history");
    let history = await res.json();
    let list = document.getElementById("history-list");
    list.innerHTML = "";
    history.forEach(item => {
        let li = document.createElement("li");
        li.innerHTML = `<span class="history-time">${item.timestamp}</span> - <span class="history-query">${item.query}</span>`;
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

