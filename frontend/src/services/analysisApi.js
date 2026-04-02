const API_BASE_URL = 'http://localhost:8082/api/v1';

export const startAnalysis = async (gitname) => {
    const response = await fetch(`${API_BASE_URL}/analysis/${gitname}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error(`Failed to start: ${response.status}`);
    return response.json();
};

export const checkAnalysisStatus = async (taskId) => {
    const response = await fetch(`${API_BASE_URL}/analysis/status/${taskId}`);
    if (!response.ok) throw new Error(`Failed to check status: ${response.status}`);
    return response.json();
};