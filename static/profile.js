async function getProfile() {
    const response = await fetch('/api/profile')
 	const data = await response.json();
//	const data = {
//    "balance": 0,
//    "children": [],
//    "created_at": "Sat, 20 Sep 2025 22:39:16 GMT",
//    "devices": [
//        {
//            "created_at": "Sat, 20 Sep 2025 22:39:16 GMT",
//            "id": 1,
//            "ip": "10.88.88.2",
//            "name": "\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e",
//            "public_key": "4kGdoJH5uumlSHda0y/rEHwS05JsSUcQ9BXkRcqrdWI=",
//            "status": "active",
//            "user_id": 1
//        },
//		        {
//            "created_at": "Sat, 20 Sep 2025 22:39:16 GMT",
//            "id": 1,
//            "ip": "10.88.88.3",
//            "name": "\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e",
//            "public_key": "4kGdoJH5uumlSHda0y/rEHwS05JsSUcQ9BXkRcqrdWI=",
//            "status": "inactive",
//            "user_id": 1
//        },
//		        {
//            "created_at": "Sat, 20 Sep 2025 22:39:16 GMT",
//            "id": 1,
//            "ip": "10.88.88.4",
//            "name": "\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e",
//            "public_key": "4kGdoJH5uumlSHda0y/rEHwS05JsSUcQ9BXkRcqrdWI=",
//            "status": "active",
//            "user_id": 1
//        }
//    ],
//    "extra_devices": 5,
//    "extra_speed": 0,
//    "extra_users": 5,
//    "id": 1,
//    "ip": "10.88.88.2",
//    "next_payment": "Sat, 20 Sep 2025 22:39:16 GMT",
//    "parent": null,
//    "parent_id": null,
//    "role": "regular",
//    "status": "active",
//    "tariff": {
//        "description": "\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439 \u0442\u0430\u0440\u0438\u0444",
//        "devices_count": 1,
//        "id": 1,
//        "name": "\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439",
//        "payment": 0,
//        "show": false,
//        "speed": 20,
//        "users_count": 1
//    },
//    "tariff_id": 1,
//    "username": "Vlad"
//}
	return data
}

// helper: название месяца буквами
function formatDateToRussian(dateStr) {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    const options = { day: "numeric", month: "long" }; // "13 октября"
    return date.toLocaleDateString("ru-RU", options).replace(" ","\u00A0");
}

// helper: создать элемент карусели
function createCarouselItem(content) {
    const item = document.createElement("div");
    item.classList.add("carousel__item");
    item.innerHTML = content;
    return item;
}

// helper: создать элемент с прогрессбаром
function createProgressItem(label, value, max) {
	
    const percent = Math.min(100, (value / max) * 100);
	
	const color = value > max ? "background-color: #e74c3c" : "";
    return createCarouselItem(`
        <span>${label}: ${value}/${max}</span>
        <div class="progress">
            <div class="progress__bar" style="width: ${percent}%; ${color}"></div>
        </div>
    `);
}

// строим профиль
async function buildProfile() {
	
	const data = await getProfile
();
    // Навбар
    document.querySelector(".user-ip").textContent = data.ip;
    document.querySelector(".user-name").textContent = data.username;

    // Баланс
    document.querySelector(".balance__amount").textContent = `${data.balance} р.`;
    document.querySelector(".balance__next").textContent =
        "Следующее списание:\u00A0" + formatDateToRussian(data.next_payment);

    // Тариф
    const tariffHeader = document.querySelector(".tariff-card .card__header");
    tariffHeader.textContent = `Тариф: "${data.tariff.name}"`;

    const tariffTrack = document.querySelector(".tariff-card .carousel__track");
    tariffTrack.innerHTML = ""; // очистить

    tariffTrack.appendChild(createCarouselItem(`Скорость: ${data.tariff.speed}\u00A0Мбит/с`));
    tariffTrack.appendChild(
        createProgressItem("Устройства", data.devices.length, data.tariff.devices_count + data.extra_devices)
    );
    tariffTrack.appendChild(
        createProgressItem("Места", 1 + data.extra_users, data.tariff.users_count + data.extra_users)
    );

    // Устройства
	
	const devicesOption = document.getElementById("devices-option");
	if	(data.devices.length < data.tariff.devices_count + data.extra_devices) {
		devicesOption.classList.remove("hidden");
	}
    const devicesTrack = document.getElementById("devices-track");
    devicesTrack.innerHTML = ""; // очистить

    data.devices.forEach(dev => {
        devicesTrack.appendChild(createCarouselItem(`<div class="device__item" onclick="openDeviceModal('${dev.ip}')">
            <span class="device__ip">${dev.ip}</span>
			<span class="device__name">${dev.name}</span>
            <span class="device__status status-${dev.status}">${dev.status === "active" ? 'Активно' : 'Неактивно'}</span></div>
        `));
    });
}

window.onload = buildProfile;

function openModal(id){
	const modal = document.getElementById(id);
	if (!modal) return;
	modal.classList.add("show");
	openModalBG();
}

function closeModal(id){
	const modal = document.getElementById(id);
	if (!modal) return;
	modal.classList.remove("show");
	closeModalBG();
}

function openModalBG(){
	const BG = document.getElementById("modal-bg");
	if (!BG) return;
	BG.classList.add("show");
}

function closeModalBG(){
	const BG = document.getElementById("modal-bg");
	const activeModals = document.querySelectorAll('.modal-content.show').length;
	if (activeModals === 0){
		BG.classList.remove("show");
	}
}

async function copyOnClick(el){
	try {
		await navigator.clipboard.writeText(el.value);
		console.log('Текст скопирован в буфер обмена');
	} catch (err) {
		console.error('Ошибка при копировании:', err);
	}
}

async function openDeviceModal(targetip){
	openModal("editDeviceModal");
	
	const name = document.getElementById("deviceEditName");
	const ip = document.getElementById('ipEdit');
	const publickey = document.getElementById("publickeyEdit");
	const status = document.getElementById("statusEdit");
	
	try {
		const resp = await fetch("/api/getDevice", {
			method:  'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ip: targetip})
		});
		if (!resp.ok){
			const text = await resp.json();
			let errMsg = text.error || JSON.stringify(text);
			
			throw new Error(`HTTP ${resp.status}: ${errMsg}`);
		}
		
		const data = await resp.json();
		name.value = data.name;
		ip.value = data.ip;
		publickey.value  = data.public_key;
		status.checked = data.status === "active";
	} catch (err) {
		console.error(err);
		name.value = 'Что-то пошло не так';
		ip.value = "Что-то пошло не так";
		publickey.value = 'Что-то пошло не так';
		status.checked = false;
	}
	
}


async function addDevice(){
	
	closeModal('addDeviceModal'); 
	openModal('keysModal');
	
	const name = document.getElementById("deviceName").value.trim();
	const privEl = document.getElementById('privateKey');
	const pubEl = document.getElementById('publicKey');
	try {
		const resp = await fetch('/api/addDevice', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({name: name})
		});
		
		if (!resp.ok) {
			const text = await resp.json();
			let errMsg = text.error || JSON.stringify(text);
			
			throw new Error(`HTTP ${resp.status}: ${errMsg}`);
		}
		
		const data = await resp.json();
		privEl.value = data.private_key;
		pubEl.value = data.public_key;
		
	} catch (err) {
		console.error(err);
		privEl.value = 'Что-то пошло не так';
		pubEl.value = 'Что-то пошло не так';
		alert('Ошибка при создании устройства: '+ (err.message || err));
	}
	
}

async function deleteDevice() {
	const ip = document.getElementById("ipEdit").value;
	try {
		const resp = await fetch('api/deleteDevice', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ip: ip})
		});
		
		if (!resp.ok) {
			const text = await resp.json();
			let errMsg = text.error || JSON.stringify(text);
			
			throw new Error(`HTTP ${resp.status}: ${errMsg}`);
		}
		
		const data = await resp.json();
		console.log(data);
	} catch (err) {
		console.log(err);
	}
	location.href = location.href;
}

async function editDevice() {
	const ip = document.getElementById("ipEdit").value;
	const name = document.getElementById("deviceEditName").value;
	const status = document.getElementById("statusEdit").checked;
	try {
		const resp = await fetch('api/editDevice', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ip: ip, name: name, status: status})
		});
		
		if (!resp.ok) {
			const text = await resp.json();
			let errMsg = text.error || JSON.stringify(text);
			
			throw new Error(`HTTP ${resp.status}: ${errMsg}`);
		}
		
		const data = await resp.json();
		console.log(data);
	} catch (err) {
		console.log(err);
	}
	location.href = location.href;
}