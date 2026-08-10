import apiClient from "./apiClient";

export async function getMyList() {
  const { data } = await apiClient.get("/list/");
  return data;
}

export async function addToList(payload) {
  const { data } = await apiClient.post("/list/", payload);
  return data;
}

export async function updateListEntry(animeId, payload) {
  const { data } = await apiClient.put(`/list/${animeId}`, payload);
  return data;
}

export async function removeFromList(animeId) {
  await apiClient.delete(`/list/${animeId}`);
}