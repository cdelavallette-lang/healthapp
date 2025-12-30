
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
function saveBiomarkers() {
    localStorage.setItem('userBiomarkers', JSON.stringify(userBiomarkers));
    
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
    
    alert('Biomarkers saved and downloaded!');
}
