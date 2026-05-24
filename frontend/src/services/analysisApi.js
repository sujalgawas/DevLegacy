const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.0.8:8082/api/v1';

const apiFetch = async (url, options = {}) => {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
                ...(options.headers || {}),
            },
        });
        return response;
    } catch (err) {
        if (err instanceof TypeError && err.message === 'Failed to fetch') {
            throw new Error(
                `Cannot reach the server at ${API_BASE_URL}. ` +
                `This is usually a CORS issue — make sure your backend allows ` +
                `POST requests from ${window.location.origin}.`
            );
        }
        throw err;
    }
};

export const startAnalysis = async (gitname) => {
    const response = await apiFetch(`${API_BASE_URL}/analysis/${gitname}`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error(`Failed to start analysis: ${response.status} ${response.statusText}`);
    return response.json();
};

export const checkUserExistingData = async (gitname) => {
    try {
        const response = await apiFetch(`${API_BASE_URL}/analysis/check/${gitname}`);
        if (!response.ok) return { status: 'not_found' };
        return response.json();
    } catch {
        return { status: 'not_found' };
    }
};

export const checkAnalysisStatus = async (taskId) => {
    const response = await apiFetch(`${API_BASE_URL}/analysis/status/${taskId}`);
    if (!response.ok) throw new Error(`Failed to check status: ${response.status} ${response.statusText}`);
    return response.json();
};