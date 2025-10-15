// ==== GLOBAL DATA ====
let clientsRoles = {};
let clientsStatuses = {};
let deviceStatuses = {};

let clientsData = {}; // Загружается только при открытии вкладки
let devicesData = {}; // Загружается только при открытии вкладки

let currentTab = "users";

// ==== UNIVERSAL FETCH ====
async function apiFetch(url, method="GET", body=null) {
    const res = await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: body ? JSON.stringify(body) : null
    });
    if(!res.ok){
        const err = await res.json().catch(() => ({error: res.statusText}));
        throw new Error(err.error || res.statusText);
    }
    return res.json();
}

// ==== LOAD STATIC DATA ON START ====
async function loadStaticData() {
    clientsRoles = await apiFetch('/api/admin/get_client_roles');
    clientsStatuses = await apiFetch('/api/admin/get_client_statuses');
    deviceStatuses = await apiFetch('/api/admin/get_device_statuses');
}

// ==== TAB SWITCHING ====
function setupTabs() {
    const tabs = document.querySelectorAll(".navbar-link");
    tabs.forEach(tab => {
        tab.addEventListener("click", async () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            if(tab.textContent === "Пользователи") {
                currentTab = "users";
                await loadClients();
            } else {
                currentTab = "devices";
                await loadDevices();
            }
        });
    });
}

// ==== UNIVERSAL SET VALUE ====
function setValue(id, value){
    const el = document.getElementById(id);
    if(el) el.value = value;
}

// ==== LOAD SELECT ====
function loadSelect(id, options, selected="") {
    const el = document.getElementById(id);
    if(!el) return;
    el.innerHTML = "";
    selected = selected.toUpperCase();
    for(const [key,value] of Object.entries(options)){
        const option = document.createElement("option");
        option.value = key;
        option.textContent = value;
        if(key === selected) option.selected = true;
        el.appendChild(option);
    }
}

// ==== MODAL CONTROL ====
function toggleModal(id, show=true){
    const modal = document.getElementById(id);
    const bg = document.getElementById("modalBg");
    if(!modal || !bg) return;
    modal.classList.toggle("show", show);
    const anyOpen = document.querySelectorAll(".modal.show").length > 0;
    bg.classList.toggle("show", anyOpen);
}

function closeAllModals(){
    document.querySelectorAll(".modal").forEach(m => m.classList.remove("show"));
    document.getElementById("modalBg").classList.remove("show");
}

// ==== CLIENTS FUNCTIONS ====
async function loadClients(){
    clientsData = await apiFetch('/api/admin/get_clients');
    const content = document.querySelector(".content");
    content.innerHTML = Object.values(clientsData).map(user => `
        <div class="content-item" data-id="${user.id}">
            <div class="content-item-left">
                <div class="status-indicator ${user.status || "inactive"}"></div>
                <div class="ID">${user.id}</div>
            </div>
            <div class="name">${user.username}</div>
            <div class="tariff">${user.tariff ? user.tariff.name : `НЕСУЩ ТАРИФ ${user.tariff_id}`}</div>
            <div class="role">${user.role}</div>
        </div>
    `).join("");

    document.querySelectorAll(".content-item").forEach(client => {
        client.addEventListener("click", onClientClick);
    });
}

// ==== DEVICES FUNCTIONS ====
async function loadDevices(){
    devicesData = Object.values(await apiFetch('/api/admin/get_devices'));
    const content = document.querySelector(".content");
    content.innerHTML = devicesData.map(device => `
        <div class="content-item" data-id="${device.id}">
            <div class="content-item-left">
                <div class="status-indicator ${device.status || "inactive"}"></div>
                <div class="ID">${device.id}</div>
            </div>
            <div class="name">${device.name}</div>
            <div class="tariff">${device.public_key}</div>
            <div class="ip">${device.ip || "???"}</div>
        </div>
    `).join("");

    document.querySelectorAll(".content-item").forEach(device => {
        device.addEventListener("click", onDeviceClick);
    });
}

// ==== DEVICE MODAL ====
async function onDeviceClick(event) {
    const el = event.currentTarget;
    const ID = el.dataset.id;
    const device = await apiFetch(`/api/admin/get_device/${ID}`);
    
    const modal = document.getElementById("deviceModal");
    modal.dataset.id = ID;

    setValue("deviceName", device.name);
    setValue("devicePublic_key", device.public_key);
    setValue("deviceIP", device.ip);
    loadSelect("deviceStatus", deviceStatuses, device.status);

    toggleModal("deviceModal", true);
}

// ==== CLIENT MODAL ====
function onClientClick(event){
    const ID = event.currentTarget.dataset.id;
    const client = clientsData[ID];
    const modal = document.getElementById("clientModal");
    modal.dataset.id = ID;

    setValue("clientUsername", client.username);
    setValue("clientDesc", client.hidden_description || "");
    loadSelect("clientRole", clientsRoles, client.role);
    loadSelect("clientStatus", clientsStatuses, client.status);
    setValue("clientTariff", client.tariff_id);
    setValue("clientBalance", client.balance);
    setValue("clientNextPayment", new Date(client.next_payment).toISOString().slice(0,10));

    // devices inside client
    const devicesContainer = document.getElementById("clientDevices");
    devicesContainer.innerHTML = "";
    client.devices.forEach(device=>{
        const div = document.createElement("div");
        div.classList.add("clientDevice");
        div.dataset.id = device.id;
        div.addEventListener("click", onDeviceClick);
        div.innerHTML = `
            <div class="clientDevice-left">
                <div class="device-status-indicator ${device.status}"></div>
                <div class="clientDevice-id">${device.id}</div>
            </div>
            <div class="clientDevice-name">${device.name}</div>
            <div class="clientDevice-ip">${device.ip}</div>
        `;
        devicesContainer.appendChild(div);
    });

    toggleModal("clientModal", true);
}

// ==== ADD/EDIT CLIENTS/DEVICES ====
async function addNewClient() {
    const data = {
        username: document.getElementById("newUsername").value.trim(),
        description: document.getElementById("newDesc").value.trim(),
        role: document.getElementById("newRole").value,
        status: document.getElementById("newStatus").value,
        tariff: document.getElementById("newTariff").value || null,
        balance: parseFloat(document.getElementById("newBalance").value) || 0,
        next_payment: document.getElementById("newNextPayment").value
    };
    try{
        await apiFetch('/api/admin/add_client','POST',data);
        toggleModal('addClientModal', false);
        if(currentTab === "users") await loadClients();
    } catch(err){ alert(err.message); console.error(err);}
}

async function editClient() {
    const ID = document.getElementById("clientModal").dataset.id;
    const data = {
        username: document.getElementById("clientUsername").value.trim(),
        description: document.getElementById("clientDesc").value.trim(),
        role: document.getElementById("clientRole").value,
        status: document.getElementById("clientStatus").value,
        tariff_id: document.getElementById("clientTariff").value.trim(),
        balance: parseFloat(document.getElementById("clientBalance").value) || 0,
        next_payment: document.getElementById("clientNextPayment").value
    };
    try{
        await apiFetch(`/api/admin/edit_client/${ID}`, 'POST', data);
        toggleModal("clientModal", false);
        if(currentTab==="users") await loadClients();
    } catch(err){ alert(err.message); console.error(err);}
}

async function deleteClient() {
    const ID = document.getElementById("clientModal").dataset.id;
    try{
        await apiFetch(`/api/admin/delete_client/${ID}`,'DELETE');
        toggleModal("clientModal", false);
        if(currentTab==="users") await loadClients();
    } catch(err){ alert(err.message); console.error(err);}
}

async function addDevice() {
    const data = {
        name: document.getElementById("newName").value.trim() || null,
        user_id: document.getElementById("clientModal").dataset.id
    };
    const DoGenKey = document.getElementById("DoGenKey").checked;
    if(!DoGenKey) data.public_key = document.getElementById("newPublicKey").value;
    try{
        await apiFetch("/api/admin/add_device", 'POST', data);
        closeAllModals();
        if(currentTab==="users") await loadClients();
        else await loadDevices();
    } catch(err){ alert(err.message); console.error(err);}
}

async function editDevice() {
    const modal = document.getElementById("deviceModal");
    const ID = modal.dataset.id;
    const data = {
        name: document.getElementById("deviceName").value.trim(),
        status: document.getElementById("deviceStatus").value,
        public_key: document.getElementById("devicePublic_key").value
    };

    try {
        await apiFetch(`/api/admin/edit_device/${ID}`, 'POST', data);
    } catch (err) {
        alert("Ошибка: " + err.message);
        console.error(err);
    } finally {
        toggleModal("deviceModal", false);
        if(currentTab==="devices") await loadDevices();
        else await loadClients();
    }
}

async function deleteDevice() {
    const modal = document.getElementById("deviceModal");
    const ID = modal.dataset.id;

    try {
        await apiFetch(`/api/admin/delete_device/${ID}`, 'DELETE');
    } catch (err) {
        alert("Ошибка: " + err.message);
        console.error(err);
    } finally {
        toggleModal("deviceModal", false);
        if(currentTab==="devices") await loadDevices();
        else await loadClients();
    }
}

// ==== ADD MODAL SETUP ====
function loadAddModal(){
    loadSelect("newRole", clientsRoles, "regular");
    loadSelect("newStatus", clientsStatuses, "inactive");
    const nextPayment = document.getElementById("newNextPayment");
    const today = new Date();
    today.setDate(today.getDate()+30);
    nextPayment.value = today.toISOString().slice(0,10);
}

// ==== INIT ==== 
document.addEventListener("DOMContentLoaded", async ()=>{
    await loadStaticData();
    setupTabs();
    await loadClients(); // default tab
    loadAddModal();

    // Buttons
    [
        {id:"addClientBtn",event:"click",handler:()=>toggleModal("addClientModal")},
        {id:"addAddClientBtn",event:"click",handler:addNewClient},
        {id:"closeAddClientBtn",event:"click",handler:()=>toggleModal("addClientModal",false)},
        {id:"editEditClientBtn",event:"click",handler:editClient},
        {id:"closeEditClientBtn",event:"click",handler:()=>toggleModal("clientModal",false)},
        {id:"deleteEditClientBtn",event:"click",handler:deleteClient},
        {id:"addAddDeviceBtn",event:"click",handler:addDevice},
        {id:"closeAddDeviceBtn",event:"click",handler:()=>toggleModal("addDeviceModal",false)},
        {id:"editDeviceBtn",event:"click",handler:editDevice},
        {id:"deleteDeviceBtn",event:"click",handler:deleteDevice},
        {id:"closeDeviceBtn",event:"click",handler:()=>toggleModal("deviceModal",false)}
    ].forEach(({id,event,handler})=>{
        const el = document.getElementById(id);
        if(el) el.addEventListener(event,handler);
    });

    // Auto textarea height
    document.querySelectorAll('textarea').forEach(t=>{
        t.addEventListener('input',()=>{
            t.style.height='auto';
            t.style.height=t.scrollHeight+'px';
        });
    });

    // ===== NEW: "+" кнопка для добавления устройства клиенту =====
    const clientDevicesLabel = document.getElementById("clientDevices-label");
    if(clientDevicesLabel){
        // создаем кнопку "+"
        const addBtn = document.createElement("button");
        addBtn.textContent = "+";
        addBtn.style.marginLeft = "8px";
        addBtn.style.padding = "2px 6px";
        addBtn.style.fontSize = "14px";
        addBtn.style.cursor = "pointer";
        addBtn.classList.add("small-btn");

        clientDevicesLabel.appendChild(addBtn);

        addBtn.addEventListener("click", ()=>{
            const clientModal = document.getElementById("clientModal");
            const clientId = clientModal.dataset.id;
            if(!clientId) return alert("Не выбран клиент!");

            // сохраняем id клиента в скрытом поле модалки добавления устройства
            let hiddenInput = document.getElementById("newDeviceUserId");
            if(!hiddenInput){
                hiddenInput = document.createElement("input");
                hiddenInput.type = "hidden";
                hiddenInput.id = "newDeviceUserId";
                document.getElementById("addDeviceModal").appendChild(hiddenInput);
            }
            hiddenInput.value = clientId;

            toggleModal("addDeviceModal", true);
        });
    }
});

