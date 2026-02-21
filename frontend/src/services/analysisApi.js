export const fetchAnalysis = async (gitname) => {
    const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/username/analysis/${gitname}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Failed to fetch analysis: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching analysis:', error);
        throw error;
    }
};
