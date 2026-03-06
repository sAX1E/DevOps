// Приложение аукциона — фронтенд

let bidders = [];
let sellers = [];
let lots = [];
let auctions = [];

document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
    setupEventListeners();
    setTodayDate();
    checkUserRole();
});

function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById('auctionDate');
    const analyticsDateEl = document.getElementById('analyticsDate');
    if (dateEl) dateEl.value = today;
    if (analyticsDateEl) analyticsDateEl.value = today;
}

function setupEventListeners() {
    const bidderForm = document.getElementById('bidderForm');
    const sellerForm = document.getElementById('sellerForm');
    const lotForm = document.getElementById('lotForm');
    const auctionForm = document.getElementById('auctionForm');
    if (bidderForm) bidderForm.addEventListener('submit', handleBidderSubmit);
    if (sellerForm) sellerForm.addEventListener('submit', handleSellerSubmit);
    if (lotForm) lotForm.addEventListener('submit', handleLotSubmit);
    if (auctionForm) auctionForm.addEventListener('submit', handleAuctionSubmit);

    const auctionsByDateForm = document.getElementById('auctionsByDateForm');
    const lotsByCategoryForm = document.getElementById('lotsByCategoryForm');
    const lotDetailsForm = document.getElementById('lotDetailsForm');
    if (auctionsByDateForm) auctionsByDateForm.addEventListener('submit', handleAuctionsByDate);
    if (lotsByCategoryForm) lotsByCategoryForm.addEventListener('submit', handleLotsByCategory);
    if (lotDetailsForm) lotDetailsForm.addEventListener('submit', handleLotDetails);
}

async function loadAllData() {
    try {
        const promises = [loadBidders(), loadLots(), loadAuctions()];
        const userRole = document.querySelector('.user-role');
        if (userRole && userRole.textContent === 'Администратор') {
            promises.push(loadSellers());
        }
        await Promise.all(promises);
        updateSelectOptions();
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        if (error.message.includes('401') || error.message.includes('403')) {
            showAlert('Сессия истекла. Войдите снова.', 'danger');
            setTimeout(function() { window.location.href = '/login'; }, 2000);
        } else {
            showAlert('Ошибка загрузки данных', 'danger');
        }
    }
}

async function loadBidders() {
    const response = await fetch('/api/bidders');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    bidders = await response.json();
    displayBidders();
}

async function loadSellers() {
    const response = await fetch('/api/sellers');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    sellers = await response.json();
    displaySellers();
}

async function loadLots() {
    const response = await fetch('/api/lots');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    lots = await response.json();
    displayLots();
}

async function loadAuctions() {
    const response = await fetch('/api/auctions');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    auctions = await response.json();
    displayAuctions();
}

function displayBidders() {
    const container = document.getElementById('biddersList');
    if (!container) return;
    if (bidders.length === 0) {
        container.innerHTML = '<p>Участников пока нет</p>';
        return;
    }
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>Имя</th>
                    <th>Email</th>
                    <th>Телефон</th>
                    <th>Адрес</th>
                </tr>
            </thead>
            <tbody>
                ${bidders.map(function(b) {
                    return '<tr><td>' + b.name + '</td><td>' + b.email + '</td><td>' + (b.phone || '—') + '</td><td class="long-text">' + (b.address || '—') + '</td></tr>';
                }).join('')}
            </tbody>
        </table>
    `;
}

function displaySellers() {
    const container = document.getElementById('sellersList');
    if (!container) return;
    if (sellers.length === 0) {
        container.innerHTML = '<p>Продавцов пока нет</p>';
        return;
    }
    container.innerHTML = `
        <table class="table">
            <thead><tr><th>Продавец</th></tr></thead>
            <tbody>
                ${sellers.map(function(s) { return '<tr><td>' + s.name + '</td></tr>'; }).join('')}
            </tbody>
        </table>
    `;
}

function displayLots() {
    const container = document.getElementById('lotsList');
    if (!container) return;
    if (lots.length === 0) {
        container.innerHTML = '<p>Лотов пока нет</p>';
        return;
    }
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Стартовая цена</th>
                    <th>Описание</th>
                    <th>Категория</th>
                </tr>
            </thead>
            <tbody>
                ${lots.map(function(l) {
                    return '<tr><td><strong>' + l.name + '</strong></td><td>' + l.starting_price + '</td><td class="long-text">' + l.description + '</td><td>' + l.category + '</td></tr>';
                }).join('')}
            </tbody>
        </table>
    `;
}

function displayAuctions() {
    const container = document.getElementById('auctionsList');
    if (!container) return;
    if (auctions.length === 0) {
        container.innerHTML = '<p>Аукционов пока нет</p>';
        return;
    }
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Лот</th>
                    <th>Продавец</th>
                    <th>Место</th>
                    <th>Статус</th>
                    <th>Победитель / Цена</th>
                </tr>
            </thead>
            <tbody>
                ${auctions.map(function(a) {
                    return '<tr><td>' + formatDate(a.date) + '</td><td>' + a.lot_name + '</td><td>' + a.seller_name + '</td><td class="long-text">' + a.location + '</td><td>' + a.status + '</td><td>' + (a.winner_name || '—') + ' / ' + (a.final_price || '—') + '</td></tr>';
                }).join('')}
            </tbody>
        </table>
    `;
}

function updateSelectOptions() {
    const auctionLot = document.getElementById('auctionLot');
    const auctionSeller = document.getElementById('auctionSeller');
    const auctionWinner = document.getElementById('auctionWinner');
    const analyticsLot = document.getElementById('analyticsLot');

    if (auctionLot) {
        auctionLot.innerHTML = '<option value="">Выберите лот</option>' + lots.map(function(l) { return '<option value="' + l.id + '">' + l.name + '</option>'; }).join('');
    }
    if (auctionSeller) {
        auctionSeller.innerHTML = '<option value="">Выберите продавца</option>' + sellers.map(function(s) { return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');
    }
    if (auctionWinner) {
        auctionWinner.innerHTML = '<option value="">—</option>' + bidders.map(function(b) { return '<option value="' + b.id + '">' + b.name + '</option>'; }).join('');
    }
    if (analyticsLot) {
        analyticsLot.innerHTML = '<option value="">Выберите лот</option>' + lots.map(function(l) { return '<option value="' + l.id + '">' + l.name + '</option>'; }).join('');
    }
}

async function handleBidderSubmit(e) {
    e.preventDefault();
    var formData = {
        name: document.getElementById('bidderName').value,
        email: document.getElementById('bidderEmail').value,
        phone: document.getElementById('bidderPhone').value || null,
        address: document.getElementById('bidderAddress').value || null
    };
    try {
        var response = await fetch('/api/bidders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (response.ok) {
            showAlert('Участник добавлен', 'success');
            document.getElementById('bidderForm').reset();
            loadBidders();
            updateSelectOptions();
        } else throw new Error();
    } catch (err) {
        showAlert('Ошибка добавления участника', 'danger');
    }
}

async function handleSellerSubmit(e) {
    e.preventDefault();
    var formData = { name: document.getElementById('sellerName').value };
    try {
        var response = await fetch('/api/sellers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (response.ok) {
            showAlert('Продавец добавлен', 'success');
            document.getElementById('sellerForm').reset();
            loadSellers();
            updateSelectOptions();
        } else throw new Error();
    } catch (err) {
        showAlert('Ошибка добавления продавца', 'danger');
    }
}

async function handleLotSubmit(e) {
    e.preventDefault();
    var formData = {
        name: document.getElementById('lotName').value,
        starting_price: document.getElementById('lotPrice').value,
        description: document.getElementById('lotDescription').value,
        category: document.getElementById('lotCategory').value
    };
    try {
        var response = await fetch('/api/lots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (response.ok) {
            showAlert('Лот добавлен', 'success');
            document.getElementById('lotForm').reset();
            loadLots();
            updateSelectOptions();
        } else throw new Error();
    } catch (err) {
        showAlert('Ошибка добавления лота', 'danger');
    }
}

async function handleAuctionSubmit(e) {
    e.preventDefault();
    var winnerId = document.getElementById('auctionWinner').value;
    var formData = {
        date: document.getElementById('auctionDate').value,
        location: document.getElementById('auctionLocation').value,
        lot_id: parseInt(document.getElementById('auctionLot').value, 10),
        seller_id: parseInt(document.getElementById('auctionSeller').value, 10),
        notes: document.getElementById('auctionNotes').value,
        status: document.getElementById('auctionStatus').value,
        final_price: document.getElementById('auctionFinalPrice').value || null,
        winner_bidder_id: winnerId ? parseInt(winnerId, 10) : null,
        bids: []
    };
    try {
        var response = await fetch('/api/auctions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (response.ok) {
            showAlert('Аукцион создан', 'success');
            document.getElementById('auctionForm').reset();
            setTodayDate();
            loadAuctions();
        } else throw new Error();
    } catch (err) {
        showAlert('Ошибка создания аукциона', 'danger');
    }
}

async function handleAuctionsByDate(e) {
    e.preventDefault();
    var date = document.getElementById('analyticsDate').value;
    try {
        var response = await fetch('/api/auctions/count-by-date', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: date })
        });
        var result = await response.json();
        document.getElementById('auctionsCount').textContent = result.count;
        document.getElementById('auctionsByDateResult').style.display = 'block';
    } catch (err) {
        showAlert('Ошибка запроса', 'danger');
    }
}

async function handleLotsByCategory(e) {
    e.preventDefault();
    var category = document.getElementById('analyticsCategory').value;
    try {
        var response = await fetch('/api/lots/count-by-category', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: category })
        });
        var result = await response.json();
        document.getElementById('lotsCount').textContent = result.count;
        document.getElementById('lotsByCategoryResult').style.display = 'block';
    } catch (err) {
        showAlert('Ошибка запроса', 'danger');
    }
}

async function handleLotDetails(e) {
    e.preventDefault();
    var lotId = document.getElementById('analyticsLot').value;
    try {
        var response = await fetch('/api/lots/' + lotId + '/details');
        var result = await response.json();
        document.getElementById('lotNameResult').textContent = result.name + ' (' + result.category + ')';
        document.getElementById('lotDetailsText').textContent = result.description;
        document.getElementById('lotDetailsResult').style.display = 'block';
    } catch (err) {
        showAlert('Ошибка запроса', 'danger');
    }
}

function checkUserRole() {
    var userInfo = document.querySelector('.user-info');
    if (!userInfo) {
        window.location.href = '/login';
        return;
    }
    var userRole = document.querySelector('.user-role');
    if (userRole && userRole.textContent === 'Продавец') {
        var sellersTab = document.querySelector('button[onclick="showTab(\'sellers\')"]');
        if (sellersTab) sellersTab.style.display = 'none';
    }
}

function showTab(tabName) {
    var userRole = document.querySelector('.user-role');
    if (userRole && userRole.textContent === 'Продавец' && tabName === 'sellers') {
        showAlert('Нет доступа к управлению продавцами', 'danger');
        return;
    }
    var tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(function(t) { t.classList.remove('active'); });
    var buttons = document.querySelectorAll('.nav-tab');
    buttons.forEach(function(b) { b.classList.remove('active'); });
    var target = document.getElementById(tabName);
    if (target) target.classList.add('active');
    if (event && event.target) event.target.classList.add('active');
    if (tabName === 'analytics') {
        loadLots();
        loadStatistics();
        loadPopularCategories();
        loadPopularLots();
        updateSelectOptions();
    }
}

function showAlert(message, type) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type;
    alertDiv.textContent = message;
    var container = document.querySelector('.container');
    if (container) container.insertBefore(alertDiv, container.firstChild);
    setTimeout(function() { alertDiv.remove(); }, 5000);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('ru-RU');
}

async function loadStatistics() {
    var container = document.getElementById('statistics');
    if (!container) return;
    try {
        var response = await fetch('/api/statistics');
        var stats = await response.json();
        container.innerHTML = ''
            + '<div class="result-box"><div class="result-number">' + stats.total_bidders + '</div><div class="result-text">участников</div></div>'
            + '<div class="result-box"><div class="result-number">' + stats.total_sellers + '</div><div class="result-text">продавцов</div></div>'
            + '<div class="result-box"><div class="result-number">' + stats.total_lots + '</div><div class="result-text">лотов</div></div>'
            + '<div class="result-box"><div class="result-number">' + stats.total_auctions + '</div><div class="result-text">аукционов</div></div>'
            + '<div class="result-box"><div class="result-number">' + stats.auctions_today + '</div><div class="result-text">аукционов сегодня</div></div>';
    } catch (err) {
        container.innerHTML = '<p>Ошибка загрузки статистики</p>';
    }
}

async function loadPopularCategories() {
    var container = document.getElementById('popularCategories');
    if (!container) return;
    try {
        var response = await fetch('/api/popular-categories');
        var data = await response.json();
        if (data.length === 0) {
            container.innerHTML = '<p>Нет данных</p>';
            return;
        }
        container.innerHTML = '<table class="table"><thead><tr><th>Категория</th><th>Кол-во</th></tr></thead><tbody>'
            + data.map(function(d) { return '<tr><td>' + d.category + '</td><td><strong>' + d.count + '</strong></td></tr>'; }).join('')
            + '</tbody></table>';
    } catch (err) {
        container.innerHTML = '<p>Ошибка загрузки</p>';
    }
}

async function loadPopularLots() {
    var container = document.getElementById('popularLots');
    if (!container) return;
    try {
        var response = await fetch('/api/popular-lots');
        var data = await response.json();
        if (data.length === 0) {
            container.innerHTML = '<p>Нет данных</p>';
            return;
        }
        container.innerHTML = '<table class="table"><thead><tr><th>Лот</th><th>Аукционов</th></tr></thead><tbody>'
            + data.map(function(m) { return '<tr><td>' + m.lot + '</td><td><strong>' + m.count + '</strong></td></tr>'; }).join('')
            + '</tbody></table>';
    } catch (err) {
        container.innerHTML = '<p>Ошибка загрузки</p>';
    }
}
