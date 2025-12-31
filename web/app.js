// Family Meal Planner Application
let recipes = [];
let weeklyPlan = {};
let currentServings = 4;
let nutrientInteractions = null;
let functionHealthData = null;
let userBiomarkers = {};
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    auth.onAuthStateChanged(async (user) => {
        if (!user) {
            // User not logged in, redirect to login page
            window.location.href = 'auth.html';
            return;
        }
        
        currentUser = user;
        console.log('User authenticated:', user.email);
        
        // Update user menu
        document.getElementById('user-email').textContent = user.email;
        
        // Load app data
        await loadRecipes();
        await loadNutrientInteractions();
        await loadFunctionHealthData();
        await loadUserData();
        setupEventListeners();
        setupUserMenu();
        renderRecipes();
        initializeDragAndDrop();
    });
});

// Load recipes from JSON
async function loadRecipes() {
    try {
        const response = await fetch('../data/recipes/recipe-database.json');
        const data = await response.json();
        recipes = data.recipes;
        console.log('Loaded recipes:', recipes.length);
    } catch (error) {
        console.error('Error loading recipes:', error);
        alert('Could not load recipes. Please check data file.');
    }
}

// Load nutrient interactions for bioavailability and synergy analysis
async function loadNutrientInteractions() {
    try {
        const response = await fetch('../data/nutrition-requirements/nutrient-interactions.json');
        nutrientInteractions = await response.json();
        console.log('Loaded nutrient interactions');
    } catch (error) {
        console.warn('Could not load nutrient interactions - synergy analysis disabled');
    }
}

// Load Function Health biomarker data
async function loadFunctionHealthData() {
    try {
        const response = await fetch('../data/biomarkers/function-health-integration.json');
        functionHealthData = await response.json();
        console.log('Loaded Function Health biomarker data');
    } catch (error) {
        console.warn('Could not load Function Health data - biomarker analysis disabled');
    }
}

// Load user data from Firestore
async function loadUserData() {
    if (!currentUser) return;
    
    try {
        // Load user preferences
        const userDoc = await db.collection('users').doc(currentUser.uid).get();
        if (userDoc.exists) {
            const userData = userDoc.data();
            if (userData.preferences) {
                currentServings = userData.preferences.servings || 4;
                document.getElementById('servings').value = currentServings;
            }
        }
        
        // Load weekly plan
        const planDoc = await db.collection('users').doc(currentUser.uid)
            .collection('mealPlans').doc('current').get();
        if (planDoc.exists) {
            weeklyPlan = planDoc.data().plan || {};
            renderWeeklyPlan();
        }
        
        // Load biomarkers
        const biomarkersDoc = await db.collection('users').doc(currentUser.uid)
            .collection('biomarkers').doc('latest').get();
        if (biomarkersDoc.exists) {
            userBiomarkers = biomarkersDoc.data().markers || {};
            loadSavedBiomarkers();
        }
        
        console.log('User data loaded successfully');
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Save user data to Firestore
async function saveUserData(type, data) {
    if (!currentUser) return;
    
    try {
        switch (type) {
            case 'preferences':
                await db.collection('users').doc(currentUser.uid).update({
                    'preferences': data,
                    'lastUpdated': firebase.firestore.FieldValue.serverTimestamp()
                });
                break;
                
            case 'weeklyPlan':
                await db.collection('users').doc(currentUser.uid)
                    .collection('mealPlans').doc('current').set({
                        plan: data,
                        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                    }, { merge: true });
                break;
                
            case 'biomarkers':
                await db.collection('users').doc(currentUser.uid)
                    .collection('biomarkers').doc('latest').set({
                        markers: data,
                        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                    }, { merge: true });
                break;
        }
        console.log(`${type} saved successfully`);
    } catch (error) {
        console.error(`Error saving ${type}:`, error);
        alert(`Failed to save ${type}. Please try again.`);
    }
}

// Setup user menu
function setupUserMenu() {
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userDropdown = document.getElementById('user-dropdown');
    const logoutLink = document.getElementById('logout-link');
    
    userMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = userDropdown.style.display === 'block';
        userDropdown.style.display = isOpen ? 'none' : 'block';
        userMenuBtn.classList.toggle('open');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        userDropdown.style.display = 'none';
        userMenuBtn.classList.remove('open');
    });
    
    // Logout
    logoutLink.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            await auth.signOut();
            window.location.href = 'auth.html';
        } catch (error) {
            console.error('Logout error:', error);
            alert('Failed to logout. Please try again.');
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => filterRecipes(btn.dataset.filter));
    });

    // Serving size selector
    const servingSelect = document.getElementById('servings');
    servingSelect.addEventListener('change', (e) => {
        currentServings = parseInt(e.target.value);
        renderRecipes();
        updateAnalysisServings();
    });

    // Planner actions
    document.getElementById('auto-generate-plan').addEventListener('click', autoGeneratePlan);
    document.getElementById('clear-plan').addEventListener('click', clearPlan);
    document.getElementById('analyze-week').addEventListener('click', analyzeWeek);
    document.getElementById('save-plan').addEventListener('click', async () => {
        try {
            await savePlan();
        } catch (error) {
            console.error('Save error:', error);
            alert('Failed to save meal plan. Please try again.');
        }
    });

    // Biomarker actions
    document.getElementById('analyze-biomarkers').addEventListener('click', analyzeBiomarkers);
    document.getElementById('clear-biomarkers').addEventListener('click', clearBiomarkers);
    document.getElementById('save-biomarkers').addEventListener('click', async () => {
        try {
            await saveBiomarkers();
        } catch (error) {
            console.error('Save error:', error);
            alert('Failed to save biomarkers. Please try again.');
        }
    });

    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('recipe-modal');
        if (e.target === modal) closeModal();
    });
    
    // Initialize recipe management
    initializeRecipeManagement();
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // If switching to nutrition tab, analyze if plan exists
    if (tabName === 'nutrition' && Object.keys(weeklyPlan).length > 0) {
        analyzeWeek();
    }
}

// Filter recipes by meal type
function filterRecipes(filter) {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    renderRecipes(filter);
}

// Render recipe cards
function renderRecipes(filter = 'all') {
    const grid = document.getElementById('recipe-grid');
    grid.innerHTML = '';

    const filteredRecipes = filter === 'all' 
        ? recipes 
        : recipes.filter(r => r.mealType === filter);

    filteredRecipes.forEach(recipe => {
        const card = createRecipeCard(recipe);
        grid.appendChild(card);
    });
}

// Create recipe card element
function createRecipeCard(recipe) {
    const scaledNutrition = scaleNutrition(recipe.nutritionPerServing, currentServings);
    
    // Check for synergies and warnings
    const warnings = checkRecipeWarnings(recipe, scaledNutrition);
    const synergies = checkRecipeSynergies(recipe, scaledNutrition);
    
    const card = document.createElement('div');
    card.className = 'recipe-card';
    card.draggable = true;
    card.dataset.recipeId = recipe.mealId;
    
    // Build warning badges
    let warningBadges = '';
    if (warnings.length > 0) {
        warningBadges = `<div class="warning-badges">`;
        warnings.forEach(warning => {
            warningBadges += `<span class="warning-badge" title="${warning.description}">⚠️ ${warning.type}</span>`;
        });
        warningBadges += `</div>`;
    }
    
    // Build synergy badges
    let synergyBadges = '';
    if (synergies.length > 0) {
        synergyBadges = `<div class="synergy-badges">`;
        synergies.forEach(synergy => {
            synergyBadges += `<span class="synergy-badge" title="${synergy.benefit}">✓ ${synergy.name}</span>`;
        });
        synergyBadges += `</div>`;
    }
    
    card.innerHTML = `
        <span class="meal-type-badge ${recipe.mealType}">${recipe.mealType}</span>
        <h3>${recipe.name}</h3>
        <p>${recipe.description}</p>
        ${warningBadges}
        ${synergyBadges}
        <div class="recipe-meta">
            <span>⏱️ ${recipe.prepTime}</span>
            <span>🔥 ${recipe.cookTime}</span>
            <span>👥 ${currentServings} servings</span>
        </div>
        <div class="recipe-nutrition-preview">
            <div class="nutrition-item">
                <div class="nutrition-value">${Math.round(scaledNutrition.calories)}</div>
                <div class="nutrition-label">calories</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-value">${Math.round(scaledNutrition.macronutrients.protein_g)}g</div>
                <div class="nutrition-label">protein</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-value">${Math.round(scaledNutrition.macronutrients.fiber_g)}g</div>
                <div class="nutrition-label">fiber</div>
            </div>
        </div>
        <div class="recipe-tags">
            ${recipe.tags ? recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
        </div>
    `;

    // Click to view details
    card.addEventListener('click', () => showRecipeDetail(recipe));

    // Drag handlers
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);

    return card;
}

// Scale nutrition based on servings
function scaleNutrition(nutrition, servings) {
    const scaled = { ...nutrition };
    scaled.calories = nutrition.calories * servings;
    
    scaled.macronutrients = {};
    for (let key in nutrition.macronutrients) {
        scaled.macronutrients[key] = nutrition.macronutrients[key] * servings;
    }
    
    return scaled;
}

// Show recipe detail modal
function showRecipeDetail(recipe) {
    const modal = document.getElementById('recipe-modal');
    const detail = document.getElementById('recipe-detail');
    const scaledNutrition = scaleNutrition(recipe.nutritionPerServing, currentServings);
    
    // Scale ingredients
    const scaledIngredients = recipe.ingredients.map(ing => {
        const scaledAmount = ing.amount * currentServings;
        return `<li><strong>${scaledAmount} ${ing.unit}</strong> ${ing.name} ${ing.notes ? `<em>(${ing.notes})</em>` : ''}</li>`;
    }).join('');
    
    // Preparation notes section (if available)
    let prepNotesHtml = '';
    if (recipe.preparationNotes) {
        const notes = recipe.preparationNotes;
        prepNotesHtml = `
            <div class="preparation-notes">
                <h3>💡 Preparation Tips</h3>
                ${notes.antiNutrientReduction ? `
                    <div class="prep-note">
                        <strong>Anti-Nutrient Reduction:</strong>
                        <p>${notes.antiNutrientReduction}</p>
                    </div>
                ` : ''}
                ${notes.bioavailabilityTips ? `
                    <div class="prep-note">
                        <strong>Bioavailability Optimization:</strong>
                        <p>${notes.bioavailabilityTips}</p>
                    </div>
                ` : ''}
                ${notes.nutrientSynergies && notes.nutrientSynergies.length > 0 ? `
                    <div class="prep-note">
                        <strong>Nutrient Synergies:</strong>
                        <ul class="synergy-list">
                            ${notes.nutrientSynergies.map(syn => `<li>${syn}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    detail.innerHTML = `
        <h2>${recipe.name}</h2>
        <span class="meal-type-badge ${recipe.mealType}">${recipe.mealType}</span>
        <p>${recipe.description}</p>
        
        <div class="recipe-meta">
            <span>⏱️ Prep: ${recipe.prepTime}</span>
            <span>🔥 Cook: ${recipe.cookTime}</span>
            <span>👥 ${currentServings} servings</span>
        </div>

        <h3>Ingredients</h3>
        <ul class="ingredient-list">
            ${scaledIngredients}
        </ul>

        <h3>Instructions</h3>
        <ol class="instruction-list">
            ${recipe.instructions.map(step => `<li>${step}</li>`).join('')}
        </ol>
        
        ${prepNotesHtml}

        <h3>Nutrition (Total for ${currentServings} servings)</h3>
        <div class="nutrition-summary">
            <div class="summary-card">
                <strong>${Math.round(scaledNutrition.calories)}</strong> calories
            </div>
            <div class="summary-card">
                <strong>${Math.round(scaledNutrition.macronutrients.protein_g)}g</strong> protein
            </div>
            <div class="summary-card">
                <strong>${Math.round(scaledNutrition.macronutrients.carbohydrates_g)}g</strong> carbs
            </div>
            <div class="summary-card">
                <strong>${Math.round(scaledNutrition.macronutrients.fat_g)}g</strong> fat
            </div>
            <div class="summary-card">
                <strong>${Math.round(scaledNutrition.macronutrients.fiber_g)}g</strong> fiber
            </div>
        </div>

        <button class="btn-primary add-to-plan-btn" onclick="closeModal()">Close</button>
    `;

    modal.classList.add('show');
}

function closeModal() {
    document.getElementById('recipe-modal').classList.remove('show');
}

// Drag and Drop functionality
let draggedRecipeId = null;

function initializeDragAndDrop() {
    document.querySelectorAll('.drop-zone').forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('dragleave', handleDragLeave);
        zone.addEventListener('drop', handleDrop);
        zone.addEventListener('click', handleZoneClick);
    });
}

function handleDragStart(e) {
    draggedRecipeId = e.target.dataset.recipeId;
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'copy';
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    const mealSlot = e.currentTarget.closest('.meal-slot');
    const day = mealSlot.closest('.day-column').dataset.day;
    const meal = mealSlot.dataset.meal;
    
    addRecipeToPlan(day, meal, draggedRecipeId);
}

function handleZoneClick(e) {
    const mealSlot = e.currentTarget.closest('.meal-slot');
    const day = mealSlot.closest('.day-column').dataset.day;
    const meal = mealSlot.dataset.meal;
    
    // Show recipe selector (simplified - you could make this a better UI)
    const mealType = meal === 'snack' ? 'snack' : meal;
    const options = recipes
        .filter(r => r.mealType === mealType)
        .map(r => `${r.name}`)
        .join('\n');
    
    // For now, just allow clicking a recipe card from the recipe tab
    alert('Drag a recipe from the Recipe Library tab, or we can implement a selection dialog here.');
}

function addRecipeToPlan(day, meal, recipeId) {
    if (!weeklyPlan[day]) weeklyPlan[day] = {};
    
    const recipe = recipes.find(r => r.mealId === recipeId);
    if (!recipe) return;
    
    weeklyPlan[day][meal] = {
        recipeId: recipe.mealId,
        recipeName: recipe.name,
        servings: currentServings
    };
    
    renderMealInSlot(day, meal, recipe);
}

function renderWeeklyPlan() {
    // Render all saved meals from weeklyPlan object
    for (let day in weeklyPlan) {
        for (let meal in weeklyPlan[day]) {
            const planItem = weeklyPlan[day][meal];
            const recipe = recipes.find(r => r.mealId === planItem.recipeId);
            if (recipe) {
                renderMealInSlot(day, meal, recipe);
            }
        }
    }
}

function renderMealInSlot(day, meal, recipe) {
    const mealSlot = document.querySelector(`[data-day="${day}"] [data-meal="${meal}"]`);
    const dropZone = mealSlot.querySelector('.drop-zone');
    
    dropZone.classList.add('filled');
    dropZone.innerHTML = `
        <div class="meal-recipe">${recipe.name}<br><small>${currentServings} servings</small></div>
        <button class="remove-meal" onclick="removeMealFromPlan('${day}', '${meal}')">×</button>
    `;
}

function removeMealFromPlan(day, meal) {
    if (weeklyPlan[day]) {
        delete weeklyPlan[day][meal];
        if (Object.keys(weeklyPlan[day]).length === 0) {
            delete weeklyPlan[day];
        }
    }
    
    const mealSlot = document.querySelector(`[data-day="${day}"] [data-meal="${meal}"]`);
    const dropZone = mealSlot.querySelector('.drop-zone');
    dropZone.classList.remove('filled');
    dropZone.innerHTML = 'Drop recipe here or click to select';
}

function autoGeneratePlan() {
    if (recipes.length === 0) {
        alert('Recipes are still loading. Please wait a moment.');
        return;
    }
    
    if (Object.keys(weeklyPlan).length > 0) {
        if (!confirm('This will replace your current meal plan. Continue?')) return;
    }
    
    // Clear existing plan
    weeklyPlan = {};
    
    // Group recipes by meal type
    const breakfasts = recipes.filter(r => r.mealType === 'breakfast');
    const lunches = recipes.filter(r => r.mealType === 'lunch');
    const dinners = recipes.filter(r => r.mealType === 'dinner');
    const snacks = recipes.filter(r => r.mealType === 'snack');
    
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    const usedRecipes = { breakfast: new Set(), lunch: new Set(), dinner: new Set(), snack: new Set() };
    
    // Generate plan for each day
    days.forEach(day => {
        weeklyPlan[day] = {};
        
        // Select breakfast (ensure variety)
        const availableBreakfasts = breakfasts.filter(r => !usedRecipes.breakfast.has(r.mealId));
        const breakfast = availableBreakfasts.length > 0 
            ? availableBreakfasts[Math.floor(Math.random() * availableBreakfasts.length)]
            : breakfasts[Math.floor(Math.random() * breakfasts.length)];
        usedRecipes.breakfast.add(breakfast.mealId);
        weeklyPlan[day].breakfast = { recipeId: breakfast.mealId, recipeName: breakfast.name, servings: currentServings };
        
        // Select lunch
        const availableLunches = lunches.filter(r => !usedRecipes.lunch.has(r.mealId));
        const lunch = availableLunches.length > 0
            ? availableLunches[Math.floor(Math.random() * availableLunches.length)]
            : lunches[Math.floor(Math.random() * lunches.length)];
        usedRecipes.lunch.add(lunch.mealId);
        weeklyPlan[day].lunch = { recipeId: lunch.mealId, recipeName: lunch.name, servings: currentServings };
        
        // Select dinner
        const availableDinners = dinners.filter(r => !usedRecipes.dinner.has(r.mealId));
        const dinner = availableDinners.length > 0
            ? availableDinners[Math.floor(Math.random() * availableDinners.length)]
            : dinners[Math.floor(Math.random() * dinners.length)];
        usedRecipes.dinner.add(dinner.mealId);
        weeklyPlan[day].dinner = { recipeId: dinner.mealId, recipeName: dinner.name, servings: currentServings };
        
        // Select snack
        if (snacks.length > 0) {
            const availableSnacks = snacks.filter(r => !usedRecipes.snack.has(r.mealId));
            const snack = availableSnacks.length > 0
                ? availableSnacks[Math.floor(Math.random() * availableSnacks.length)]
                : snacks[Math.floor(Math.random() * snacks.length)];
            usedRecipes.snack.add(snack.mealId);
            weeklyPlan[day].snack = { recipeId: snack.mealId, recipeName: snack.name, servings: currentServings };
        }
    });
    
    // Render the generated plan
    renderWeeklyPlan();
    
    // Show success message
    alert(`✨ Weekly meal plan generated for ${currentServings} people! Click "Save Plan" to save to cloud.`);
}

function clearPlan() {
    if (!confirm('Clear entire meal plan?')) return;
    
    weeklyPlan = {};
    document.querySelectorAll('.drop-zone').forEach(zone => {
        zone.classList.remove('filled');
        zone.innerHTML = 'Drop recipe here or click to select';
    });
}

function analyzeWeek() {
    if (Object.keys(weeklyPlan).length === 0) {
        alert('Please add some meals to your plan first!');
        return;
    }

    // Calculate weekly nutrition
    let totalNutrition = initializeNutritionTotals();
    let mealCount = 0;

    for (let day in weeklyPlan) {
        for (let meal in weeklyPlan[day]) {
            const planItem = weeklyPlan[day][meal];
            const recipe = recipes.find(r => r.mealId === planItem.recipeId);
            if (recipe) {
                const scaledNutrition = scaleNutrition(recipe.nutritionPerServing, planItem.servings);
                addNutrition(totalNutrition, scaledNutrition);
                mealCount++;
            }
        }
    }

    // Calculate daily averages (assuming 7 days, but only filled days)
    const daysWithMeals = Object.keys(weeklyPlan).length;
    const dailyAverage = divideNutrition(totalNutrition, daysWithMeals || 1);

    // Display results
    displayNutritionAnalysis(dailyAverage, totalNutrition);
    
    // Switch to nutrition tab
    switchTab('nutrition');
}

function initializeNutritionTotals() {
    return {
        calories: 0,
        macronutrients: {
            protein_g: 0,
            carbohydrates_g: 0,
            fat_g: 0,
            fiber_g: 0,
            omega3_g: 0
        },
        vitamins: {},
        minerals: {}
    };
}

function addNutrition(total, addition) {
    total.calories += addition.calories || 0;
    
    // Add macronutrients
    for (let key in addition.macronutrients) {
        total.macronutrients[key] = (total.macronutrients[key] || 0) + (addition.macronutrients[key] || 0);
    }
    
    // Add vitamins
    if (addition.vitamins) {
        for (let key in addition.vitamins) {
            total.vitamins[key] = (total.vitamins[key] || 0) + (addition.vitamins[key] || 0);
        }
    }
    
    // Add minerals
    if (addition.minerals) {
        for (let key in addition.minerals) {
            total.minerals[key] = (total.minerals[key] || 0) + (addition.minerals[key] || 0);
        }
    }
}

function divideNutrition(nutrition, divisor) {
    const result = { ...nutrition };
    result.calories = Math.round(nutrition.calories / divisor);
    
    // Divide macronutrients
    result.macronutrients = {};
    for (let key in nutrition.macronutrients) {
        result.macronutrients[key] = Math.round(nutrition.macronutrients[key] / divisor);
    }
    
    // Divide vitamins
    result.vitamins = {};
    for (let key in nutrition.vitamins) {
        result.vitamins[key] = Math.round((nutrition.vitamins[key] / divisor) * 10) / 10;
    }
    
    // Divide minerals
    result.minerals = {};
    for (let key in nutrition.minerals) {
        result.minerals[key] = Math.round((nutrition.minerals[key] / divisor) * 10) / 10;
    }
    
    return result;
}

function displayNutritionAnalysis(dailyAverage, weeklyTotal) {
    // RDA/Optimal targets for adults
    const targets = {
        macros: {
            protein_g: { target: 120, unit: 'g', name: 'Protein' },
            carbohydrates_g: { target: 130, unit: 'g', name: 'Carbohydrates' },
            fat_g: { target: 70, unit: 'g', name: 'Fat' },
            fiber_g: { target: 40, unit: 'g', name: 'Fiber' },
            omega3_g: { target: 2.5, unit: 'g', name: 'Omega-3' }
        },
        vitamins: {
            vitaminA_mcg: { target: 900, unit: 'mcg', name: 'Vitamin A' },
            vitaminD_IU: { target: 600, unit: 'IU', name: 'Vitamin D' },
            vitaminE_mg: { target: 15, unit: 'mg', name: 'Vitamin E' },
            vitaminK_mcg: { target: 120, unit: 'mcg', name: 'Vitamin K' },
            vitaminC_mg: { target: 90, unit: 'mg', name: 'Vitamin C' },
            vitaminB12_mcg: { target: 2.4, unit: 'mcg', name: 'Vitamin B12' },
            vitaminB6_mg: { target: 1.7, unit: 'mg', name: 'Vitamin B6' },
            folate_B9_mcg: { target: 400, unit: 'mcg', name: 'Folate (B9)' },
            thiamin_B1_mg: { target: 1.2, unit: 'mg', name: 'Thiamin (B1)' },
            riboflavin_B2_mg: { target: 1.3, unit: 'mg', name: 'Riboflavin (B2)' },
            niacin_B3_mg: { target: 16, unit: 'mg', name: 'Niacin (B3)' },
            choline_mg: { target: 550, unit: 'mg', name: 'Choline' }
        },
        minerals: {
            iron_mg: { target: 18, unit: 'mg', name: 'Iron' },
            magnesium_mg: { target: 420, unit: 'mg', name: 'Magnesium' },
            selenium_mcg: { target: 55, unit: 'mcg', name: 'Selenium' },
            zinc_mg: { target: 11, unit: 'mg', name: 'Zinc' },
            potassium_mg: { target: 3500, unit: 'mg', name: 'Potassium' },
            calcium_mg: { target: 1000, unit: 'mg', name: 'Calcium' },
            phosphorus_mg: { target: 700, unit: 'mg', name: 'Phosphorus' },
            copper_mg: { target: 0.9, unit: 'mg', name: 'Copper' },
            manganese_mg: { target: 2.3, unit: 'mg', name: 'Manganese' }
        }
    };

    // Update summary cards
    document.getElementById('daily-calories').textContent = `${dailyAverage.calories} kcal`;
    document.getElementById('daily-protein').textContent = `${dailyAverage.macronutrients.protein_g}g protein`;
    document.getElementById('daily-fiber').textContent = `${dailyAverage.macronutrients.fiber_g}g fiber`;

    // Calculate overall compliance
    let totalCompliance = 0;
    let nutrientCount = 0;
    
    // Calculate macro compliance
    for (let key in targets.macros) {
        if (dailyAverage.macronutrients[key]) {
            const percent = (dailyAverage.macronutrients[key] / targets.macros[key].target) * 100;
            totalCompliance += Math.min(percent, 100);
            nutrientCount++;
        }
    }
    
    const avgCompliance = nutrientCount > 0 ? Math.round(totalCompliance / nutrientCount) : 0;
    document.getElementById('compliance-score').textContent = `${avgCompliance}%`;

    // Build detailed nutrient lists
    const compliantList = document.querySelector('#compliant-nutrients .nutrient-list');
    const deficientList = document.querySelector('#deficient-nutrients .nutrient-list');
    const excessiveList = document.querySelector('#excessive-nutrients .nutrient-list');

    compliantList.innerHTML = '';
    deficientList.innerHTML = '';
    excessiveList.innerHTML = '';

    // Helper function to display nutrient
    function displayNutrient(value, target, name, unit) {
        const percent = Math.round((value / target) * 100);
        const displayValue = unit.includes('mcg') || unit.includes('mg') ? value.toFixed(1) : Math.round(value);
        
        const html = `
            <div class="nutrient-item">
                <div class="nutrient-name">${name}</div>
                <div class="nutrient-value">${displayValue}${unit} / ${target}${unit}</div>
                <div class="nutrient-bar">
                    <div class="nutrient-bar-fill" style="width: ${Math.min(percent, 100)}%"></div>
                </div>
                <div class="nutrient-percent">${percent}% DV</div>
            </div>
        `;
        
        if (percent >= 90 && percent <= 150) {
            compliantList.innerHTML += html;
        } else if (percent < 90) {
            deficientList.innerHTML += html;
        } else {
            excessiveList.innerHTML += html;
        }
    }

    // Display macronutrients
    for (let key in targets.macros) {
        if (dailyAverage.macronutrients[key]) {
            displayNutrient(
                dailyAverage.macronutrients[key],
                targets.macros[key].target,
                targets.macros[key].name,
                targets.macros[key].unit
            );
        }
    }

    // Display vitamins
    for (let key in targets.vitamins) {
        if (dailyAverage.vitamins && dailyAverage.vitamins[key]) {
            displayNutrient(
                dailyAverage.vitamins[key],
                targets.vitamins[key].target,
                targets.vitamins[key].name,
                targets.vitamins[key].unit
            );
        }
    }

    // Display minerals
    for (let key in targets.minerals) {
        if (dailyAverage.minerals && dailyAverage.minerals[key]) {
            displayNutrient(
                dailyAverage.minerals[key],
                targets.minerals[key].target,
                targets.minerals[key].name,
                targets.minerals[key].unit
            );
        }
    }

    // Show/hide sections based on content
    document.querySelector('#compliant-nutrients').style.display = compliantList.innerHTML ? 'block' : 'none';
    document.querySelector('#deficient-nutrients').style.display = deficientList.innerHTML ? 'block' : 'none';
    document.querySelector('#excessive-nutrients').style.display = excessiveList.innerHTML ? 'block' : 'none';
}

function updateAnalysisServings() {
    document.getElementById('analysis-servings').textContent = currentServings;
}

async function savePlan() {
    const planData = {
        planName: `Meal Plan - ${new Date().toLocaleDateString()}`,
        servings: currentServings,
        weeklyPlan: weeklyPlan
    };

    // Save to Firestore
    await saveUserData('weeklyPlan', weeklyPlan);
    
    // Also save preferences
    await saveUserData('preferences', { servings: currentServings });
    
    // Also offer download
    const dataStr = JSON.stringify(planData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `meal-plan-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    alert('Meal plan saved to cloud and downloaded!');
}
// Check for warnings (anti-nutrients, antagonistic combinations)
function checkRecipeWarnings(recipe, nutrition) {
    if (!nutrientInteractions) return [];
    
    const warnings = [];
    const calcium = nutrition.minerals?.calcium_mg || 0;
    const iron = nutrition.minerals?.iron_mg || 0;
    const fiber = nutrition.macronutrients?.fiber_g || 0;
    
    // Check for calcium-iron antagonism
    if (calcium > 300 && iron > 5) {
        warnings.push({
            type: 'Ca+Fe Competition',
            severity: 'medium',
            description: 'High calcium and iron in same meal - calcium may reduce iron absorption by 30-50%. Consider separating by 2+ hours.'
        });
    }
    
    // Check for high oxalates if spinach is present
    const hasSpinach = recipe.ingredients?.some(ing => ing.foodId?.includes('spinach'));
    if (hasSpinach && iron > 3) {
        warnings.push({
            type: 'Oxalates',
            severity: 'low',
            description: 'Spinach contains oxalates which can reduce iron absorption. Cooking reduces oxalates by 30-87%.'
        });
    }
    
    // Check if it's an iron-rich meal (warn about tea/coffee)
    if (iron > 5) {
        warnings.push({
            type: 'Iron Timing',
            severity: 'low',
            description: 'Iron-rich meal - avoid tea/coffee 1-2 hours before and after (tannins reduce iron absorption by 60-70%)'
        });
    }
    
    return warnings;
}

// Check for nutrient synergies
function checkRecipeSynergies(recipe, nutrition) {
    if (!nutrientInteractions) return [];
    
    const synergies = [];
    
    // Check for bone health trio (Ca + D + K2 + Mg)
    const calcium = nutrition.minerals?.calcium_mg || 0;
    const vitaminD = nutrition.vitamins?.vitaminD_IU || 0;
    const vitaminK2 = nutrition.vitamins?.vitaminK2_mcg || 0;
    const magnesium = nutrition.minerals?.magnesium_mg || 0;
    
    if (calcium > 200 && vitaminD > 200 && vitaminK2 > 10 && magnesium > 50) {
        synergies.push({
            name: 'Bone Health Trio',
            benefit: 'Complete synergy: Ca+D+K2+Mg ensures calcium goes to bones, not arteries'
        });
    }
    
    // Check for iron absorption complex (Iron + Vitamin C)
    const iron = nutrition.minerals?.iron_mg || 0;
    const vitaminC = nutrition.vitamins?.vitaminC_mg || 0;
    
    if (iron > 3 && vitaminC > 25) {
        synergies.push({
            name: 'Iron + Vitamin C',
            benefit: 'Vitamin C increases iron absorption by 3x (critical for plant-based iron)'
        });
    }
    
    // Check for omega-3 (from fish)
    const omega3 = nutrition.macronutrients?.omega3_g || 0;
    const hasFish = recipe.ingredients?.some(ing => 
        ing.foodId?.includes('salmon') || ing.foodId?.includes('sardine') || ing.foodId?.includes('mackerel')
    );
    
    if (omega3 > 1 && hasFish) {
        synergies.push({
            name: 'Omega-3 EPA/DHA',
            benefit: 'Direct EPA/DHA from fish (much better than plant ALA which converts at only 1-10%)'
        });
    }
    
    // Check for fat-soluble vitamin absorption (vitamins A,D,E,K + fat)
    const hasVitaminA = (nutrition.vitamins?.vitaminA_mcg || 0) > 150;
    const hasVitaminD_sol = vitaminD > 200;
    const hasVitaminE = (nutrition.vitamins?.vitaminE_mg || 0) > 3;
    const hasVitaminK = (nutrition.vitamins?.vitaminK_mcg || 0) > 50;
    const hasFat = (nutrition.macronutrients?.fat_g || 0) > 10;
    
    if ((hasVitaminA || hasVitaminD_sol || hasVitaminE || hasVitaminK) && hasFat) {
        synergies.push({
            name: 'Fat-Soluble Vitamins',
            benefit: 'Healthy fats present to absorb fat-soluble vitamins A, D, E, K'
        });
    }
    
    return synergies;
}
// ========== BIOMARKER TRACKING FUNCTIONS ==========

// Load saved biomarkers from localStorage
function loadSavedBiomarkers() {
    // Data already loaded from Firestore in loadUserData()
    // Just populate form fields
    if (userBiomarkers && Object.keys(userBiomarkers).length > 0) {
        for (let key in userBiomarkers) {
            const input = document.getElementById(key);
            if (input && userBiomarkers[key] !== null) {
                input.value = userBiomarkers[key];
            }
        }
    }
}

// Analyze biomarkers and generate recommendations
function analyzeBiomarkers() {
    if (!functionHealthData) {
        alert('Biomarker data not loaded. Please check data files.');
        return;
    }
    
    // Collect biomarker values from form
    userBiomarkers = {
        vitaminD: parseFloat(document.getElementById('vitaminD').value) || null,
        vitaminB12: parseFloat(document.getElementById('vitaminB12').value) || null,
        ferritin: parseFloat(document.getElementById('ferritin').value) || null,
        magnesium: parseFloat(document.getElementById('magnesium').value) || null,
        omega3Index: parseFloat(document.getElementById('omega3Index').value) || null,
        folate: parseFloat(document.getElementById('folate').value) || null,
        fastingGlucose: parseFloat(document.getElementById('fastingGlucose').value) || null,
        hba1c: parseFloat(document.getElementById('hba1c').value) || null,
        fastingInsulin: parseFloat(document.getElementById('fastingInsulin').value) || null,
        apoB: parseFloat(document.getElementById('apoB').value) || null,
        hsCRP: parseFloat(document.getElementById('hsCRP').value) || null,
        homocysteine: parseFloat(document.getElementById('homocysteine').value) || null
    };
    
    // Check if any values entered
    const hasValues = Object.values(userBiomarkers).some(v => v !== null);
    if (!hasValues) {
        alert('Please enter at least one biomarker value to analyze.');
        return;
    }
    
    // Analyze each biomarker
    const analysis = analyzeBiomarkerValues(userBiomarkers);
    
    // Display results
    displayBiomarkerResults(analysis);
    
    // Show results section
    document.getElementById('biomarker-results').style.display = 'block';
    
    // Scroll to results
    document.getElementById('biomarker-results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Analyze biomarker values against optimal ranges
function analyzeBiomarkerValues(biomarkers) {
    const results = {
        optimal: [],
        suboptimal: [],
        deficient: [],
        recommendations: []
    };
    
    const biomarkerCategories = functionHealthData.biomarker_categories;
    
    // Analyze nutrient status
    if (biomarkerCategories.nutrient_status) {
        biomarkerCategories.nutrient_status.markers.forEach(marker => {
            const markerKey = getMarkerKey(marker.marker);
            const value = biomarkers[markerKey];
            
            if (value !== null && value !== undefined) {
                const status = evaluateBiomarker(marker, value);
                const result = {
                    name: marker.marker,
                    value: value,
                    unit: marker.unit,
                    status: status.level,
                    range: status.range,
                    recommendation: status.recommendation,
                    adjustments: marker.meal_plan_adjustments || {}
                };
                
                if (status.level === 'optimal') {
                    results.optimal.push(result);
                } else if (status.level === 'suboptimal') {
                    results.suboptimal.push(result);
                } else {
                    results.deficient.push(result);
                }
            }
        });
    }
    
    // Analyze metabolic health
    if (biomarkerCategories.metabolic_health) {
        biomarkerCategories.metabolic_health.markers.forEach(marker => {
            const markerKey = getMarkerKey(marker.marker);
            const value = biomarkers[markerKey];
            
            if (value !== null && value !== undefined) {
                const status = evaluateBiomarker(marker, value);
                const result = {
                    name: marker.marker,
                    value: value,
                    unit: marker.unit,
                    status: status.level,
                    range: status.range,
                    recommendation: status.recommendation,
                    adjustments: marker.meal_plan_adjustments || {}
                };
                
                if (status.level === 'optimal') {
                    results.optimal.push(result);
                } else if (status.level === 'suboptimal') {
                    results.suboptimal.push(result);
                } else {
                    results.deficient.push(result);
                }
            }
        });
    }
    
    // Analyze cardiovascular health
    if (biomarkerCategories.cardiovascular_health) {
        biomarkerCategories.cardiovascular_health.markers.forEach(marker => {
            const markerKey = getMarkerKey(marker.marker);
            const value = biomarkers[markerKey];
            
            if (value !== null && value !== undefined) {
                const status = evaluateBiomarker(marker, value);
                const result = {
                    name: marker.marker,
                    value: value,
                    unit: marker.unit,
                    status: status.level,
                    range: status.range,
                    recommendation: status.recommendation,
                    adjustments: marker.meal_plan_adjustments || {}
                };
                
                if (status.level === 'optimal') {
                    results.optimal.push(result);
                } else if (status.level === 'suboptimal') {
                    results.suboptimal.push(result);
                } else {
                    results.deficient.push(result);
                }
            }
        });
    }
    
    // Generate meal plan recommendations
    results.recommendations = generateMealPlanRecommendations(results);
    
    return results;
}

// Get camelCase key from marker name
function getMarkerKey(markerName) {
    const keyMap = {
        'Vitamin D (25-OH)': 'vitaminD',
        'Vitamin B12': 'vitaminB12',
        'Ferritin (Iron Storage)': 'ferritin',
        'Magnesium (RBC)': 'magnesium',
        'Omega-3 Index': 'omega3Index',
        'Folate (B9)': 'folate',
        'Fasting Glucose': 'fastingGlucose',
        'HbA1c (Hemoglobin A1c)': 'hba1c',
        'Fasting Insulin': 'fastingInsulin',
        'ApoB (Apolipoprotein B)': 'apoB',
        'hs-CRP (High-Sensitivity C-Reactive Protein)': 'hsCRP',
        'Homocysteine': 'homocysteine'
    };
    return keyMap[markerName] || markerName;
}

// Evaluate a single biomarker value
function evaluateBiomarker(marker, value) {
    const ranges = marker.functional_range;
    let level, range, recommendation;
    
    // Parse ranges (handle different formats)
    if (typeof ranges.optimal === 'string') {
        // Handle range strings like "40-60", ">8", "<5.3"
        if (ranges.optimal.startsWith('>')) {
            const threshold = parseFloat(ranges.optimal.substring(1));
            if (value >= threshold) {
                level = 'optimal';
                range = ranges.optimal;
                recommendation = `Your ${marker.marker} is optimal. Maintain current nutrition habits.`;
            } else if (ranges.acceptable && value >= parseFloat(ranges.acceptable.split('-')[0])) {
                level = 'suboptimal';
                range = ranges.acceptable || ranges.sufficient;
                recommendation = `Your ${marker.marker} is acceptable but below optimal. Consider dietary improvements.`;
            } else {
                level = 'deficient';
                range = ranges.deficient || `<${threshold}`;
                recommendation = `Your ${marker.marker} is below optimal levels. Dietary intervention recommended.`;
            }
        } else if (ranges.optimal.startsWith('<')) {
            const threshold = parseFloat(ranges.optimal.substring(1));
            if (value < threshold) {
                level = 'optimal';
                range = ranges.optimal;
                recommendation = `Your ${marker.marker} is optimal. Great work!`;
            } else if (ranges.acceptable && value <= parseFloat(ranges.acceptable)) {
                level = 'suboptimal';
                range = ranges.acceptable;
                recommendation = `Your ${marker.marker} is acceptable but above optimal. Consider dietary modifications.`;
            } else {
                level = 'deficient';
                range = `>${threshold}`;
                recommendation = `Your ${marker.marker} is elevated. Dietary changes recommended.`;
            }
        } else if (ranges.optimal.includes('-')) {
            // Range like "40-60"
            const [min, max] = ranges.optimal.split('-').map(parseFloat);
            if (value >= min && value <= max) {
                level = 'optimal';
                range = ranges.optimal;
                recommendation = `Your ${marker.marker} is in the optimal range. Excellent!`;
            } else if (value < min) {
                if (ranges.sufficient) {
                    const suffMin = parseFloat(ranges.sufficient.split('-')[0]);
                    if (value >= suffMin) {
                        level = 'suboptimal';
                        range = ranges.sufficient;
                        recommendation = `Your ${marker.marker} is below optimal but sufficient. Room for improvement.`;
                    } else {
                        level = 'deficient';
                        range = ranges.deficient || `<${suffMin}`;
                        recommendation = `Your ${marker.marker} is deficient. Dietary intervention needed.`;
                    }
                } else {
                    level = 'suboptimal';
                    range = `<${min}`;
                    recommendation = `Your ${marker.marker} is below optimal range.`;
                }
            } else {
                level = 'suboptimal';
                range = `>${max}`;
                recommendation = `Your ${marker.marker} is above optimal range.`;
            }
        }
    }
    
    return { level, range, recommendation };
}

// Generate meal plan recommendations based on biomarker analysis
function generateMealPlanRecommendations(results) {
    const recommendations = [];
    
    // Process deficient and suboptimal markers
    [...results.deficient, ...results.suboptimal].forEach(marker => {
        if (marker.adjustments) {
            let adjustmentList = [];
            
            // Extract adjustments based on marker
            if (marker.name.includes('Vitamin D')) {
                adjustmentList = marker.adjustments.if_below_40 || [];
            } else if (marker.name.includes('B12')) {
                adjustmentList = marker.adjustments.if_below_500 || [];
            } else if (marker.name.includes('Ferritin')) {
                adjustmentList = marker.adjustments.if_low || [];
            } else if (marker.name.includes('Magnesium')) {
                adjustmentList = marker.adjustments.if_below_6 || [];
            } else if (marker.name.includes('Omega-3')) {
                adjustmentList = marker.adjustments.if_below_8 || [];
            } else if (marker.name.includes('Folate')) {
                adjustmentList = marker.adjustments.if_below_10 || [];
            } else if (marker.name.includes('Glucose') || marker.name.includes('HbA1c')) {
                adjustmentList = marker.adjustments.if_above_85 || marker.adjustments.if_above_5_3 || [];
            } else if (marker.name.includes('Insulin')) {
                adjustmentList = marker.adjustments.if_above_5 || [];
            } else if (marker.name.includes('ApoB')) {
                adjustmentList = marker.adjustments.if_above_80 || [];
            } else if (marker.name.includes('CRP')) {
                adjustmentList = marker.adjustments.if_above_0_5 || [];
            } else if (marker.name.includes('Homocysteine')) {
                adjustmentList = marker.adjustments.if_above_7 || [];
            }
            
            if (adjustmentList.length > 0) {
                recommendations.push({
                    marker: marker.name,
                    status: marker.status,
                    adjustments: adjustmentList
                });
            }
        }
    });
    
    return recommendations;
}

// Display biomarker results
function displayBiomarkerResults(analysis) {
    // Display summary cards
    const summaryDiv = document.getElementById('biomarker-summary');
    summaryDiv.innerHTML = `
        <div class="status-card optimal">
            <div class="status-label">Optimal Range</div>
            <div class="status-number">${analysis.optimal.length}</div>
        </div>
        <div class="status-card suboptimal">
            <div class="status-label">Suboptimal</div>
            <div class="status-number">${analysis.suboptimal.length}</div>
        </div>
        <div class="status-card deficient">
            <div class="status-label">Needs Attention</div>
            <div class="status-number">${analysis.deficient.length}</div>
        </div>
    `;
    
    // Display detailed results
    const detailsDiv = document.getElementById('biomarker-details');
    detailsDiv.innerHTML = '';
    
    const allMarkers = [...analysis.deficient, ...analysis.suboptimal, ...analysis.optimal];
    
    allMarkers.forEach(marker => {
        const item = document.createElement('div');
        item.className = `biomarker-item ${marker.status}`;
        item.innerHTML = `
            <div class="biomarker-item-header">
                <div>
                    <span class="biomarker-name">${marker.name}</span>
                    <span class="biomarker-status ${marker.status}">${marker.status.toUpperCase()}</span>
                </div>
                <div class="biomarker-value">${marker.value} ${marker.unit}</div>
            </div>
            <div class="biomarker-range">Target Range: ${marker.range}</div>
            <div class="biomarker-recommendation">${marker.recommendation}</div>
        `;
        detailsDiv.appendChild(item);
    });
    
    // Display meal plan adjustments
    const adjustmentsDiv = document.getElementById('adjustment-list');
    adjustmentsDiv.innerHTML = '';
    
    if (analysis.recommendations.length === 0) {
        adjustmentsDiv.innerHTML = '<p style="color: var(--text-light); text-align: center; padding: 20px;">All biomarkers are optimal! No meal plan adjustments needed. Keep up the great work! 🎉</p>';
    } else {
        analysis.recommendations.forEach(rec => {
            const adjItem = document.createElement('div');
            adjItem.className = 'adjustment-item';
            adjItem.innerHTML = `
                <h5>${rec.marker} - ${rec.status === 'deficient' ? 'Priority' : 'Improvement'}</h5>
                <ul>
                    ${rec.adjustments.map(adj => `<li>${adj}</li>`).join('')}
                </ul>
            `;
            adjustmentsDiv.appendChild(adjItem);
        });
    }
}

// Clear biomarker form
function clearBiomarkers() {
    if (!confirm('Clear all biomarker data?')) return;
    
    const inputs = document.querySelectorAll('#biomarkers-tab input[type="number"]');
    inputs.forEach(input => input.value = '');
    
    userBiomarkers = {};
    document.getElementById('biomarker-results').style.display = 'none';
}

// Save biomarkers to localStorage
async function saveBiomarkers() {
    // Save to Firestore
    await saveUserData('biomarkers', userBiomarkers);
    
    // Also offer download
    const dataStr = JSON.stringify({
        date: new Date().toISOString(),
        biomarkers: userBiomarkers
    }, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `biomarkers-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    alert('Biomarkers saved to cloud and downloaded!');
}

// ==========================================
// RECIPE MANAGEMENT FUNCTIONALITY
// ==========================================

let customRecipes = [];
let ingredientCounter = 0;

// Initialize recipe management features
function initializeRecipeManagement() {
    // Method tab switching
    document.querySelectorAll('.method-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const method = tab.dataset.method;
            switchInputMethod(method);
        });
    });
    
    // URL scanning
    document.getElementById('scan-url-btn').addEventListener('click', scanRecipeFromURL);
    
    // Manual form
    document.getElementById('add-ingredient-btn').addEventListener('click', addIngredientRow);
    document.getElementById('calculate-nutrition-btn').addEventListener('click', calculateNutritionFromIngredients);
    document.getElementById('manual-recipe-form').addEventListener('submit', saveManualRecipe);
    document.getElementById('reset-form-btn').addEventListener('click', resetManualForm);
    
    // File uploads
    document.getElementById('file-upload-btn').addEventListener('click', () => {
        document.getElementById('file-upload').click();
    });
    document.getElementById('file-upload').addEventListener('change', handleFileUpload);
    
    document.getElementById('image-upload-btn').addEventListener('click', () => {
        document.getElementById('image-upload').click();
    });
    document.getElementById('image-upload').addEventListener('change', handleImageUpload);
    
    // Initialize with one ingredient row
    addIngredientRow();
    
    // Load custom recipes
    loadCustomRecipes();
}

// Switch between input methods
function switchInputMethod(method) {
    document.querySelectorAll('.method-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.method === method);
    });
    document.querySelectorAll('.input-method').forEach(section => {
        section.classList.toggle('active', section.id === `${method}-method`);
    });
}

// Scan recipe from URL
async function scanRecipeFromURL() {
    const url = document.getElementById('recipe-url').value.trim();
    const statusEl = document.getElementById('url-status');
    
    if (!url) {
        showStatus(statusEl, 'Please enter a URL', 'error');
        return;
    }
    
    // Validate URL
    try {
        new URL(url);
    } catch (e) {
        showStatus(statusEl, '❌ Invalid URL format', 'error');
        return;
    }
    
    showStatus(statusEl, '🔍 Scanning recipe...', 'info');
    
    // Try multiple CORS proxies as fallback
    const proxies = [
        { url: 'https://api.allorigins.win/raw?url=', name: 'AllOrigins' },
        { url: 'https://corsproxy.io/?', name: 'CORSProxy' },
        { url: 'https://api.codetabs.com/v1/proxy?quest=', name: 'CodeTabs' }
    ];
    
    let lastError = null;
    
    for (const proxy of proxies) {
        try {
            console.log(`Trying ${proxy.name} proxy...`);
            showStatus(statusEl, `🔍 Trying ${proxy.name} proxy...`, 'info');
            
            const proxyUrl = proxy.url + encodeURIComponent(url);
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
            
            const response = await fetch(proxyUrl, { 
                signal: controller.signal,
                headers: {
                    'Accept': 'text/html,application/xhtml+xml,application/xml'
                }
            });
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const html = await response.text();
            console.log('HTML fetched, length:', html.length);
            
            // Parse recipe from HTML
            const recipe = parseRecipeFromHTML(html, url);
            
            if (recipe && recipe.name) {
                displayScannedRecipe(recipe);
                showStatus(statusEl, `✅ Recipe scanned successfully via ${proxy.name}!`, 'success');
                return; // Success!
            } else {
                throw new Error('No recipe data found in page');
            }
        } catch (error) {
            console.error(`${proxy.name} proxy failed:`, error);
            lastError = error;
            // Continue to next proxy
        }
    }
    
    // All proxies failed
    const errorMsg = lastError?.name === 'AbortError' 
        ? '⏱️ Request timed out. Site may be slow or blocking scrapers.'
        : '❌ Could not fetch recipe. Site may block automated access.';
    
    showStatus(statusEl, errorMsg, 'error');
    
    // Show helpful message
    const previewEl = document.getElementById('scanned-recipe-preview');
    previewEl.style.display = 'block';
    previewEl.innerHTML = `
        <h4>⚠️ Unable to Scan Recipe</h4>
        <p><strong>Possible reasons:</strong></p>
        <ul style="margin: 12px 0; padding-left: 20px; line-height: 1.8;">
            <li>Website blocks automated scraping</li>
            <li>Recipe not formatted with standard schema</li>
            <li>CORS proxy limitations</li>
            <li>Network or timeout issues</li>
        </ul>
        <p><strong>Alternative options:</strong></p>
        <div class="form-actions" style="margin-top: 16px;">
            <button onclick="switchInputMethod('manual')" class="btn-primary">
                ✍️ Enter Recipe Manually
            </button>
            <button onclick="copyPasteHelper()" class="btn-secondary">
                📋 Copy/Paste Helper
            </button>
        </div>
    `;
    
    console.log('All proxies failed. Last error:', lastError);
}

// Parse recipe from HTML using Schema.org or common patterns
function parseRecipeFromHTML(html, url) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // Try to find Recipe schema (JSON-LD)
    const scripts = doc.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
        try {
            const data = JSON.parse(script.textContent);
            if (data['@type'] === 'Recipe' || (Array.isArray(data['@graph']) && data['@graph'].find(item => item['@type'] === 'Recipe'))) {
                const recipeData = Array.isArray(data['@graph']) ? data['@graph'].find(item => item['@type'] === 'Recipe') : data;
                return extractFromSchema(recipeData);
            }
        } catch (e) {
            continue;
        }
    }
    
    // Try microdata
    const recipeEl = doc.querySelector('[itemtype*="schema.org/Recipe"]');
    if (recipeEl) {
        return extractFromMicrodata(recipeEl);
    }
    
    // Fallback: common patterns
    return extractFromCommonPatterns(doc);
}

// Extract recipe from Schema.org JSON-LD
function extractFromSchema(data) {
    const getText = (value) => {
        if (!value) return '';
        if (typeof value === 'string') return value;
        if (value['@value']) return value['@value'];
        if (value.name) return value.name;
        if (Array.isArray(value)) return value[0] ? getText(value[0]) : '';
        return String(value);
    };
    
    return {
        name: getText(data.name),
        description: getText(data.description),
        prepTime: getText(data.prepTime),
        cookTime: getText(data.cookTime),
        servings: parseInt(getText(data.recipeYield)) || parseInt(getText(data.yield)) || 4,
        ingredients: Array.isArray(data.recipeIngredient) ? data.recipeIngredient.map(i => getText(i)) : [],
        instructions: Array.isArray(data.recipeInstructions) ? 
            data.recipeInstructions.map(i => getText(i.text || i)).filter(t => t).join('\n') : '',
        nutrition: data.nutrition || null,
        image: data.image?.url || (Array.isArray(data.image) ? data.image[0] : data.image) || ''
    };
}

// Extract from microdata
function extractFromMicrodata(el) {
    const get = (prop) => el.querySelector(`[itemprop="${prop}"]`)?.textContent?.trim();
    const getAll = (prop) => Array.from(el.querySelectorAll(`[itemprop="${prop}"]`)).map(e => e.textContent.trim());
    
    return {
        name: get('name') || '',
        description: get('description') || '',
        prepTime: get('prepTime') || '',
        cookTime: get('cookTime') || '',
        servings: get('recipeYield') || 4,
        ingredients: getAll('recipeIngredient'),
        instructions: getAll('recipeInstructions').join('\n'),
        nutrition: null,
        image: el.querySelector('[itemprop="image"]')?.src || ''
    };
}

// Extract from common HTML patterns
function extractFromCommonPatterns(doc) {
    const getBySelectors = (selectors) => {
        for (const sel of selectors) {
            const el = doc.querySelector(sel);
            if (el) return el.textContent.trim();
        }
        return '';
    };
    
    const getAllBySelectors = (selectors) => {
        for (const sel of selectors) {
            const els = doc.querySelectorAll(sel);
            if (els.length > 0) return Array.from(els).map(e => e.textContent.trim());
        }
        return [];
    };
    
    return {
        name: getBySelectors(['.recipe-title', '.recipe-name', 'h1.title', 'h1']),
        description: getBySelectors(['.recipe-description', '.description', '.summary']),
        prepTime: getBySelectors(['.prep-time', '.preptime', '[class*="prep"]']),
        cookTime: getBySelectors(['.cook-time', '.cooktime', '[class*="cook"]']),
        servings: getBySelectors(['.servings', '.yield', '[class*="serving"]']) || 4,
        ingredients: getAllBySelectors(['.ingredient', '.ingredients li', '[class*="ingredient"] li']),
        instructions: getAllBySelectors(['.instruction', '.instructions li', '.step', '[class*="instruction"] li']).join('\n'),
        nutrition: null,
        image: doc.querySelector('.recipe-image img, .featured-image img, [class*="recipe"] img')?.src || ''
    };
}

// Display scanned recipe for review
function displayScannedRecipe(recipe) {
    const previewEl = document.getElementById('scanned-recipe-preview');
    previewEl.style.display = 'block';
    previewEl.innerHTML = `
        <h4>📋 Scanned Recipe</h4>
        ${recipe.image ? `<img src="${recipe.image}" alt="${recipe.name}" style="max-width: 100%; max-height: 300px; border-radius: 8px; margin: 12px 0;">` : ''}
        <p><strong>Name:</strong> ${recipe.name}</p>
        <p><strong>Description:</strong> ${recipe.description}</p>
        <p><strong>Servings:</strong> ${recipe.servings}</p>
        <p><strong>Prep:</strong> ${recipe.prepTime} | <strong>Cook:</strong> ${recipe.cookTime}</p>
        <div style="margin: 16px 0;">
            <strong>Ingredients (${recipe.ingredients.length}):</strong>
            <ul style="margin: 8px 0; padding-left: 20px;">
                ${recipe.ingredients.slice(0, 5).map(ing => `<li>${ing}</li>`).join('')}
                ${recipe.ingredients.length > 5 ? `<li><em>...and ${recipe.ingredients.length - 5} more</em></li>` : ''}
            </ul>
        </div>
        <div class="form-actions" style="margin-top: 16px;">
            <button onclick="populateFormFromScanned(${JSON.stringify(recipe).replace(/"/g, '&quot;')})" class="btn-primary">
                ✏️ Edit & Save
            </button>
            <button onclick="saveScannedRecipeDirectly(${JSON.stringify(recipe).replace(/"/g, '&quot;')})" class="btn-secondary">
                💾 Save As-Is
            </button>
        </div>
    `;
}

// Populate manual form from scanned recipe
function populateFormFromScanned(recipe) {
    switchInputMethod('manual');
    document.getElementById('recipe-name').value = recipe.name || '';
    document.getElementById('recipe-description').value = recipe.description || '';
    document.getElementById('recipe-servings').value = recipe.servings || 4;
    document.getElementById('recipe-prep-time').value = recipe.prepTime || '';
    document.getElementById('recipe-cook-time').value = recipe.cookTime || '';
    
    // Clear existing ingredients
    document.getElementById('ingredients-list').innerHTML = '';
    ingredientCounter = 0;
    
    // Add ingredients
    if (recipe.ingredients && recipe.ingredients.length > 0) {
        recipe.ingredients.forEach(ing => {
            addIngredientRow(ing);
        });
    } else {
        addIngredientRow();
    }
    
    // Scroll to form
    document.getElementById('manual-method').scrollIntoView({ behavior: 'smooth' });
}

// Save scanned recipe directly (with estimated nutrition)
async function saveScannedRecipeDirectly(recipe) {
    if (!recipe.name) {
        alert('Recipe must have a name');
        return;
    }
    
    // Generate recipe ID
    const mealId = 'custom_' + Date.now() + '_' + recipe.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
    
    // Estimate basic nutrition (user can edit later)
    const customRecipe = {
        mealId,
        name: recipe.name,
        description: recipe.description || 'Scanned from web',
        baseServings: recipe.servings || 4,
        scalable: true,
        prepTime: recipe.prepTime || 'Unknown',
        cookTime: recipe.cookTime || 'Unknown',
        mealType: 'dinner', // Default, user can change
        ingredients: recipe.ingredients || [],
        nutritionPerServing: {
            calories: 400, // Estimated
            macronutrients: { protein_g: 25, carbohydrates_g: 35, fat_g: 15, fiber_g: 5, omega3_g: 0.5 },
            vitamins: { vitaminA_mcg: 0, vitaminD_IU: 0, vitaminE_mg: 0, vitaminK_mcg: 0, vitaminC_mg: 0, vitaminB12_mcg: 0, vitaminB6_mg: 0, folate_B9_mcg: 0, thiamin_B1_mg: 0, riboflavin_B2_mg: 0, niacin_B3_mg: 0, choline_mg: 0 },
            minerals: { iron_mg: 0, magnesium_mg: 0, selenium_mcg: 0, zinc_mg: 0, potassium_mg: 0, calcium_mg: 0, phosphorus_mg: 0, copper_mg: 0, manganese_mg: 0 }
        },
        tags: ['custom', 'scanned'],
        sourceUrl: document.getElementById('recipe-url').value,
        custom: true
    };
    
    await saveRecipeToFirestore(customRecipe);
    alert(`✅ Recipe "${recipe.name}" saved! Note: Nutrition values are estimated. You can edit them later.`);
}

// Add ingredient row to manual form
function addIngredientRow(value = '') {
    const container = document.getElementById('ingredients-list');
    const row = document.createElement('div');
    row.className = 'ingredient-item';
    row.innerHTML = `
        <input type="text" placeholder="Ingredient name" value="${value}" class="ingredient-name" />
        <input type="text" placeholder="Amount (e.g., 2 cups)" class="ingredient-amount" />
        <button type="button" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(row);
    ingredientCounter++;
}

// Calculate nutrition from ingredients (using USDA API or estimation)
async function calculateNutritionFromIngredients() {
    const ingredients = [];
    document.querySelectorAll('.ingredient-item').forEach(item => {
        const name = item.querySelector('.ingredient-name').value.trim();
        const amount = item.querySelector('.ingredient-amount').value.trim();
        if (name) ingredients.push({ name, amount });
    });
    
    if (ingredients.length === 0) {
        alert('Please add ingredients first');
        return;
    }
    
    const statusEl = document.getElementById('url-status');
    showStatus(statusEl, '🧮 Calculating nutrition...', 'info');
    
    try {
        // Note: This would require USDA FoodData Central API or similar
        // For now, we'll show a message that this requires API setup
        alert('⚠️ Nutrition calculation requires USDA API integration.\n\nFor now, please:\n1. Use a nutrition calculator website\n2. Enter values manually in the form below\n\nAPI integration coming soon!');
        showStatus(statusEl, 'Manual nutrition entry required', 'info');
        
        // Scroll to nutrition section
        document.querySelector('.nutrition-inputs').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Nutrition calculation error:', error);
        showStatus(statusEl, 'Error calculating nutrition', 'error');
    }
}

// Save manual recipe
async function saveManualRecipe(e) {
    e.preventDefault();
    
    // Collect form data
    const ingredients = [];
    document.querySelectorAll('.ingredient-item').forEach(item => {
        const name = item.querySelector('.ingredient-name').value.trim();
        const amount = item.querySelector('.ingredient-amount').value.trim();
        if (name) ingredients.push({ name, amount });
    });
    
    const tags = document.getElementById('recipe-tags').value
        .split(',')
        .map(t => t.trim())
        .filter(t => t);
    tags.push('custom'); // Always add custom tag
    
    const recipe = {
        mealId: 'custom_' + Date.now() + '_' + document.getElementById('recipe-name').value.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        name: document.getElementById('recipe-name').value,
        description: document.getElementById('recipe-description').value || '',
        baseServings: parseInt(document.getElementById('recipe-servings').value),
        scalable: true,
        prepTime: document.getElementById('recipe-prep-time').value || 'Not specified',
        cookTime: document.getElementById('recipe-cook-time').value || 'Not specified',
        mealType: document.getElementById('recipe-meal-type').value,
        ingredients,
        nutritionPerServing: {
            calories: parseFloat(document.getElementById('nutrition-calories').value) || 0,
            macronutrients: {
                protein_g: parseFloat(document.getElementById('nutrition-protein').value) || 0,
                carbohydrates_g: parseFloat(document.getElementById('nutrition-carbs').value) || 0,
                fat_g: parseFloat(document.getElementById('nutrition-fat').value) || 0,
                fiber_g: parseFloat(document.getElementById('nutrition-fiber').value) || 0,
                omega3_g: parseFloat(document.getElementById('nutrition-omega3').value) || 0
            },
            vitamins: {
                vitaminA_mcg: parseFloat(document.getElementById('nutrition-vitaminA').value) || 0,
                vitaminD_IU: parseFloat(document.getElementById('nutrition-vitaminD').value) || 0,
                vitaminE_mg: parseFloat(document.getElementById('nutrition-vitaminE').value) || 0,
                vitaminK_mcg: parseFloat(document.getElementById('nutrition-vitaminK').value) || 0,
                vitaminC_mg: parseFloat(document.getElementById('nutrition-vitaminC').value) || 0,
                vitaminB12_mcg: parseFloat(document.getElementById('nutrition-vitaminB12').value) || 0,
                vitaminB6_mg: parseFloat(document.getElementById('nutrition-vitaminB6').value) || 0,
                folate_B9_mcg: parseFloat(document.getElementById('nutrition-folate').value) || 0,
                thiamin_B1_mg: parseFloat(document.getElementById('nutrition-thiamin').value) || 0,
                riboflavin_B2_mg: parseFloat(document.getElementById('nutrition-riboflavin').value) || 0,
                niacin_B3_mg: parseFloat(document.getElementById('nutrition-niacin').value) || 0,
                choline_mg: parseFloat(document.getElementById('nutrition-choline').value) || 0
            },
            minerals: {
                iron_mg: parseFloat(document.getElementById('nutrition-iron').value) || 0,
                magnesium_mg: parseFloat(document.getElementById('nutrition-magnesium').value) || 0,
                selenium_mcg: parseFloat(document.getElementById('nutrition-selenium').value) || 0,
                zinc_mg: parseFloat(document.getElementById('nutrition-zinc').value) || 0,
                potassium_mg: parseFloat(document.getElementById('nutrition-potassium').value) || 0,
                calcium_mg: parseFloat(document.getElementById('nutrition-calcium').value) || 0,
                phosphorus_mg: parseFloat(document.getElementById('nutrition-phosphorus').value) || 0,
                copper_mg: parseFloat(document.getElementById('nutrition-copper').value) || 0,
                manganese_mg: parseFloat(document.getElementById('nutrition-manganese').value) || 0
            }
        },
        tags,
        custom: true,
        createdAt: new Date().toISOString()
    };
    
    await saveRecipeToFirestore(recipe);
    alert(`✅ Recipe "${recipe.name}" saved successfully!`);
    resetManualForm();
    
    // Switch to recipe library to show the new recipe
    document.querySelector('[data-tab="recipes"]').click();
}

// Save recipe to Firestore
async function saveRecipeToFirestore(recipe) {
    if (!currentUser) {
        alert('You must be logged in to save recipes');
        return;
    }
    
    try {
        await db.collection('users').doc(currentUser.uid)
            .collection('customRecipes').doc(recipe.mealId).set(recipe);
        
        // Add to local array
        customRecipes.push(recipe);
        
        // Reload recipes to include custom ones
        await loadCustomRecipes();
        renderRecipes();
    } catch (error) {
        console.error('Error saving recipe:', error);
        alert('Error saving recipe: ' + error.message);
    }
}

// Load custom recipes from Firestore
async function loadCustomRecipes() {
    if (!currentUser) return;
    
    try {
        const snapshot = await db.collection('users').doc(currentUser.uid)
            .collection('customRecipes').get();
        
        customRecipes = [];
        snapshot.forEach(doc => {
            customRecipes.push(doc.data());
        });
        
        console.log('Loaded custom recipes:', customRecipes.length);
        
        // Merge with main recipes array for auto-generate
        recipes = [...recipes.filter(r => !r.custom), ...customRecipes];
        
        // Render custom recipes in the Add Recipe tab
        renderCustomRecipes();
    } catch (error) {
        console.error('Error loading custom recipes:', error);
    }
}

// Render custom recipes in Add Recipe tab
function renderCustomRecipes() {
    const grid = document.getElementById('custom-recipes-grid');
    if (!grid) return;
    
    if (customRecipes.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No custom recipes yet. Create your first recipe above!</p>';
        return;
    }
    
    grid.innerHTML = customRecipes.map(recipe => `
        <div class="recipe-card custom-recipe" draggable="true" data-recipe-id="${recipe.mealId}">
            <div class="recipe-image" style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);">
                <span style="font-size: 48px;">🍳</span>
            </div>
            <div class="recipe-info">
                <h3>${recipe.name}</h3>
                <p class="recipe-description">${recipe.description || ''}</p>
                <div class="recipe-meta">
                    <span>⏱️ ${recipe.prepTime}</span>
                    <span>🍽️ ${recipe.baseServings} servings</span>
                </div>
                <div class="recipe-nutrition">
                    <div class="nutrition-item">
                        <span class="nutrition-value">${recipe.nutritionPerServing.calories}</span>
                        <span class="nutrition-label">cal</span>
                    </div>
                    <div class="nutrition-item">
                        <span class="nutrition-value">${recipe.nutritionPerServing.macronutrients.protein_g}g</span>
                        <span class="nutrition-label">protein</span>
                    </div>
                </div>
                <div class="recipe-tags">
                    ${recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <button onclick="deleteCustomRecipe('${recipe.mealId}')" class="btn-secondary" style="margin-top: 12px; width: 100%;">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Delete custom recipe
async function deleteCustomRecipe(mealId) {
    if (!confirm('Delete this recipe?')) return;
    
    try {
        await db.collection('users').doc(currentUser.uid)
            .collection('customRecipes').doc(mealId).delete();
        
        customRecipes = customRecipes.filter(r => r.mealId !== mealId);
        recipes = recipes.filter(r => r.mealId !== mealId);
        
        renderCustomRecipes();
        renderRecipes();
        alert('Recipe deleted');
    } catch (error) {
        console.error('Error deleting recipe:', error);
        alert('Error deleting recipe');
    }
}

// Reset manual form
function resetManualForm() {
    document.getElementById('manual-recipe-form').reset();
    document.getElementById('ingredients-list').innerHTML = '';
    ingredientCounter = 0;
    addIngredientRow();
}

// Handle file upload (JSON/CSV)
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const statusEl = document.getElementById('file-upload-status');
    showStatus(statusEl, '📤 Uploading...', 'info');
    
    try {
        const text = await file.text();
        let recipes = [];
        
        if (file.name.endsWith('.json')) {
            const data = JSON.parse(text);
            recipes = Array.isArray(data) ? data : (data.recipes || [data]);
        } else if (file.name.endsWith('.csv')) {
            recipes = parseCSV(text);
        }
        
        if (recipes.length === 0) {
            showStatus(statusEl, '❌ No recipes found in file', 'error');
            return;
        }
        
        // Save all recipes
        for (const recipe of recipes) {
            // Ensure required fields
            if (!recipe.name || !recipe.mealType) continue;
            
            recipe.mealId = recipe.mealId || ('custom_' + Date.now() + '_' + recipe.name.toLowerCase().replace(/[^a-z0-9]/g, '_'));
            recipe.custom = true;
            
            await saveRecipeToFirestore(recipe);
        }
        
        showStatus(statusEl, `✅ Imported ${recipes.length} recipes!`, 'success');
        e.target.value = ''; // Reset input
    } catch (error) {
        console.error('File upload error:', error);
        showStatus(statusEl, '❌ Error importing file', 'error');
    }
}

// Parse CSV to recipes
function parseCSV(text) {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',').map(h => h.trim());
    const recipes = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const recipe = {};
        headers.forEach((header, idx) => {
            recipe[header] = values[idx] || '';
        });
        recipes.push(recipe);
    }
    
    return recipes;
}

// Handle image upload (OCR)
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const statusEl = document.getElementById('image-upload-status');
    showStatus(statusEl, '📸 Image uploaded. OCR requires API integration (Tesseract.js or Google Vision).', 'info');
    
    // OCR implementation would go here
    // For now, show placeholder message
    alert('Image OCR feature requires additional setup:\n\n1. Install Tesseract.js for client-side OCR\n2. Or integrate Google Cloud Vision API\n3. Or use AWS Textract\n\nThis feature is coming soon!');
    
    e.target.value = ''; // Reset input
}

// Show status message
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
}

// Copy/Paste helper for manual entry
function copyPasteHelper() {
    switchInputMethod('manual');
    alert('💡 Quick Tip:\n\n1. Open the recipe in another tab\n2. Copy the recipe text\n3. Paste ingredients one at a time\n4. Use online nutrition calculators:\n   • MyFitnessPal\n   • Cronometer\n   • USDA FoodData Central\n\nPaste nutrition values into the form below!');
    document.getElementById('recipe-name').focus();
}

// Make functions globally available
window.populateFormFromScanned = populateFormFromScanned;
window.saveScannedRecipeDirectly = saveScannedRecipeDirectly;
window.deleteCustomRecipe = deleteCustomRecipe;
window.copyPasteHelper = copyPasteHelper;

