// analysisApi.js

const API_BASE_URL = 'http://localhost:8082/api/v1';

export const startAnalysis = async (gitname) => {
    try {
        console.log(`Sending POST request to start analysis for: ${gitname}`);
        const response = await fetch(`${API_BASE_URL}/analysis/${gitname}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("Start Analysis Error Response:", errorData);
            throw new Error(errorData.detail || `Failed to start analysis: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Start Analysis Success Response:", data);
        return data; 
    } catch (error) {
        console.error('Error in startAnalysis:', error);
        throw error;
    }
};

export const checkAnalysisStatus = async (taskId) => {
    try {
        console.log(`Checking status for Task ID: ${taskId}`);
        const response = await fetch(`${API_BASE_URL}/analysis/status/${taskId}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("Check Status Error Response:", errorData);
            throw new Error(errorData.detail || `Failed to check status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Check Status Response:", data);
        return data; 
    } catch (error) {
        console.error('Error in checkAnalysisStatus:', error);
        throw error;
    }
};