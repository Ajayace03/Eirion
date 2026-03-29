import axios from "axios";
import { AnalysisRequest, AnalysisResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const runAnalysis = async (request: AnalysisRequest): Promise<AnalysisResponse> => {
  const { data } = await axios.post<AnalysisResponse>(`${API_BASE_URL}/analysis/run`, request);
  return data;
};
