import apiClient from "./apiClient";

export async function recommendByDescription(description, limit = 5) {
  const { data } = await apiClient.post("/recommendations/by-description", null, {
    params: { description, limit },
  });
  return data;
}

export async function recommendByAnime(externalId, { limit = 5, minScore = 75 } = {}) {
  const { data } = await apiClient.get(`/recommendations/by-anime/${externalId}`, {
    params: { limit, min_score: minScore },
  });
  return data;
}

export async function getPersonalized(limit = 5) {
  const { data } = await apiClient.get("/recommendations/personalized", {
    params: { limit },
  });
  return data;
}
