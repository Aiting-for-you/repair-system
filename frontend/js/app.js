// frontend/js/app.js
document.addEventListener('DOMContentLoaded', () => {
    const schoolSelect = document.getElementById('school-select');
    const itemsGrid = document.getElementById('items-grid');
    const repairItemSelect = document.getElementById('repair-item-select'); // 新增：维修项目下拉选择框
    const repairQuantityInput = document.getElementById('repair-quantity'); // 新增：维修数量输入框
    const addItemToCartBtn = document.getElementById('add-item-to-cart-btn'); // 新增：添加到计价单按钮
    const repairPersonInput = document.getElementById('repair-person'); // 新增：维修人员输入框
    const repairLocationInput = document.getElementById('repair-location'); // 新增：维修地点输入框
    const repairTimeInput = document.getElementById('repair-time'); // 新增：维修时间输入框
    const selectedItemsList = document.getElementById('selected-items-list');
    const totalPriceEl = document.getElementById('total-price');
    const submitQuotationBtn = document.getElementById('submit-quotation-btn');

    const API_BASE_URL = 'http://127.0.0.1:5001/api'; // 后端API地址

    let currentSchoolId = null;
    let currentRepairItems = []; // 当前学校的维修项目
    let selectedQuotationItems = []; // 当前计价单中的项目

    /**
     * 获取学校列表并填充选择框
     */
    async function fetchSchools() {
        try {
            const response = await fetch(`${API_BASE_URL}/schools`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const schools = await response.json();
            schools.forEach(school => {
                const option = document.createElement('option');
                option.value = school.id;
                option.textContent = school.name;
                schoolSelect.appendChild(option);
            });
        } catch (error) {
            console.error("获取学校列表失败:", error);
            alert("获取学校列表失败，请检查网络或联系管理员。");
        }
    }

    /**
     * 根据学校ID获取维修项目
     * @param {number} schoolId 学校ID
     */
    async function fetchRepairItems(schoolId) {
        if (!schoolId) {
            // itemsGrid.innerHTML = '<p>请先选择学校</p>'; // 旧的网格布局，不再使用
            repairItemSelect.innerHTML = '<option value="">请先选择学校</option>'; // 更新下拉框
            currentRepairItems = [];
            return;
        }
        try {
            // itemsGrid.innerHTML = '<p>加载中...</p>'; // 旧的网格布局
            repairItemSelect.innerHTML = '<option value="">加载中...</option>'; // 更新下拉框
            const response = await fetch(`${API_BASE_URL}/schools/${schoolId}/items`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            currentRepairItems = await response.json();
            renderRepairItemsDropdown(); // 修改为渲染下拉框
        } catch (error) {
            console.error(`获取学校 ${schoolId} 的维修项目失败:`, error);
            // itemsGrid.innerHTML = '<p>加载维修项目失败，请稍后重试。</p>'; // 旧的网格布局
            repairItemSelect.innerHTML = '<option value="">加载失败</option>'; // 更新下拉框
            currentRepairItems = [];
        }
    }

    /**
     * 渲染维修项目到下拉选择框
     */
    function renderRepairItemsDropdown() {
        repairItemSelect.innerHTML = '<option value="">请选择维修项目</option>'; // 清空并添加默认选项
        if (currentRepairItems.length === 0 && currentSchoolId) {
            repairItemSelect.innerHTML = '<option value="">该学校暂无维修项目</option>';
            return;
        }
        currentRepairItems.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = `${item.name} (${item.price.toFixed(2)} 元 / ${item.unit})`;
            option.dataset.price = item.price;
            option.dataset.unit = item.unit;
            option.dataset.name = item.name; // 存储项目名称
            repairItemSelect.appendChild(option);
        });
    }

    /**
     * 获取指定项目在购物车中的数量
     * @param {number} itemId 项目ID
     * @returns {number} 数量
     */
    function getQuantityInCart(itemId) {
        const foundItem = selectedQuotationItems.find(item => item.item_id === itemId);
        return foundItem ? foundItem.quantity : 0;
    }

    /**
     * 更新项目卡片上的数量和按钮状态
     * @param {number} itemId 项目ID
     * @param {number} quantity 数量
     */
    function updateItemCardQuantity(itemId, quantity) {
        // const qtyInput = document.getElementById(`qty-${itemId}`); // 旧的网格布局中的输入框
        // const addToCartBtn = itemsGrid.querySelector(`.add-to-cart-btn[data-item-id="${itemId}"]`); // 旧的网格布局中的按钮
        // const decreaseBtn = itemsGrid.querySelector(`.decrease-qty[data-item-id="${itemId}"]`); // 旧的网格布局中的按钮

        // if (qtyInput) qtyInput.value = quantity; // 旧逻辑
        // if (addToCartBtn) { // 旧逻辑
        //     addToCartBtn.disabled = quantity > 0;
        //     addToCartBtn.textContent = quantity > 0 ? '已添加' : '添加到计价单';
        // }
        // if (decreaseBtn) { // 旧逻辑
        //     decreaseBtn.disabled = quantity === 0;
        // }
        // 对于新的下拉框模式，我们主要更新已选列表，不需要直接操作卡片上的数量显示
        // 如果需要，可以在这里添加逻辑来禁用/启用下拉框中的已选项目，或更新其显示
    }

    /**
     * 处理添加到计价单按钮点击事件
     * @param {number} itemId 项目ID
     * @param {number} quantity 数量
     */
    function handleAddToCart(itemId, quantity) { // quantity 现在是必须的
        if (!itemId || quantity <= 0) {
            alert("请选择有效的维修项目和数量！");
            return;
        }

        const selectedOption = repairItemSelect.options[repairItemSelect.selectedIndex];
        if (!selectedOption || !selectedOption.value) {
            alert("请选择一个维修项目！");
            return;
        }

        const itemToAdd = {
            id: parseInt(selectedOption.value),
            name: selectedOption.dataset.name,
            price: parseFloat(selectedOption.dataset.price),
            unit: selectedOption.dataset.unit
        };

        if (!itemToAdd) return; // 应该不会发生，因为我们从下拉框获取

        const existingItem = selectedQuotationItems.find(item => item.item_id === itemToAdd.id);

        if (existingItem) {
            existingItem.quantity = quantity; // 直接使用传入的quantity
            existingItem.subtotal = existingItem.price * existingItem.quantity;
        } else {
            selectedQuotationItems.push({
                item_id: itemToAdd.id,
                name: itemToAdd.name,
                price: itemToAdd.price,
                unit: itemToAdd.unit,
                quantity: quantity,
                subtotal: itemToAdd.price * quantity
            });
        }
        // updateItemCardQuantity(itemId, quantity); // 旧的网格布局逻辑，不再需要
        renderSelectedItems();
        calculateTotalPrice();
        // 清空选择和数量，以便添加下一个
        repairItemSelect.value = '';
        repairQuantityInput.value = '1';
    }

    /**
     * 处理从计价单移除项目
     * @param {number} itemId 项目ID
     */
    function handleRemoveFromCart(itemId) {
        selectedQuotationItems = selectedQuotationItems.filter(item => item.item_id !== itemId);
        updateItemCardQuantity(itemId, 0);
        renderSelectedItems();
        calculateTotalPrice();
    }

    /**
     * 渲染已选项目到计价单列表
     */
    function renderSelectedItems() {
        selectedItemsList.innerHTML = ''; // 清空
        if (selectedQuotationItems.length === 0) {
            selectedItemsList.innerHTML = '<p class="empty-cart-message">请从左侧选择维修项目</p>';
            totalPriceEl.textContent = '0.00';
            return;
        }

        selectedQuotationItems.forEach(item => {
            const listItem = document.createElement('div');
            listItem.classList.add('selected-item');
            listItem.innerHTML = `
                <div class="item-info">
                    <span class="item-name">${item.name}</span>
                    <span class="item-details">(${item.quantity} ${item.unit} x ${item.price.toFixed(2)})</span>
                </div>
                <span class="item-subtotal">${item.subtotal.toFixed(2)}</span>
                <button class="button remove-item-btn" data-item-id="${item.item_id}">移除</button>
            `;
            selectedItemsList.appendChild(listItem);
        });
    }

    /**
     * 计算并显示总价
     */
    function calculateTotalPrice() {
        const total = selectedQuotationItems.reduce((sum, item) => sum + item.subtotal, 0);
        totalPriceEl.textContent = total.toFixed(2);
        return total;
    }

    /**
     * 提交计价单
     */
    async function submitQuotation() {
        if (selectedQuotationItems.length === 0) {
            alert('请至少选择一个维修项目！');
            return;
        }
        if (!currentSchoolId) {
            alert('请选择学校！');
            return;
        }
        const repairPerson = repairPersonInput.value.trim();
        const repairLocation = repairLocationInput.value.trim();
        const repairTime = repairTimeInput.value.trim();

        if (!repairPerson) {
            alert('请输入维修人员！');
            repairPersonInput.focus();
            return;
        }
        if (!repairLocation) {
            alert('请输入维修地点！');
            repairLocationInput.focus();
            return;
        }
        if (!repairTime) {
            alert('请选择或输入维修时间！');
            repairTimeInput.focus();
            return;
        }

        const quotationData = {
            school_id: parseInt(currentSchoolId),
            repair_person: repairPerson, // 新增
            repair_location: repairLocation, // 新增
            repair_time: repairTime, // 新增
            items: selectedQuotationItems.map(item => ({ // 确保后端需要的字段
                item_id: item.item_id,
                name: item.name,
                price: item.price,
                unit: item.unit,
                quantity: item.quantity,
                subtotal: item.subtotal
            })),
            total_price: parseFloat(calculateTotalPrice())
        };

        try {
            submitQuotationBtn.disabled = true;
            submitQuotationBtn.textContent = '提交中...';
            const response = await fetch(`${API_BASE_URL}/quotations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(quotationData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            alert(`计价单 ${result.quotation_number} 提交成功！`);

            // 弹出新窗口或提供链接下载图片和Excel
            const confirmation = confirm("是否立即生成并下载计价单图片和Excel文件？");
            if (confirmation) {
                window.open(`${API_BASE_URL}/quotations/${result.id}/image`, '_blank');
                window.open(`${API_BASE_URL}/quotations/${result.id}/excel`, '_blank');
            }

            // 重置表单
            selectedQuotationItems = [];
            renderSelectedItems();
            // renderRepairItems(); // 旧的网格布局逻辑，现在是下拉框
            renderRepairItemsDropdown(); // 重新渲染下拉框，如果需要的话（比如库存变化）
            repairPersonInput.value = '';
            repairLocationInput.value = '';
            repairTimeInput.value = '';
            repairItemSelect.value = '';
            repairQuantityInput.value = '1';

        } catch (error) {
            console.error("提交计价单失败:", error);
            alert(`提交计价单失败: ${error.message}`);
        } finally {
            submitQuotationBtn.disabled = false;
            submitQuotationBtn.textContent = '提交计价单';
        }
    }

    // --- 事件监听 ---
    schoolSelect.addEventListener('change', (event) => {
        currentSchoolId = event.target.value;
        selectedQuotationItems = []; //切换学校时清空已选项目
        renderSelectedItems();
        fetchRepairItems(currentSchoolId);
        repairItemSelect.value = ''; // 重置维修项目选择
        repairQuantityInput.value = '1'; // 重置数量
    });

    // itemsGrid.addEventListener('click', (event) => { ... }); // 旧的网格布局事件监听，移除
    // itemsGrid.addEventListener('change', (event) => { ... }); // 旧的网格布局事件监听，移除

    // 新增：添加到计价单按钮的事件监听
    addItemToCartBtn.addEventListener('click', () => {
        const selectedItemId = parseInt(repairItemSelect.value);
        const quantity = parseInt(repairQuantityInput.value);

        if (!selectedItemId) {
            alert('请选择一个维修项目！');
            repairItemSelect.focus();
            return;
        }
        if (isNaN(quantity) || quantity <= 0) {
            alert('请输入有效的维修数量！');
            repairQuantityInput.focus();
            return;
        }
        handleAddToCart(selectedItemId, quantity);
    });

    selectedItemsList.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-item-btn')) {
            const itemId = parseInt(event.target.dataset.itemId);
            handleRemoveFromCart(itemId);
        }
    });

    submitQuotationBtn.addEventListener('click', submitQuotation);

    // --- 初始化 ---
    fetchSchools();
    renderSelectedItems(); // 初始化时显示空购物车消息
    // itemsGrid.innerHTML = '<p>请先选择学校</p>'; // 旧的网格布局初始提示
    repairItemSelect.innerHTML = '<option value="">请先选择学校</option>'; // 新的下拉框初始提示
    repairQuantityInput.value = '1'; // 初始化数量为1
});