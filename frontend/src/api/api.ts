import axios from "axios";
import type {
  BreakdownData,
  DiagnosisResult,
  Provider,
} from "../types/vehicle";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const analyzeBreakdown = async (
  data: BreakdownData
): Promise<DiagnosisResult> => {
  const response = await api.post("/api/breakdown/analyze", data);

  return response.data;
};

export const getNearbyProviders = async (
  latitude: number,
  longitude: number,
  assistanceRequired: string
): Promise<Provider[]> => {
  const response = await api.get("/api/providers/nearby", {
    params: {
      latitude,
      longitude,
      assistanceRequired,
    },
  });

  return response.data.providers;
};

export default api;