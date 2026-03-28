import axios from "axios";
import { AnalysisRequest, AnalysisResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const runAnalysis = async (request: AnalysisRequest): Promise<AnalysisResponse> => {
  try {
    const { data } = await axios.post<AnalysisResponse>(`${API_BASE_URL}/analysis/run`, request);
    return data;
  } catch (error) {
    console.error("API call failed, attempting to load fallback mock data", error);
    try {
      // Dynamic import of fallback JSON if backend is unreachable
      const mockResult = await import("../../../backend/data/mock_response.json");
      console.warn("Using fallback mock data.");
      return mockResult.default as AnalysisResponse;
    } catch (fallbackError) {
      console.error("Failed to load fallback mock data", fallbackError);
      throw error;
    }
  }
};
