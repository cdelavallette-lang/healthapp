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
    document.getElementById('clear-plan').addEventListener('click', clearPlan);
    document.getElementById('analyze-week').addEventListener('click', analyzeWeek);
    document.getElementById('save-plan').addEventListener('click', savePlan);

    // Biomarker actions
    document.getElementById('analyze-biomarkers').addEventListener('click', analyzeBiomarkers);
    document.getElementById('clear-biomarkers').addEventListener('click', clearBiomarkers);
    document.getElementById('save-biomarkers').addEventListener('click', saveBiomarkers);

    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('recipe-modal');
        if (e.target === modal) closeModal();
    });
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
    
    for (let key in addition.macronutrients) {
        total.macronutrients[key] = (total.macronutrients[key] || 0) + (addition.macronutrients[key] || 0);
    }
}

function divideNutrition(nutrition, divisor) {
    const result = { ...nutrition };
    result.calories = Math.round(nutrition.calories / divisor);
    
    result.macronutrients = {};
    for (let key in nutrition.macronutrients) {
        result.macronutrients[key] = Math.round(nutrition.macronutrients[key] / divisor);
    }
    
    return result;
}

function displayNutritionAnalysis(dailyAverage, weeklyTotal) {
    // Update summary cards
    document.getElementById('daily-calories').textContent = `${dailyAverage.calories} kcal`;
    document.getElementById('daily-protein').textContent = `${dailyAverage.macronutrients.protein_g}g protein`;
    document.getElementById('daily-fiber').textContent = `${dailyAverage.macronutrients.fiber_g}g fiber`;

    // For now, show a simple compliance score (you can enhance this with actual requirements checking)
    const proteinTarget = 120; // from optimal requirements
    const fiberTarget = 40;
    const proteinCompliance = Math.min((dailyAverage.macronutrients.protein_g / proteinTarget) * 100, 100);
    const fiberCompliance = Math.min((dailyAverage.macronutrients.fiber_g / fiberTarget) * 100, 100);
    const avgCompliance = Math.round((proteinCompliance + fiberCompliance) / 2);
    
    document.getElementById('compliance-score').textContent = `${avgCompliance}%`;

    // Show nutrient breakdown (simplified)
    const compliantList = document.querySelector('#compliant-nutrients .nutrient-list');
    const deficientList = document.querySelector('#deficient-nutrients .nutrient-list');

    compliantList.innerHTML = '';
    deficientList.innerHTML = '';

    if (dailyAverage.macronutrients.protein_g >= proteinTarget * 0.9) {
        compliantList.innerHTML += `
            <div class="nutrient-item">
                <div class="nutrient-name">Protein</div>
                <div class="nutrient-value">${dailyAverage.macronutrients.protein_g}g / ${proteinTarget}g</div>
            </div>
        `;
    } else {
        deficientList.innerHTML += `
            <div class="nutrient-item">
                <div class="nutrient-name">Protein</div>
                <div class="nutrient-value">${dailyAverage.macronutrients.protein_g}g / ${proteinTarget}g (${Math.round(proteinCompliance)}%)</div>
            </div>
        `;
    }

    if (dailyAverage.macronutrients.fiber_g >= fiberTarget * 0.9) {
        compliantList.innerHTML += `
            <div class="nutrient-item">
                <div class="nutrient-name">Fiber</div>
                <div class="nutrient-value">${dailyAverage.macronutrients.fiber_g}g / ${fiberTarget}g</div>
            </div>
        `;
    } else {
        deficientList.innerHTML += `
            <div class="nutrient-item">
                <div class="nutrient-name">Fiber</div>
                <div class="nutrient-value">${dailyAverage.macronutrients.fiber_g}g / ${fiberTarget}g (${Math.round(fiberCompliance)}%)</div>
            </div>
        `;
    }
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
