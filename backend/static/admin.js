// frontend/js/admin.js
document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:5001/api';

    // 维修项目相关 DOM
    const repairItemsTableBody = document.querySelector('#repair-items-table tbody');
    const addItemBtn = document.getElementById('add-item-btn');
    const itemModal = document.getElementById('item-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const itemForm = document.getElementById('item-form');
    const modalTitle = document.getElementById('modal-title');
    const editItemIdInput = document.getElementById('edit-item-id');
    const itemNameInput = document.getElementById('item-name');
    const itemPriceInput = document.getElementById('item-price');
    const itemUnitInput = document.getElementById('item-unit');
    const itemSchoolSelect = document.getElementById('item-school');

    // 学校信息相关 DOM
    const schoolsTableBody = document.querySelector('#schools-table tbody');

    // 计价单相关 DOM
    const quotationsTableBody = document.querySelector('#quotations-table tbody');
    const exportBatchExcelBtn = document.getElementById('export-batch-excel-btn');

    let allSchools = []; // 存储所有学校信息，用于下拉选择

    /**
     * 加载所有学校信息 (用于项目表单和学校列表)
     */
    async function fetchAllSchools() {
        try {
            const response = await fetch(`${API_BASE_URL}/schools`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allSchools = await response.json();
            populateSchoolSelect(allSchools);
            renderSchoolsTable(allSchools);
        } catch (error) {
            console.error("获取学校列表失败:", error);
            alert("获取学校列表失败。");
        }
    }

    /**
     * 填充学校选择下拉框 (用于新增/编辑项目)
     * @param {Array} schools 学校列表数据
     */
    function populateSchoolSelect(schools) {
        itemSchoolSelect.innerHTML = '<option value="">请选择学校</option>'; // 清空并添加默认选项
        schools.forEach(school => {
            const option = document.createElement('option');
            option.value = school.id;
            option.textContent = school.name;
            itemSchoolSelect.appendChild(option);
        });
    }

    /**
     * 渲染学校信息到表格
     * @param {Array} schools 学校列表数据
     */
    function renderSchoolsTable(schools) {
        schoolsTableBody.innerHTML = '';
        if (schools.length === 0) {
            schoolsTableBody.innerHTML = '<tr><td colspan="3">暂无学校信息</td></tr>';
            return;
        }
        schools.forEach(school => {
            const row = schoolsTableBody.insertRow();
            row.innerHTML = `
                <td>${school.id}</td>
                <td>${school.name}</td>
                <td>
                    <button class="button edit-school-btn">编辑</button>
                    <button class="button delete-school-btn">删除</button>
                </td>
            `;
        });
    }

    /**
     * 加载所有维修项目
     */
    async function fetchAllRepairItems() {
        try {
            repairItemsTableBody.innerHTML = '<tr><td colspan="6">加载中...</td></tr>';
            const response = await fetch(`${API_BASE_URL}/items`); // 后台获取所有项目API
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const items = await response.json();
            renderRepairItemsTable(items);
        } catch (error) {
            console.error("获取维修项目列表失败:", error);
            repairItemsTableBody.innerHTML = '<tr><td colspan="6">加载维修项目失败</td></tr>';
        }
    }

    /**
     * 渲染维修项目到表格
     * @param {Array} items 项目列表数据
     */
    function renderRepairItemsTable(items) {
        repairItemsTableBody.innerHTML = '';
        if (items.length === 0) {
            repairItemsTableBody.innerHTML = '<tr><td colspan="6">暂无维修项目</td></tr>';
            return;
        }
        items.forEach(item => {
            const row = repairItemsTableBody.insertRow();
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.name}</td>
                <td>${item.price.toFixed(2)}</td>
                <td>${item.unit}</td>
                <td>${item.school_name || '未知学校'} (ID: ${item.school_id})</td>
                <td class="actions">
                    <button class="button edit-btn item-edit-btn" data-id="${item.id}">编辑</button>
                    <button class="button delete-btn item-delete-btn" data-id="${item.id}">删除</button>
                </td>
            `;
        });
    }

    /**
     * 打开新增/编辑项目模态框
     * @param {Object|null} itemToEdit 如果是编辑，则传入项目对象，否则为null
     */
    function openItemModal(itemToEdit = null) {
        itemForm.reset(); // 重置表单
        populateSchoolSelect(allSchools); // 确保学校列表最新
        if (itemToEdit) {
            modalTitle.textContent = '编辑维修项目';
            editItemIdInput.value = itemToEdit.id;
            itemNameInput.value = itemToEdit.name;
            itemPriceInput.value = itemToEdit.price;
            itemUnitInput.value = itemToEdit.unit;
            itemSchoolSelect.value = itemToEdit.school_id;
        } else {
            modalTitle.textContent = '新增维修项目';
            editItemIdInput.value = ''; // 清空ID，表示新增
        }
        itemModal.style.display = 'block';
    }

    /**
     * 关闭模态框
     */
    function closeItemModal() {
        itemModal.style.display = 'none';
    }

    /**
     * 处理项目表单提交 (新增或编辑)
     * @param {Event} event
     */
    async function handleItemFormSubmit(event) {
        event.preventDefault();
        const itemId = editItemIdInput.value;
        const schoolId = parseInt(itemSchoolSelect.value);

        if (!schoolId) {
            alert('请选择所属学校！');
            return;
        }

        const itemData = {
            name: itemNameInput.value.trim(),
            price: parseFloat(itemPriceInput.value),
            unit: itemUnitInput.value.trim(),
            school_id: schoolId
        };

        if (!itemData.name || isNaN(itemData.price) || !itemData.unit) {
            alert('请填写所有必填项！');
            return;
        }

        const url = itemId ? `${API_BASE_URL}/items/${itemId}` : `${API_BASE_URL}/items`;
        const method = itemId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(itemData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            alert(`项目已${itemId ? '更新' : '添加'}！`);
            closeItemModal();
            fetchAllRepairItems(); // 刷新列表
        } catch (error) {
            console.error("保存项目失败:", error);
            alert(`保存项目失败: ${error.message}`);
        }
    }

    /**
     * 处理删除项目
     * @param {number} itemId 项目ID
     */
    async function handleDeleteItem(itemId) {
        if (!confirm('确定要删除这个维修项目吗？此操作不可恢复。')) {
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            alert('项目已删除！');
            fetchAllRepairItems(); // 刷新列表
        } catch (error) {
            console.error("删除项目失败:", error);
            alert(`删除项目失败: ${error.message}`);
        }
    }

    /**
     * 加载所有计价单
     */
    async function fetchAllQuotations() {
        try {
            quotationsTableBody.innerHTML = '<tr><td colspan="6">加载中...</td></tr>';
            const response = await fetch(`${API_BASE_URL}/quotations`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const quotations = await response.json();
            renderQuotationsTable(quotations);
        } catch (error) {
            console.error("获取计价单列表失败:", error);
            quotationsTableBody.innerHTML = '<tr><td colspan="6">加载计价单失败</td></tr>';
        }
    }

    /**
     * 渲染计价单到表格
     * @param {Array} quotations 计价单列表数据
     */
    function renderQuotationsTable(quotations) {
        quotationsTableBody.innerHTML = '';
        if (quotations.length === 0) {
            quotationsTableBody.innerHTML = '<tr><td colspan="6">暂无计价单</td></tr>';
            return;
        }
        quotations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); // 按创建时间降序

        quotations.forEach(q => {
            const row = quotationsTableBody.insertRow();
            const createdDate = new Date(q.created_at).toLocaleDateString('zh-CN') + ' ' + new Date(q.created_at).toLocaleTimeString('zh-CN');
            row.innerHTML = `
                <td>${q.id}</td>
                <td>${q.quotation_number}</td>
                <td>${q.school_name}</td>
                <td>${q.total_price.toFixed(2)}</td>
                <td>${createdDate}</td>
                <td class="actions">
                    <a href="${API_BASE_URL}/quotations/${q.id}/image" target="_blank" class="button">查看图片</a>
                    <a href="${API_BASE_URL}/quotations/${q.id}/excel" target="_blank" class="button">导出Excel</a>
                    <button class="button delete-quotation-btn" data-id="${q.id}">删除</button>
                </td>
            `;
        });
    }

    // --- 事件监听 ---
    addItemBtn.addEventListener('click', () => openItemModal());
    closeModalBtn.addEventListener('click', closeItemModal);
    window.addEventListener('click', (event) => {
        if (event.target == itemModal) {
            closeItemModal();
        }
    });
    itemForm.addEventListener('submit', handleItemFormSubmit);

    repairItemsTableBody.addEventListener('click', async (event) => {
        const target = event.target;
        if (target.classList.contains('item-edit-btn')) {
            const itemId = parseInt(target.dataset.id);
            // 需要先获取单个项目的详细信息，因为列表可能不包含所有学校ID
            try {
                const res = await fetch(`${API_BASE_URL}/items`); // 获取所有项目，然后筛选
                if (!res.ok) throw new Error('Failed to fetch item details for editing');
                const allItems = await res.json();
                const itemToEdit = allItems.find(item => item.id === itemId);
                if (itemToEdit) {
                    openItemModal(itemToEdit);
                } else {
                    alert('未找到要编辑的项目信息。');
                }
            } catch (err) {
                alert('加载编辑信息失败: ' + err.message);
            }
        } else if (target.classList.contains('item-delete-btn')) {
            const itemId = parseInt(target.dataset.id);
            handleDeleteItem(itemId);
        }
    });

    // 批量导出Excel事件监听
    document.getElementById('export-batch-excel-btn').addEventListener('click', async () => {
        const schoolId = document.getElementById('export-school').value;
        const start = document.getElementById('export-start').value;
        const end = document.getElementById('export-end').value;
        let params = [];
        if (schoolId) params.push(`school_id=${encodeURIComponent(schoolId)}`);
        if (start) params.push(`start=${encodeURIComponent(start)}`);
        if (end) params.push(`end=${encodeURIComponent(end)}`);
        let url = `${API_BASE_URL}/quotations/export_batch_excel`;
        if (params.length > 0) url += '?' + params.join('&');
        try {
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 404) {
                    alert("没有计价单可以导出。");
                    return;
                }
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            // 触发浏览器下载
            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let filename = '批量导出计价单.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
            const urlBlob = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = urlBlob;
            a.download = decodeURIComponent(filename); // 解码文件名
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(urlBlob);
            document.body.removeChild(a);
            alert('批量导出Excel文件已开始下载。');
        } catch (error) {
            console.error("批量导出Excel失败:", error);
            alert(`批量导出Excel失败: ${error.message}`);
        }
    });

    // 初始化学校下拉框（导出用）
    async function initExportSchoolSelect() {
        const select = document.getElementById('export-school');
        select.innerHTML = '<option value="">全部</option>';
        try {
            const response = await fetch(`${API_BASE_URL}/schools`);
            if (!response.ok) return;
            const schools = await response.json();
            schools.forEach(school => {
                const option = document.createElement('option');
                option.value = school.id;
                option.textContent = school.name;
                select.appendChild(option);
            });
        } catch (e) {}
    }

    // --- 计价单条件查询 ---
    async function initFilterSchoolSelect() {
        const select = document.getElementById('filter-school');
        select.innerHTML = '<option value="">全部</option>';
        try {
            const response = await fetch(`${API_BASE_URL}/schools`);
            if (!response.ok) return;
            const schools = await response.json();
            schools.forEach(school => {
                const option = document.createElement('option');
                option.value = school.id;
                option.textContent = school.name;
                select.appendChild(option);
            });
        } catch (e) {}
    }
    document.getElementById('filter-quotation-btn').addEventListener('click', async () => {
        const schoolId = document.getElementById('filter-school').value;
        const start = document.getElementById('filter-start').value;
        const end = document.getElementById('filter-end').value;
        let url = `${API_BASE_URL}/quotations`;
        const params = [];
        if (schoolId) params.push(`school_id=${encodeURIComponent(schoolId)}`);
        if (start) params.push(`start=${encodeURIComponent(start)}`);
        if (end) params.push(`end=${encodeURIComponent(end)}`);
        if (params.length > 0) url += '?' + params.join('&');
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error('查询失败');
            const data = await res.json();
            renderQuotationsTable(data);
        } catch (e) {
            alert('查询失败');
        }
    });

    // --- 初始化加载 ---
    async function initializeAdminPage() {
        await fetchAllSchools(); // 先加载学校，因为项目表单需要学校列表
        await fetchAllRepairItems();
        await fetchAllQuotations();
        await initExportSchoolSelect(); // 初始化导出学校下拉
        await initFilterSchoolSelect(); // 初始化查询条件学校下拉
    }

    // 学校管理：新增、编辑、删除
    document.getElementById('add-school-btn').addEventListener('click', async () => {
        const name = prompt('请输入学校名称：');
        if (!name) return;
        try {
            const response = await fetch(`${API_BASE_URL}/schools`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            if (!response.ok) throw new Error('添加失败');
            alert('添加成功');
            await fetchAllSchools();
            await initExportSchoolSelect();
        } catch (e) { alert('添加失败'); }
    });

    schoolsTableBody.addEventListener('click', async (event) => {
        const target = event.target;
        const row = target.closest('tr');
        if (!row) return;
        const id = row.children[0].textContent;
        if (target.classList.contains('edit-school-btn')) {
            const oldName = row.children[1].textContent;
            const name = prompt('修改学校名称：', oldName);
            if (!name) return;
            try {
                const response = await fetch(`${API_BASE_URL}/schools/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                if (!response.ok) throw new Error('修改失败');
                alert('修改成功');
                await fetchAllSchools();
                await initExportSchoolSelect();
            } catch (e) { alert('修改失败'); }
        } else if (target.classList.contains('delete-school-btn')) {
            if (!confirm('确定删除该学校？')) return;
            try {
                const response = await fetch(`${API_BASE_URL}/schools/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('删除失败');
                alert('删除成功');
                await fetchAllSchools();
                await initExportSchoolSelect();
            } catch (e) { alert('删除失败'); }
        }
    });

    // 计价单删除事件监听
    quotationsTableBody.addEventListener('click', async (event) => {
        const target = event.target;
        if (target.classList.contains('delete-quotation-btn')) {
            const id = target.dataset.id;
            if (!confirm('确定要删除该计价单吗？此操作不可恢复。')) return;
            try {
                const response = await fetch(`${API_BASE_URL}/quotations/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('删除失败');
                alert('删除成功');
                fetchAllQuotations();
            } catch (e) {
                alert('删除失败');
            }
        }
    });

    initializeAdminPage();
});